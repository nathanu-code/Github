"""World Ignored command line. Run from the world-ignored/ folder:  python -m wi <command> ...

Scheduled Claude sessions drive the pipeline through these commands (see ops/*.md).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from . import captions, config, models, slack
from .store import Store


def _today() -> str:
    return datetime.now(config.tz()).date().isoformat()


def _drive():
    from .storage import Drive
    d = Drive()
    return d if d.available()[0] else None


def _print(obj) -> None:
    print(json.dumps(obj, indent=1, ensure_ascii=False, default=str))


def _deep_update(dst: dict, src: dict) -> dict:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_update(dst[k], v)
        else:
            dst[k] = v
    return dst


# ----- research ------------------------------------------------------------------------------------
def cmd_feeds(a):
    from .research import feeds
    res = feeds.collect(a.hours)
    out = config.STATE_DIR / "research" / f"{_today()}_feeds.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    big = [e for e in res["events"] if (e["severity"].get("alert") or "").lower() in ("orange", "red", "yellow")
           or (e["severity"].get("magnitude") or 0) >= 6]
    _print({"saved": str(out), "events": len(res["events"]), "news": len(res["news"]), "errors": res["errors"],
            "notable": [f"{e['feed']} {e['type']} {e['date']} {e['title'][:90]}" for e in big[:25]]})


def cmd_research_save(a):
    """Score researcher candidates, pick up to 3 slots, add picks to the tracker."""
    from .research import scoring
    cands = json.loads(Path(a.file).read_text())
    store = Store()
    history = store.all()
    scored = [scoring.score(c, history) for c in cands]
    picks = scoring.pick_slots(scored, n=len(config.settings()["schedule"]["slots"]))
    rejected = [c for c in scored if c not in picks]
    out = config.STATE_DIR / "research" / f"{_today()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"date": _today(), "picks": picks, "rejected": rejected}, indent=1, ensure_ascii=False))
    added = []
    for c in picks:
        it = models.new_item(event_type=c["type"], title=c["title"], country=c["country"], location=c["location"],
                             event_date=c["event_date"], footage_url=c["footage_url"])
        it["event"]["sources"] = c.get("sources", [])
        it["event"]["summary"] = c.get("summary", "")
        it["event"]["new_development"] = bool(c.get("significant_new_development"))
        _deep_update(it["footage"], {k: c[k] for k in ("platform", "uploader", "original_creator", "filmed_date",
                                                         "published_date", "duration_s", "orientation", "description")
                                     if k in c})
        it["verification"]["concerns"] = c.get("concerns", [])
        it["verification"]["confidence"] = c["sub_scores"]["verification_confidence"]
        it["rights"]["status"] = c.get("rights_outlook", "unknown")
        it["score"] = c["score"]
        try:
            store.add(it)
            added.append(it["id"])
        except ValueError as exc:
            added.append(f"skipped: {exc}")
    _print({"saved": str(out), "picked": [(c["title"], c["score"]) for c in picks], "tracker": added,
            "rejected": [(c["title"], c["score"], c["blockers"]) for c in rejected]})


# ----- tracker editing -----------------------------------------------------------------------------
def cmd_show(a):
    _print(Store().get(a.id))


def cmd_update(a):
    store = Store()
    it = store.get(a.id)
    patch = json.loads(Path(a.patch).read_text()) if a.patch.endswith(".json") else json.loads(a.patch)
    for blocked in ("status", "approval", "publish", "history"):
        if blocked in patch:
            sys.exit(f"'{blocked}' can't be patched directly; use the workflow commands")
    _deep_update(it, patch)
    changed = models.invalidate_approval_if_changed(it, actor=a.by)
    store.save(it)
    _print({"id": it["id"], "status": it["status"], "approval_invalidated": changed})


def cmd_transition(a):
    store = Store()
    it = store.get(a.id)
    try:
        models.transition(it, a.status, actor=a.by, note=a.note or "")
    except models.GateError as exc:
        sys.exit(f"BLOCKED: {exc}")
    store.save(it)
    _print({"id": it["id"], "status": it["status"]})


def cmd_verify_event(a):
    """Corroborate the event against today's feed snapshot; record the check (does not mark verified alone)."""
    from .research import feeds
    store = Store()
    it = store.get(a.id)
    snap = config.STATE_DIR / "research" / f"{_today()}_feeds.json"
    events = json.loads(snap.read_text())["events"] if snap.exists() else feeds.collect(96)["events"]
    hits = feeds.corroborate(it["event"]["type"], it["event"]["country"], it["event"]["event_date"], events)
    it["verification"]["checks"].append({"at": models.now_iso(), "check": "authoritative feed corroboration",
                                         "result": [f"{h['feed']}: {h['title']} {h['url']}" for h in hits[:5]] or "no feed match"})
    store.save(it)
    _print({"matches": hits[:5]})


