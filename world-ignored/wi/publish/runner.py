"""Publishing runner: gates, idempotency ledger, safe retries, manual-publish fallback.

For every (item, platform) the ledger in item["publish"][platform] records:
  status: pending | uploading | published | processing | manual | failed | needs_check
  key:    "<item id>:<platform>:<content hash>"  (one post per approved version per platform)

Rules:
  * Nothing is posted unless: not paused/stopped, publishing_live is on, footage verified, rights clear
    for that platform, and the approval matches the current content hash and includes the platform.
  * A job found in "uploading" (interrupted run) is never re-posted blindly: the adapter checks the
    account for the post first; if it can't tell, the platform is set to needs_check and Slack is alerted.
  * Retries happen only for errors raised before the create-post call (PublishError.before_commit).
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import config, models, slack
from ..models import now_iso
from ..store import Store
from .base import Publisher, PublishError
from .meta import FacebookFeed, FacebookReels, InstagramFeed, InstagramReels, Threads
from .others import LinkedIn, TikTok, X, YouTubeShorts

ADAPTERS = {c.name: c for c in (TikTok, YouTubeShorts, InstagramReels, FacebookReels, Threads, InstagramFeed,
                                FacebookFeed, X, LinkedIn)}
CAPTION_KEY = {"youtube_shorts": "youtube_description"}


def adapter(platform: str):
    return ADAPTERS[platform]()


def connection_status() -> dict:
    out = {}
    for p, cfg in config.settings()["platforms"].items():
        ok, why = adapter(p).available()
        out[p] = {"enabled": cfg["enabled"], "connected": ok, "detail": why, "preset": cfg["preset"],
                  "manual_only": cfg.get("manual_only", False)}
    return out


def _file_for(item: dict, preset: str, drive) -> str | None:
    o = item["edit"]["outputs"].get(preset, {})
    if o.get("path") and Path(o["path"]).exists():
        return o["path"]
    if o.get("drive_id") and drive is not None:
        dest = config.WORK_DIR / "publish" / item["id"] / Path(o.get("path") or f"{preset}.mp4").name
        return str(drive.download(o["drive_id"], dest))
    return None


def publish_item(item: dict, store: Store, *, dry_run: bool = False, drive=None) -> dict:
    s = config.settings()
    ctl = store.control()
    if ctl.get("emergency_stop") or ctl.get("paused"):
        return {"_blocked": f"publishing {'stopped' if ctl.get('emergency_stop') else 'paused'}: {ctl.get('reason', '')}"}
    live = s["control"]["publishing_live"] and not dry_run
    models.invalidate_approval_if_changed(item)
    ok, why = models.approval_valid(item)
    if not ok:
        return {"_blocked": why}
    rok, rwhy = models.rights_clear(item)
    if not rok or not item["verification"]["footage_verified"]:
        return {"_blocked": rwhy if not rok else "footage not verified"}
    version = models.content_hash(item)
    results = {}
    for platform in item["approval"]["platforms"]:
        cfg = s["platforms"].get(platform, {})
        led = item["publish"].setdefault(platform, {"status": "pending", "attempts": 0})
        key = f"{item['id']}:{platform}:{version}"
        if led.get("key") == key and led.get("status") in ("published", "processing", "manual"):
            results[platform] = {**led, "note": "already done"}
            continue
        if platform not in item["rights"]["permitted_platforms"] and "all" not in item["rights"]["permitted_platforms"]:
            led.update(status="manual", reason="rights do not cover this platform")
            results[platform] = dict(led)
            continue
        ad = adapter(platform)
        available, reason = ad.available()
        if cfg.get("manual_only") or not available:
            led.update(status="manual", reason=reason, key=key)
            results[platform] = dict(led)
            continue
        caption = item["captions"].get(CAPTION_KEY.get(platform, platform), "")
        if not live:
            results[platform] = {"status": "dry_run", "would_post": caption[:80], "preset": cfg["preset"]}
            continue
        if led.get("status") == "uploading" and led.get("key") == key:
            found = ad.find_existing(caption, led.get("started_at", now_iso()))
            if found:
                led.update(status="published", post_id=found.post_id, url=found.url, verified_at=now_iso())
                results[platform] = dict(led)
                continue
            if type(ad).find_existing is Publisher.find_existing:   # adapter can't search the account
                led.update(status="needs_check", last_error="interrupted mid-publish; cannot confirm absence")
                results[platform] = dict(led)
                continue
        path = _file_for(item, cfg["preset"], drive)
        if not path:
            led.update(status="failed", last_error=f"{cfg['preset']} file not available")
            results[platform] = dict(led)
            continue
        public_url = None
        for attempt in range(3):
            led.update(status="uploading", key=key, started_at=now_iso(), attempts=led.get("attempts", 0) + 1)
            store.save(item)   # persist before the network call so an interruption is detectable
            try:
                if ad.needs_public_url() and public_url is None:
                    if drive is None:
                        raise PublishError("public URL needed but Drive storage is not configured", before_commit=True)
                    public_url = drive.share_link(item["edit"]["outputs"][cfg["preset"]]["drive_id"])
                res = ad.publish(path, caption, item, public_url=public_url)
                led.update(status=res.status, post_id=res.post_id, url=res.url, published_at=now_iso(), last_error="")
                break
            except PublishError as exc:
                led["last_error"] = str(exc)[:400]
                if exc.before_commit and attempt < 2:
                    time.sleep(exc.retry_after or 15 * (attempt + 1))
                    continue
                led["status"] = "failed" if exc.before_commit else "needs_check"
                break
            except Exception as exc:  # noqa: BLE001 - unknown failure after upload start: don't retry blindly
                led.update(status="needs_check", last_error=f"{exc.__class__.__name__}: {str(exc)[:300]}")
                break
        if public_url and drive is not None:
            drive.unshare(item["edit"]["outputs"][cfg["preset"]]["drive_id"])
        store.save(item)
        results[platform] = dict(led)
    return results


def finalize(item: dict, results: dict, store: Store) -> None:
    statuses = {r.get("status") for k, r in results.items() if not k.startswith("_")}
    if "_blocked" in results or not statuses or statuses <= {"dry_run"}:
        return
    if statuses & {"failed", "needs_check"}:
        item["errors"].append({"at": now_iso(), "stage": "publish", "msg": "; ".join(
            f"{p}: {r.get('last_error', '')[:100]}" for p, r in results.items() if r.get("status") in ("failed", "needs_check"))})
        if not statuses & {"published", "processing"}:
            models.transition(item, models.FAILED, actor="publisher")
    if statuses & {"published", "processing"}:
        if item["status"] == models.APPROVED:
            models.transition(item, models.SCHEDULED, actor="publisher")
        if item["status"] == models.SCHEDULED:
            models.transition(item, models.PUBLISHED, actor="publisher")
    store.save(item)


def due_items(store: Store, slot_id: str, date_iso: str) -> list[dict]:
    return [i for i in store.by_status(models.APPROVED, models.SCHEDULED)
            if i["schedule"].get("slot") == slot_id and i["schedule"].get("date") == date_iso]


def run_slot(slot_id: str, *, dry_run: bool = False) -> dict:
    store = Store()
    today = datetime.now(config.tz()).date().isoformat()
    try:
        from ..storage import Drive
        d = Drive()
        drive = d if d.available()[0] else None
    except ImportError:
        drive = None
    out = {}
    items = due_items(store, slot_id, today)
    if not items:
        waiting = [i["id"] for i in store.by_status(models.READY_FOR_APPROVAL)
                   if i["schedule"].get("slot") == slot_id and i["schedule"].get("date") == today]
        out["_empty"] = ("nothing approved for this slot" + (f"; awaiting approval: {', '.join(waiting)}" if waiting else ""))
        return out
    for item in items[:1]:   # one video per slot
        res = publish_item(item, store, dry_run=dry_run, drive=drive)
        finalize(item, res, store)
        out[item["id"]] = res
        if "_blocked" in res:
            slack.send(f"⛔ *Not published ({slot_id}):* {res['_blocked']}", kind="blocked", item_id=item["id"],
                       thread_ts=slack.review_ts(item["id"]), dedupe_key=f"blocked:{item['id']}:{slot_id}:{today}")
        if "_blocked" not in res and any(r.get("status") not in ("dry_run",) for r in res.values()):
            slack.send(slack.confirmation(item, res), kind="publish_confirmation", item_id=item["id"],
                       dedupe_key=f"confirm:{item['id']}:{models.content_hash(item)}:{sorted(res)}")
        bad = {p: r for p, r in res.items() if isinstance(r, dict) and r.get("status") in ("failed", "needs_check")}
        if bad:
            slack.send(slack.alert(f"Publishing problem · {item['id']}",
                                   "\n".join(f"{p}: {r.get('status')} {r.get('last_error', '')}" for p, r in bad.items()),
                                   "Check the platform(s) above. needs_check = confirm whether the post exists before retrying."),
                       kind="alert", item_id=item["id"], dedupe_key=f"alert:{item['id']}:{sorted(bad)}:{today}")
    return out
