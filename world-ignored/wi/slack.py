"""Slack delivery for #world-ignored: review packages, confirmations, reports, alerts.

Two transports:
  * Bot token (SLACK_BOT_TOKEN, scopes chat:write, files:write, channels:history/groups:history,
    reactions:read): posts and uploads directly from Python.
  * Connector outbox (default today): messages are written to work/outbox/*.json and the scheduled
    Claude session posts them with the Slack connector, then records the message ts with
    `wi slack-sent`. The connector posts as the signed-in user (see settings.slack.automation_identity).

Secrets are never put in messages.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import requests

from . import config, models
from .models import now_iso

OUTBOX = config.STATE_DIR / "outbox"   # persisted with state so undelivered messages survive the run
_SECRETISH = re.compile(r"(xox[abpr]-[\w-]+|EAA[\w]{20,}|ya29\.[\w.-]+|sk-[\w-]{20,}|AIza[\w-]{30,})")


def scrub(text: str) -> str:
    return _SECRETISH.sub("[redacted]", text)


def channel() -> str:
    return config.settings()["slack"]["channel_id"]


def send(text: str, *, kind: str, thread_ts: str | None = None, files: list[str] | None = None,
         item_id: str | None = None, dedupe_key: str | None = None) -> dict:
    """Post now (bot token) or queue for the connector. dedupe_key prevents double posts across retries."""
    text = scrub(text)
    sent_log = config.STATE_DIR / "slack_sent.json"
    sent = json.loads(sent_log.read_text()) if sent_log.exists() else {}
    if dedupe_key and dedupe_key in sent:
        return {"status": "duplicate_skipped", **sent[dedupe_key]}
    if dedupe_key and OUTBOX.exists():   # already queued but not yet delivered
        for q in OUTBOX.glob("*.json"):
            if json.loads(q.read_text()).get("dedupe_key") == dedupe_key:
                return {"status": "already_queued", "id": q.stem}
    token = config.env("SLACK_BOT_TOKEN")
    if token:
        h = {"Authorization": f"Bearer {token}"}
        body = {"channel": channel(), "text": text, "unfurl_links": False, "mrkdwn": True}
        if thread_ts:
            body["thread_ts"] = thread_ts
        r = requests.post("https://slack.com/api/chat.postMessage", headers=h, json=body, timeout=30).json()
        if not r.get("ok"):
            raise RuntimeError(f"Slack error: {r.get('error')}")
        for f in files or []:
            _upload(h, f, r["ts"])
        rec = {"ts": r["ts"], "at": now_iso(), "kind": kind, "item_id": item_id}
        if dedupe_key:
            sent[dedupe_key] = rec
            sent_log.write_text(json.dumps(sent, indent=1))
        return {"status": "sent", **rec}
    OUTBOX.mkdir(parents=True, exist_ok=True)
    msg_id = f"{now_iso().replace(':', '').replace('-', '')}_{kind}_{(item_id or 'all')}"[:120]
    payload = {"id": msg_id, "channel_id": channel(), "text": text, "thread_ts": thread_ts, "kind": kind,
               "item_id": item_id, "files": files or [], "dedupe_key": dedupe_key}
    (OUTBOX / f"{msg_id}.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    return {"status": "queued", "id": msg_id}


def _upload(h: dict, path: str, thread_ts: str) -> None:
    p = Path(path)
    r = requests.post("https://slack.com/api/files.getUploadURLExternal", headers=h, timeout=30,
                      data={"filename": p.name, "length": p.stat().st_size}).json()
    if not r.get("ok"):
        raise RuntimeError(f"Slack upload error: {r.get('error')}")
    with open(p, "rb") as fh:
        requests.post(r["upload_url"], files={"file": fh}, timeout=300).raise_for_status()
    c = requests.post("https://slack.com/api/files.completeUploadExternal", headers=h, timeout=30, json={
        "files": [{"id": r["file_id"], "title": p.name}], "channel_id": channel(), "thread_ts": thread_ts}).json()
    if not c.get("ok"):
        raise RuntimeError(f"Slack upload error: {c.get('error')}")


def mark_sent(msg_id: str, ts: str) -> None:
    """Record that the connector posted an outbox message (keeps dedupe working in connector mode)."""
    p = OUTBOX / f"{msg_id}.json"
    msg = json.loads(p.read_text())
    sent_log = config.STATE_DIR / "slack_sent.json"
    sent = json.loads(sent_log.read_text()) if sent_log.exists() else {}
    key = msg.get("dedupe_key") or msg_id
    sent[key] = {"ts": ts, "at": now_iso(), "kind": msg["kind"], "item_id": msg.get("item_id")}
    sent_log.write_text(json.dumps(sent, indent=1))
    p.rename(p.with_suffix(".sent"))


def read_thread(ts: str) -> list[dict]:
    """Thread replies via the bot token: [{user, ts, text}]."""
    token = config.env("SLACK_BOT_TOKEN")
    if not token:
        raise RuntimeError("SLACK_BOT_TOKEN not set; read the thread with the Slack connector instead")
    r = requests.get("https://slack.com/api/conversations.replies", headers={"Authorization": f"Bearer {token}"},
                     params={"channel": channel(), "ts": ts, "limit": 200}, timeout=30).json()
    if not r.get("ok"):
        raise RuntimeError(f"Slack error: {r.get('error')}")
    return [{"user": m.get("user"), "ts": m["ts"], "text": m.get("text", "")} for m in r["messages"][1:]]


def recent_commands(limit: int = 50) -> list[dict]:
    """Recent channel messages (bot mode), used for WI STOP / WI PAUSE / WI RESUME."""
    token = config.env("SLACK_BOT_TOKEN")
    if not token:
        return []
    r = requests.get("https://slack.com/api/conversations.history", headers={"Authorization": f"Bearer {token}"},
                     params={"channel": channel(), "limit": limit}, timeout=30).json()
    return [{"user": m.get("user"), "ts": m["ts"], "text": m.get("text", "")} for m in r.get("messages", [])]


def review_ts(item_id: str) -> str | None:
    """ts of the latest review package posted for an item (for threading replies)."""
    sent_log = config.STATE_DIR / "slack_sent.json"
    if not sent_log.exists():
        return None
    recs = [r for r in json.loads(sent_log.read_text()).values()
            if r.get("item_id") == item_id and r.get("kind") == "review_package"]
    return max(recs, key=lambda r: r["at"])["ts"] if recs else None


# --- message builders -------------------------------------------------------------------------
def review_package(item: dict, slot: dict | None) -> str:
    e, f, r, v = item["event"], item["footage"], item["rights"], item["verification"]
    ed = item["edit"]
    version = models.content_hash(item)
    outs = ed.get("outputs", {})
    platforms = item.get("proposed_platforms") or [p for p, c in config.settings()["platforms"].items() if c["enabled"]]

    def link(o, label):
        return f"<{o['drive_url']}|{label}>" if o.get("drive_url") else f"{label} (not uploaded)"

    flags = []
    for name, o in outs.items():
        flags += [f"{name}: {x}" for x in o.get("qc", {}).get("review_flags", [])]
    concerns = v.get("concerns", []) + flags
    sources = "\n".join(f"• <{s['url']}|{s.get('name', s['url'])}>" for s in e.get("sources", [])[:5])
    caps = item.get("captions", {})
    slot_txt = f"{slot['id']} · {item['schedule'].get('date')} {slot['time']} PHT" if slot else "unscheduled"
    lines = [
        f"*REVIEW · {e['title'].upper()}*  `{item['id']}`  version `{version}`",
        f"📍 {e['location']}, {e['country']}  ·  📅 event {e['event_date']}  ·  {e['type']}",
        f"*Original footage:* <{f['url']}|link> · filmed {f.get('filmed_date') or 'unconfirmed'} · posted {f.get('published_date') or '?'}",
        f"*Filmer / rights holder:* {f.get('original_creator') or 'unknown'} / {r.get('holder') or 'unknown'} · "
        f"*Rights:* {r.get('status')} ({r.get('license_type') or 'none'}) · evidence: {r.get('evidence_ref') or 'none'}",
        f"*Verification:* event {'✅' if v['event_verified'] else '❌'} · footage {'✅' if v['footage_verified'] else '❌'} · "
        f"confidence {v.get('confidence', 0):.0%}",
        f"*Sources:*\n{sources or '• none'}",
        f"*Edits:* {link(outs.get('v9x16', {}), '9:16 video')} · {link(outs.get('f4x5', {}), '4:5 video')} · "
        f"{link({'drive_url': outs.get('v9x16', {}).get('preview_url')}, 'preview frames')}",
        f"*Proposed slot:* {slot_txt}",
        f"*Platforms:* {', '.join(platforms)}",
        "",
        "*Main caption (IG/FB):*",
        "```" + caps.get("instagram_reels", "(missing)")[:1800] + "```",
        f"*X:* ```{caps.get('x', '(missing)')}```",
        f"*YouTube title:* {caps.get('youtube_title', '(missing)')}",
        "Full per-platform captions: see the Captions file in Drive." if caps else "",
        "",
        ("⚠️ *Concerns:*\n" + "\n".join(f"• {c}" for c in concerns)) if concerns else "No open concerns.",
        "",
        f"*Reply in this thread* (approvers only) with one of:",
        f"`APPROVE {version}` (all platforms listed) · `APPROVE {version} tiktok,youtube_shorts` · "
        f"`REQUEST CHANGES {version} <what to change>` · `HOLD {version}` · `REJECT {version} <reason>`",
        "No reply = not approved. Any change to the video or captions creates a new version that needs a new approval.",
    ]
    return "\n".join(x for x in lines if x is not None)


def confirmation(item: dict, results: dict) -> str:
    rows = []
    for p, res in results.items():
        if res.get("url"):
            rows.append(f"✅ {p}: <{res['url']}|post>")
        elif res.get("status") == "manual":
            rows.append(f"📝 {p}: manual upload needed ({res.get('reason', '')})")
        else:
            rows.append(f"❌ {p}: {res.get('status')} {res.get('error', '')[:120]}")
    head = "PUBLISHED" if any(r.get("url") for r in results.values()) else "PUBLISH UPDATE"
    manual = [p for p, r in results.items() if r.get("status") == "manual"]
    tail = ""
    if manual:
        outs = item["edit"]["outputs"]
        files = ", ".join(f"<{o['drive_url']}|{k}>" for k, o in outs.items() if o.get("drive_url")) or "files not in Drive yet"
        tail = (f"\n*Manual upload package:* {files} · captions: "
                f"{('<' + item['captions_drive_url'] + '|captions file>') if item.get('captions_drive_url') else 'see tracker'}"
                f"\nAfter posting manually, reply in this thread with the post links so the tracker can record them.")
    return f"*{head} · {item['event']['title'].upper()}* `{item['id']}`\n" + "\n".join(rows) + tail


def alert(title: str, detail: str, action: str) -> str:
    return f"🚨 *{title}*\n{scrub(detail)[:1500]}\n*Action needed:* {action}"