# ----- media -----------------------------------------------------------------------------------------
def cmd_ingest(a):
    """Attach an authorised raw file (local path or Drive file id) to an item."""
    store = Store()
    it = store.get(a.id)
    drive = _drive()
    dest_dir = config.WORK_DIR / "raw" / it["id"]
    dest_dir.mkdir(parents=True, exist_ok=True)
    if Path(a.source).exists():
        dest = dest_dir / Path(a.source).name
        if Path(a.source).resolve() != dest.resolve():
            shutil.copy2(a.source, dest)
    elif drive:
        dest = drive.download(a.source, dest_dir / f"{it['id']}_raw.mp4")
        it["footage"]["raw_drive_id"] = a.source
    else:
        sys.exit("source not found locally and Drive is not configured")
    from .edit.analyze import probe
    pr = probe(dest)
    h = hashlib.sha256(dest.read_bytes()).hexdigest()
    dup = [o["id"] for o in store.all() if o["id"] != it["id"] and o["footage"].get("sha256") == h]
    if dup:
        sys.exit(f"duplicate raw file: already used by {dup}")
    it["footage"].update(raw_path=str(dest), sha256=h, duration_s=round(pr.duration, 2),
                         orientation="vertical" if pr.display_size[1] > pr.display_size[0] else "horizontal",
                         resolution=f"{pr.display_size[0]}x{pr.display_size[1]}")
    if drive and not it["footage"].get("raw_drive_id"):
        up = drive.upload(dest, "Raw Videos", f"{it['id']}_raw{dest.suffix}")
        it["footage"]["raw_drive_id"] = up["id"]
    store.save(it)
    _print({"id": it["id"], "raw": str(dest), "duration": pr.duration, "size": pr.display_size, "audio": pr.has_audio,
            "drive": it["footage"].get("raw_drive_id") or "not uploaded (Drive not configured)"})


