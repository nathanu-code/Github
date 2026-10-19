"""Apply reviewer decisions from the review-package thread.

Rules (enforced here, not by convention):
  * Only users listed in settings.slack.approvers count. The automation's own identity never counts.
  * A decision must quote the current version code (content hash). Decisions about an older version
    are ignored, so a changed video or caption always needs a fresh approval.
  * Decisions are applied in time order; the latest one from an approver wins.
  * Silence is never approval.
"""
from __future__ import annotations

import re

from . import config, models

PATTERN = re.compile(r"^\s*(APPROVE|APPROVED|REQUEST CHANGES|CHANGES|HOLD|REJECT)\b[\s:]*([0-9a-f]{12})?\s*(.*)$",
                     re.I | re.S)
ACTION = {"approve": "approved", "approved": "approved", "request changes": "changes_requested",
          "changes": "changes_requested", "hold": "hold", "reject": "rejected"}


def parse(text: str) -> tuple[str, str | None, str] | None:
    m = PATTERN.match(text.replace("*", "").replace("`", ""))
    if not m:
        return None
    return ACTION[m.group(1).lower()], (m.group(2) or "").lower() or None, m.group(3).strip()


def apply(item: dict, messages: list[dict]) -> dict:
    """messages: thread replies as [{user, ts, text}] (from Slack conversations.replies or the connector)."""
    s = config.settings()["slack"]
    approvers = s["approvers"]
    me = s.get("automation_identity")
    version = models.content_hash(item)
    enabled = [p for p, c in config.settings()["platforms"].items() if c["enabled"]]
    proposed = item.get("proposed_platforms") or enabled
    decision = None
    ignored = []
    for msg in sorted(messages, key=lambda m: float(m["ts"])):
        parsed = parse(msg.get("text", ""))
        if not parsed:
            continue
        action, ver, rest = parsed
        user = msg.get("user")
        if user == me or user not in approvers:
            ignored.append(f"{user}: not an authorised approver")
            continue
        if ver != version:
            ignored.append(f"{approvers[user]}: version {ver or 'missing'} != current {version}")
            continue
        platforms = proposed
        if action == "approved" and rest:
            named = [p.strip().lower() for p in re.split(r"[,\s]+", rest) if p.strip()]
            if named and named != ["all"]:
                unknown = [p for p in named if p not in enabled]
                if unknown:
                    ignored.append(f"{approvers[user]}: unknown platform(s) {unknown}")
                    continue
                platforms = named
        decision = {"status": action, "by": approvers[user], "by_id": user, "at": msg["ts"], "content_hash": ver,
                    "platforms": platforms if action == "approved" else [], "notes": rest}
    result = {"version": version, "decision": decision, "ignored": ignored}
    if decision:
        item["approval"].update({k: v for k, v in decision.items() if k != "by_id"})
        actor = f"slack:{decision['by']}"
        if decision["status"] == "approved" and item["status"] == models.READY_FOR_APPROVAL:
            models.transition(item, models.APPROVED, actor=actor, note=f"platforms={','.join(decision['platforms'])}")
        elif decision["status"] == "changes_requested" and item["status"] in (models.READY_FOR_APPROVAL, models.APPROVED):
            item["edit"]["change_request"] = decision["notes"]
            models.transition(item, models.READY_FOR_EDITING, actor=actor, note=decision["notes"])
        elif decision["status"] == "rejected":
            models.transition(item, models.ARCHIVED, actor=actor, note=f"rejected: {decision['notes']}")
    return result
