"""Consolidated 7:00 AM Slack report: A. performance, B. today's queue, C. recommendations, D. automation status."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timedelta

from . import config, models
from .analytics import collect as an
from .publish.runner import connection_status
from .store import Store

RESEARCH_DIR = config.STATE_DIR / "research"
PRETTY = {"tiktok": "TikTok", "youtube_shorts": "YouTube", "instagram_reels": "IG Reels", "facebook_reels": "FB Reels",
          "threads": "Threads", "instagram_feed": "IG feed", "facebook_feed": "FB feed", "x": "X", "linkedin": "LinkedIn"}


def _n(v) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float) and not v.is_integer():
        return f"{v:,.1f}"
    return f"{int(v):,}"


def _delta(today, before) -> str:
    if today is None or before is None:
        return ""
    d = today - before
    return f" ({'+' if d >= 0 else ''}{d:,})"


def performance(today_iso: str) -> list[str]:
    snap = an.load(today_iso)
    prev = an.load((date.fromisoformat(today_iso) - timedelta(days=1)).isoformat())
    lines = ["*A. Yesterday's performance*"]
    if not snap:
        return lines + ["No analytics snapshot was collected (see Automation status)."]
    connected = [p for p, e in snap["platforms"].items() if e["connected"]]
    if not connected:
        return lines + ["No platform analytics connected yet, so no metrics to report. (Nothing is estimated.)"]
    store = Store()
    items = {i["id"]: i for i in store.all()}
    totals = defaultdict(int)
    per_video = defaultdict(lambda: defaultdict(int))
    for p in connected:
        e = snap["platforms"][p]
        pe = (prev or {}).get("platforms", {}).get(p, {})
        views = likes = comments = shares = 0
        for iid, m in e["posts"].items():
            pm = pe.get("posts", {}).get(iid, {})
            dv = (m.get("views") or 0) - (pm.get("views") or 0)   # growth since last snapshot = "yesterday"
            views += max(0, dv)
            likes += max(0, (m.get("likes") or 0) - (pm.get("likes") or 0))
            comments += max(0, (m.get("comments") or 0) - (pm.get("comments") or 0))
            shares += max(0, (m.get("shares") or 0) - (pm.get("shares") or 0))
            per_video[iid]["views"] += max(0, dv)
            per_video[iid]["eng"] += max(0, (m.get("likes") or 0) + (m.get("comments") or 0) + (m.get("shares") or 0)
                                         - (pm.get("likes") or 0) - (pm.get("comments") or 0) - (pm.get("shares") or 0))
        f_now = e.get("account", {}).get("followers")
        f_prev = pe.get("account", {}).get("followers")
        totals["views"] += views
        totals["eng"] += likes + comments + shares
        er = f"{(likes + comments + shares) / views:.1%}" if views else "n/a"
        lines.append(f"• {PRETTY.get(p, p)}: views {_n(views)} · likes {_n(likes)} · comments {_n(comments)} · "
                     f"shares {_n(shares)} · ER {er} · followers {_n(f_now)}{_delta(f_now, f_prev)}"
                     + (f" ⚠️ {e['error']}" if e.get("error") else ""))
    lines.insert(1, f"Total views {_n(totals['views'])} · engagements {_n(totals['eng'])} across {len(connected)} connected platform(s)")
    ranked = sorted(per_video.items(), key=lambda kv: -kv[1]["views"])
    if ranked:
        lines.append("*Top videos:* " + "; ".join(
            f"{items[i]['event']['title'][:50]} ({_n(v['views'])} views)" for i, v in ranked[:3] if i in items))
        if len(ranked) > 3:
            low = ranked[-1]
            if low[0] in items:
                lines.append(f"*Lowest:* {items[low[0]]['event']['title'][:50]} ({_n(low[1]['views'])} views)")
        by_type, by_slot = defaultdict(list), defaultdict(list)
        for i, v in ranked:
            if i in items:
                by_type[items[i]["event"]["type"]].append(v["views"])
                by_slot[items[i]["schedule"].get("slot", "?")].append(v["views"])
        if by_type:
            lines.append("*By category (avg views):* " + ", ".join(
                f"{k} {_n(sum(v) / len(v))}" for k, v in sorted(by_type.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))))
        if by_slot:
            lines.append("*By slot (avg views):* " + ", ".join(f"{k} {_n(sum(v) / len(v))}" for k, v in sorted(by_slot.items())))
    return lines


def queue(today_iso: str) -> list[str]:
    s = config.settings()
    store = Store()
    lines = ["*B. Today's posting queue*"]
    for slot in s["schedule"]["slots"]:
        here = [i for i in store.all() if i["schedule"].get("date") == today_iso and i["schedule"].get("slot") == slot["id"]]
        if not here:
            lines.append(f"• {slot['time']} ({slot['id']}): empty, no cleared video assigned")
            continue
        i = here[0]
        lines.append(f"• {slot['time']} ({slot['id']}): {i['event']['title'][:60]} · *{i['status']}* · `{i['id']}`")
    pending = store.by_status(models.READY_FOR_APPROVAL)
    if pending:
        lines.append("Awaiting approval: " + ", ".join(f"`{i['id']}`" for i in pending))
    rights = store.by_status(models.FOOTAGE_VERIFIED)
    if rights:
        lines.append("Waiting on footage rights: " + "; ".join(
            f"{i['event']['title'][:40]} (holder: {i['rights'].get('holder') or i['footage'].get('original_creator') or 'unknown'})"
            for i in rights))
    return lines


def recommendations(today_iso: str) -> list[str]:
    p = RESEARCH_DIR / f"{today_iso}.json"
    lines = ["*C. Today's content recommendations*"]
    if not p.exists():
        return lines + ["Research has not run yet today."]
    r = json.loads(p.read_text())
    picks = r.get("picks", [])
    if not picks:
        lines.append("No candidate met the bar (verified event, strong on-camera impact, rights obtainable). "
                     "Slots stay empty rather than filled with weak footage.")
    for k, c in enumerate(picks, 1):
        lines.append(f"{k}. *{c['title']}* · {c['location']}, {c['country']} · {c['type']} · score {c['score']:.2f}\n"
                     f"   footage: <{c['footage_url']}|link> · filmer: {c.get('original_creator') or 'unconfirmed'} · "
                     f"rights: {c.get('rights_outlook', 'unknown')}\n   {c.get('verification_summary', '')[:220]}")
    if r.get("rejected"):
        lines.append(f"_Rejected ({len(r['rejected'])}):_")
        for c in r["rejected"][:5]:
            why = "; ".join(c.get("blockers") or [f"score {c['score']:.2f} below bar"])
            lines.append(f"   • {c['title'][:70]} ({c['country']}): {why}")
    return lines


def automation_status() -> list[str]:
    store = Store()
    ctl = store.control()
    st = connection_status()
    lines = ["*D. Automation status*"]
    con = [p for p, v in st.items() if v["connected"]]
    lines.append(f"Publishing: {'🛑 EMERGENCY STOP' if ctl.get('emergency_stop') else '⏸ paused' if ctl.get('paused') else ('🟢 live' if config.settings()['control']['publishing_live'] else '🟡 dry-run (not live)')}")
    lines.append(f"Connected platforms ({len(con)}/{len(st)}): {', '.join(PRETTY[p] for p in con) or 'none'}")
    missing = [PRETTY[p] for p, v in st.items() if not v["connected"] and not v["manual_only"]]
    if missing:
        lines.append(f"Missing API access: {', '.join(missing)} (these go out as manual-upload packages; "
                     f"`python -m wi health` lists the exact credentials)")
    manual = [PRETTY[p] for p, v in st.items() if v["manual_only"]]
    if manual:
        lines.append(f"Manual by design: {', '.join(manual)} (no API for this format)")
    from .storage import Drive
    ok, why = Drive().available()
    lines.append(f"Drive storage: {'connected' if ok else '❌ ' + why}")
    lines.append(f"Slack transport: {'bot token' if config.env('SLACK_BOT_TOKEN') else 'connector (posts as automation user)'}")
    errs = [(i["id"], e) for i in store.all() for e in i.get("errors", [])
            if e["at"][:10] >= (date.today() - timedelta(days=1)).isoformat()]
    if errs:
        lines.append("Recent errors: " + "; ".join(f"`{i}` {e['stage']}: {e['msg'][:80]}" for i, e in errs[:5]))
    rot = config.STATE_DIR / "token_rotation_needed.txt"
    if rot.exists():
        lines.append("⚠️ " + rot.read_text().strip() + " (update the environment secret)")
    return lines


def build(today_iso: str | None = None) -> str:
    today_iso = today_iso or datetime.now(config.tz()).date().isoformat()
    d = date.fromisoformat(today_iso)
    parts = [f"*WORLD IGNORED · DAILY REPORT · {d.strftime('%a %b %-d, %Y')}* (PHT)"]
    for fn in (performance, queue, recommendations):
        try:
            parts.append("\n".join(fn(today_iso)))
        except Exception as exc:  # noqa: BLE001 - a broken section must not kill the report
            parts.append(f"_{fn.__name__} section failed: {exc.__class__.__name__}: {str(exc)[:120]}_")
    parts.append("\n".join(automation_status()))
    return "\n\n".join(parts)