def cmd_edit(a):
    from .edit.qc import check_all
    from .edit.render import render
    store = Store()
    it = store.get(a.id)
    if it["status"] not in (models.READY_FOR_EDITING,):
        sys.exit(f"BLOCKED: item is {it['status']}, must be READY_FOR_EDITING")
    if not it["edit"].get("closing_headline"):
        it["edit"]["closing_headline"], it["edit"]["closing_subhead"] = captions.default_safety(it["event"]["type"])
    it["edit"]["location_line"] = captions.location_line(it)
    texts = captions.banner_texts(it)
    raw = it["footage"]["raw_path"]
    if not Path(raw).exists() and it["footage"].get("raw_drive_id"):
        raw = str(_drive().download(it["footage"]["raw_drive_id"], config.WORK_DIR / "raw" / it["id"] / "raw.mp4"))
    presets = a.presets.split(",") if a.presets else list(config.settings()["presets"])
    out_dir = config.WORK_DIR / "edits" / it["id"]
    trim = tuple(it["edit"].get("trim") or (None, None))
    res = render(raw, out_dir, texts, presets, trim=trim, basename=it["id"], fit_mode=a.fit)
    qc = check_all(res)
    drive = _drive()
    for name, meta in res.items():
        o = {"path": meta["path"], "sha256": meta["sha256"], "qc": qc[name], "crop": meta["crop"],
             "opening": {k: meta["opening"][k] for k in ("rect", "zone", "overlap")},
             "closing": {k: meta["closing"][k] for k in ("rect", "zone", "overlap")}, "preview": qc[name]["preview"]}
        if drive:
            folder = __import__("wi.storage", fromlist=["PRESET_FOLDER"]).PRESET_FOLDER[name]
            up = drive.upload(meta["path"], folder)
            o.update(drive_id=up["id"], drive_url=up.get("webViewLink"))
            pv = drive.upload(qc[name]["preview"], "Video Previews")
            o["preview_url"] = pv.get("webViewLink")
        it["edit"]["outputs"][name] = o
    it["edit"]["fit_mode"] = a.fit
    models.invalidate_approval_if_changed(it, actor="editor")
    if all(q["passed"] for q in qc.values()):
        models.transition(it, models.EDITED, actor="editor")
    else:
        store.log_error(it, "; ".join(f"{k}: {q['hard_failures']}" for k, q in qc.items() if not q["passed"]), stage="qc")
    store.save(it)
    _print({k: {"passed": q["passed"], "hard": q["hard_failures"], "flags": q["review_flags"], "preview": q["preview"]}
            for k, q in qc.items()})


def cmd_captions(a):
    store = Store()
    it = store.get(a.id)
    try:
        it["captions"] = captions.build(it)
    except captions.CaptionError as exc:
        sys.exit(f"BLOCKED: {exc}")
    models.invalidate_approval_if_changed(it, actor="captions")
    drive = _drive()
    if drive:
        txt = "\n\n".join(f"===== {k} =====\n{v}" for k, v in it["captions"].items())
        up = drive.upload_text(txt, "Captions", f"{it['id']}_captions.txt")
        it["captions_drive_url"] = up.get("webViewLink")
    store.save(it)
    _print(it["captions"])


def cmd_package(a):
    store = Store()
    it = store.get(a.id)
    slot = next((s for s in config.settings()["schedule"]["slots"] if s["id"] == a.slot), None)
    if a.slot and not slot:
        sys.exit(f"unknown slot {a.slot}")
    it["schedule"].update(date=a.date or _today(), slot=a.slot or "", time=slot["time"] if slot else "")
    if a.platforms:
        it["proposed_platforms"] = a.platforms.split(",")
    try:
        if it["status"] == models.EDITED:
            models.transition(it, models.READY_FOR_APPROVAL, actor="packager")
    except models.GateError as exc:
        sys.exit(f"BLOCKED: {exc}")
    if it["status"] != models.READY_FOR_APPROVAL:
        sys.exit(f"BLOCKED: item is {it['status']}")
    if not any(o.get("drive_url") for o in it["edit"]["outputs"].values()):
        it["verification"]["concerns"] = list(dict.fromkeys(it["verification"]["concerns"] + [
            "Edited files are not in Drive (Drive credentials missing), so reviewers can't open the videos yet."]))
    store.save(it)
    version = models.content_hash(it)
    res = slack.send(slack.review_package(it, slot), kind="review_package", item_id=it["id"],
                     dedupe_key=f"review:{it['id']}:{version}",
                     files=[o["preview"] for o in it["edit"]["outputs"].values() if o.get("preview")][:2])
    it["approval"]["requested_version"] = version
    store.save(it)
    _print({"version": version, "slack": res})


def cmd_approvals(a):
    from . import approvals
    store = Store()
    it = store.get(a.id)
    if a.thread:
        msgs = json.loads(Path(a.thread).read_text())
    else:   # bot mode: read the review thread directly
        ts = slack.review_ts(it["id"])
        if not ts:
            sys.exit("no review package ts on record for this item")
        msgs = slack.read_thread(ts)
    try:
        res = approvals.apply(it, msgs)
    except models.GateError as exc:
        sys.exit(f"BLOCKED: {exc}")
    store.save(it)
    _print({**res, "status": it["status"]})


# ----- publishing / reporting -------------------------------------------------------------------------
def cmd_record_post(a):
    """Record a post made manually (or confirmed after needs_check) so tracking and analytics include it."""
    store = Store()
    it = store.get(a.id)
    if a.platform not in config.settings()["platforms"]:
        sys.exit(f"unknown platform {a.platform}")
    if not a.url.startswith("https://"):
        sys.exit("url must be the public https post link")
    led = it["publish"].setdefault(a.platform, {})
    led.update(status="published", url=a.url, post_id=a.post_id or led.get("post_id", ""), published_at=models.now_iso(),
               recorded_by=a.by, method="manual" if led.get("status") in (None, "manual", "pending") else "confirmed")
    if it["status"] == models.APPROVED:
        models.transition(it, models.SCHEDULED, actor=a.by)
    if it["status"] == models.SCHEDULED:
        models.transition(it, models.PUBLISHED, actor=a.by, note=f"{a.platform} recorded manually")
    store.save(it)
    _print({"id": it["id"], "status": it["status"], a.platform: led})


def cmd_publish_slot(a):
    from .publish.runner import run_slot
    _print(run_slot(a.slot, dry_run=a.dry_run))


def cmd_analytics(a):
    from .analytics.collect import collect
    snap = collect()
    _print({p: {"connected": e["connected"], "posts": len(e["posts"]), "account": e["account"], "error": e.get("error")}
            for p, e in snap["platforms"].items()})


def cmd_report(a):
    from . import report
    text = report.build(a.date)
    if a.send:
        _print(slack.send(text, kind="daily_report", dedupe_key=f"daily_report:{a.date or _today()}"))
    else:
        print(text)


def cmd_health(a):
    from .publish.runner import connection_status
    from .storage import Drive
    store = Store()
    _print({"control": store.control(), "publishing_live": config.settings()["control"]["publishing_live"],
            "drive": Drive().available(), "slack_bot_token": bool(config.env("SLACK_BOT_TOKEN")),
            "platforms": connection_status(),
            "items_by_status": {s: len(store.by_status(s)) for s in models.STATUSES if store.by_status(s)},
            "outbox": sorted(p.name for p in slack.OUTBOX.glob("*.json")) if slack.OUTBOX.exists() else []})


def cmd_slack_commands(a):
    """Apply WI STOP / WI PAUSE / WI RESUME from approvers (bot mode)."""
    import re
    store = Store()
    approvers = config.settings()["slack"]["approvers"]
    last = store.control().get("last_command_ts", "0")
    applied = []
    for m in sorted(slack.recent_commands(), key=lambda m: float(m["ts"])):
        if float(m["ts"]) <= float(last) or m.get("user") not in approvers:
            continue
        cmd = re.match(r"^\s*WI\s+(STOP|PAUSE|RESUME)\b", m["text"], re.I)
        if not cmd:
            continue
        flags = {"STOP": {"emergency_stop": True, "paused": True}, "PAUSE": {"paused": True},
                 "RESUME": {"paused": False, "emergency_stop": False}}[cmd.group(1).upper()]
        store.set_control(**flags, reason=m["text"][:200], by=approvers[m["user"]], last_command_ts=m["ts"])
        applied.append((approvers[m["user"]], cmd.group(1).upper()))
    _print({"applied": applied, "control": store.control()})


def cmd_control(a):
    store = Store()
    flags = {"pause": {"paused": True}, "resume": {"paused": False}, "stop": {"emergency_stop": True, "paused": True},
             "unstop": {"emergency_stop": False}}[a.action]
    _print(store.set_control(**flags, reason=a.reason or "", by=a.by))


def cmd_outbox(a):
    msgs = [json.loads(p.read_text()) for p in sorted(slack.OUTBOX.glob("*.json"))] if slack.OUTBOX.exists() else []
    _print(msgs)


def cmd_slack_sent(a):
    slack.mark_sent(a.id, a.ts)
    print("recorded")


def cmd_tracker_csv(a):
    print(Store().to_csv())


def cmd_sheet_sync(a):
    from .analytics.collect import load
    from .storage import sync_tracker
    d = _drive()
    if not d:
        sys.exit("Google credentials not configured; tracker stays in state/tracker.json")
    rows = []
    snap = load(_today())
    if snap and a.with_analytics:
        for p, e in snap["platforms"].items():
            fol = e.get("account", {}).get("followers")
            for iid, m in e["posts"].items():
                rows.append([snap["date"], p, iid, m.get("views"), m.get("reach"), m.get("likes"), m.get("comments"),
                             m.get("shares"), m.get("saves"), round((m.get("avg_watch_ms") or 0) / 1000, 1) or None, fol])
            if e["connected"] and not e["posts"]:
                rows.append([snap["date"], p, "", None, None, None, None, None, None, None, fol])
    _print(sync_tracker(d, Store().to_csv(), rows))


def cmd_drive_init(a):
    d = _drive()
    if not d:
        sys.exit("Drive not configured")
    _print(d.init_folders(a.root))


def main(argv=None):
    p = argparse.ArgumentParser(prog="wi")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *args):
        sp = sub.add_parser(name)
        for spec in args:
            sp.add_argument(*spec[0], **spec[1])
        sp.set_defaults(fn=fn)

    add("feeds", cmd_feeds, (["--hours"], {"type": int, "default": 72}))
    add("research-save", cmd_research_save, (["file"], {}))
    add("show", cmd_show, (["id"], {}))
    add("update", cmd_update, (["id"], {}), (["patch"], {}), (["--by"], {"default": "claude"}))
    add("transition", cmd_transition, (["id"], {}), (["status"], {}), (["--by"], {"default": "claude"}),
        (["--note"], {}))
    add("verify-event", cmd_verify_event, (["id"], {}))
    add("ingest", cmd_ingest, (["id"], {}), (["source"], {}))
    add("edit", cmd_edit, (["id"], {}), (["--presets"], {}), (["--fit"], {"default": "fill", "choices": ["fill", "blur"]}))
    add("captions", cmd_captions, (["id"], {}))
    add("package", cmd_package, (["id"], {}), (["--slot"], {}), (["--date"], {}), (["--platforms"], {}))
    add("approvals", cmd_approvals, (["id"], {}), (["thread"], {"nargs": "?"}))
    add("publish-slot", cmd_publish_slot, (["slot"], {}), (["--dry-run"], {"action": "store_true"}))
    add("record-post", cmd_record_post, (["id"], {}), (["platform"], {}), (["url"], {}), (["--post-id"], {}),
        (["--by"], {"default": "team"}))
    add("analytics", cmd_analytics)
    add("report", cmd_report, (["--date"], {}), (["--send"], {"action": "store_true"}))
    add("health", cmd_health)
    add("control", cmd_control, (["action"], {"choices": ["pause", "resume", "stop", "unstop"]}),
        (["--reason"], {}), (["--by"], {"default": "claude"}))
    add("outbox", cmd_outbox)
    add("slack-commands", cmd_slack_commands)
    add("slack-sent", cmd_slack_sent, (["id"], {}), (["ts"], {}))
    add("tracker-csv", cmd_tracker_csv)
    add("sheet-sync", cmd_sheet_sync, (["--with-analytics"], {"action": "store_true"}))
    add("drive-init", cmd_drive_init, (["--root"], {}))
    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
