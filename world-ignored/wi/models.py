"""Content item model, status workflow and publishing gates.

Items are plain dicts so they serialise straight to state/tracker.json. Every status change goes
through `transition()`, which enforces the workflow and the verification/rights/approval gates.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

UNVERIFIED = "UNVERIFIED"
EVENT_VERIFIED = "EVENT_VERIFIED/FOOTAGE_UNVERIFIED"
FOOTAGE_VERIFIED = "FOOTAGE_VERIFIED/RIGHTS_PENDING"
RIGHTS_CLEARED = "RIGHTS_CLEARED"
READY_FOR_EDITING = "READY_FOR_EDITING"
EDITED = "EDITED"
READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
APPROVED = "APPROVED"
SCHEDULED = "SCHEDULED"
PUBLISHED = "PUBLISHED"
FAILED = "FAILED"
ARCHIVED = "ARCHIVED"

STATUSES = [UNVERIFIED, EVENT_VERIFIED, FOOTAGE_VERIFIED, RIGHTS_CLEARED, READY_FOR_EDITING, EDITED,
            READY_FOR_APPROVAL, APPROVED, SCHEDULED, PUBLISHED, FAILED, ARCHIVED]

# Forward path plus the allowed step-backs (changes requested, content changed after approval, retries).
ALLOWED = {
    UNVERIFIED: {EVENT_VERIFIED},
    EVENT_VERIFIED: {FOOTAGE_VERIFIED, UNVERIFIED},
    FOOTAGE_VERIFIED: {RIGHTS_CLEARED},
    RIGHTS_CLEARED: {READY_FOR_EDITING},
    READY_FOR_EDITING: {EDITED},
    EDITED: {READY_FOR_APPROVAL, READY_FOR_EDITING},
    READY_FOR_APPROVAL: {APPROVED, READY_FOR_EDITING, EDITED},
    APPROVED: {SCHEDULED, READY_FOR_APPROVAL, READY_FOR_EDITING},
    SCHEDULED: {PUBLISHED, APPROVED, READY_FOR_APPROVAL},
    PUBLISHED: set(),
    FAILED: {READY_FOR_EDITING, READY_FOR_APPROVAL, APPROVED},
    ARCHIVED: set(),
}

# Licence types that can clear footage for social reuse. "credit_only" is deliberately absent:
# crediting a filmer does not grant permission.
CLEARING_LICENSES = {
    "written_permission",      # direct permission from the filmer / rights holder (stored evidence)
    "licensed_agency",         # paid licence from an agency (Storyful, Newsflare, ViralHog, Reuters, AP...)
    "public_domain",           # e.g. US federal government works
    "cc_by", "cc_by_sa", "cc0",
    "official_release",        # agency/government footage released for media reuse, with terms stored
    "own_footage",
}


class GateError(Exception):
    """Raised when an item is not allowed to move to the requested status."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(text: str, limit: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:limit].rstrip("-")


def new_item(*, event_type: str, title: str, country: str, location: str, event_date: str,
             footage_url: str, discovered_by: str = "research") -> dict:
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    return {
        "id": f"WI-{day}-{slugify(country, 12)}-{slugify(title, 24)}",
        "status": UNVERIFIED,
        "created_at": now_iso(),
        "discovered_by": discovered_by,
        "event": {"type": event_type, "title": title, "country": country, "location": location,
                  "event_date": event_date, "sources": [], "new_development": False},
        "footage": {"url": footage_url, "platform": "", "uploader": "", "original_creator": "",
                    "filmed_date": "", "published_date": "", "duration_s": None, "orientation": "",
                    "description": "", "raw_path": "", "raw_drive_id": "", "sha256": ""},
        "verification": {"event_verified": False, "footage_verified": False, "confidence": 0.0,
                         "checks": [], "concerns": []},
        "rights": {"status": "pending", "holder": "", "license_type": "", "evidence_ref": "",
                   "permitted_platforms": [], "attribution": "", "restrictions": "", "obtained_at": ""},
        "edit": {"headline": "", "subhead": "", "location_line": "", "closing_headline": "",
                 "closing_subhead": "", "trim": [None, None], "outputs": {}, "content_hash": "",
                 "flags": []},
        "captions": {},
        "approval": {"status": "none", "by": "", "at": "", "content_hash": "", "platforms": [],
                     "slack_ts": "", "notes": ""},
        "schedule": {"date": "", "slot": "", "time": ""},
        "publish": {},
        "metrics": {},
        "history": [],
        "errors": [],
        "score": None,
    }


def content_hash(item: dict) -> str:
    """Fingerprint of everything a reviewer approves: rendered files, captions, titles, platforms.

    Any change to these produces a new hash, which invalidates an earlier approval.
    """
    outputs = {k: v.get("sha256", "") for k, v in sorted(item["edit"].get("outputs", {}).items())}
    payload = {
        "outputs": outputs,
        "captions": item.get("captions", {}),
        "headline": item["edit"].get("headline"),
        "subhead": item["edit"].get("subhead"),
        "location_line": item["edit"].get("location_line"),
        "closing": [item["edit"].get("closing_headline"), item["edit"].get("closing_subhead")],
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()[:12]


def rights_clear(item: dict) -> tuple[bool, str]:
    r = item["rights"]
    if r.get("license_type") not in CLEARING_LICENSES:
        return False, f"licence type '{r.get('license_type') or 'none'}' does not clear reuse"
    if not r.get("evidence_ref"):
        return False, "no stored permission/licence evidence"
    if not r.get("holder"):
        return False, "rights holder not identified"
    if not r.get("permitted_platforms"):
        return False, "permitted platforms not recorded"
    return True, "ok"


def approval_valid(item: dict, platforms: list[str] | None = None) -> tuple[bool, str]:
    a = item["approval"]
    if a.get("status") == "stale":
        return False, "content changed since approval; re-approval required"
    if a.get("status") != "approved":
        return False, f"approval status is '{a.get('status')}'"
    if a.get("content_hash") != content_hash(item):
        return False, "content changed since approval; re-approval required"
    for p in platforms or []:
        if p not in a.get("platforms", []):
            return False, f"platform '{p}' not in approved platforms"
    return True, "ok"


def check_gate(item: dict, target: str) -> None:
    """Raise GateError if `item` may not enter `target`."""
    v = item["verification"]
    if target in (EVENT_VERIFIED,) and not item["event"]["sources"]:
        raise GateError("event needs at least one reliable source")
    if target == EVENT_VERIFIED and not v["event_verified"]:
        raise GateError("event not marked verified")
    if target == FOOTAGE_VERIFIED and not (v["event_verified"] and v["footage_verified"]):
        raise GateError("footage not verified against the event")
    if target in (RIGHTS_CLEARED, READY_FOR_EDITING, EDITED, READY_FOR_APPROVAL, APPROVED, SCHEDULED, PUBLISHED):
        ok, why = rights_clear(item)
        if not ok:
            raise GateError(f"rights not cleared: {why}")
        if not v["footage_verified"]:
            raise GateError("footage not verified")
    if target == READY_FOR_EDITING and not item["footage"].get("raw_path") and not item["footage"].get("raw_drive_id"):
        raise GateError("no authorised raw file on record")
    if target == READY_FOR_APPROVAL:
        outs = item["edit"].get("outputs", {})
        if not outs:
            raise GateError("no rendered outputs")
        failed = [k for k, o in outs.items() if not o.get("qc", {}).get("passed")]
        if failed:
            raise GateError(f"QC failed or pending for: {', '.join(failed)}")
        if not item.get("captions"):
            raise GateError("captions missing")
    if target in (APPROVED, SCHEDULED, PUBLISHED):
        ok, why = approval_valid(item)
        if not ok:
            raise GateError(why)


def transition(item: dict, target: str, *, actor: str, note: str = "") -> dict:
    if target not in STATUSES:
        raise GateError(f"unknown status {target}")
    current = item["status"]
    if target not in (FAILED, ARCHIVED) and target not in ALLOWED.get(current, set()):
        raise GateError(f"{current} -> {target} is not an allowed transition")
    if target not in (FAILED, ARCHIVED):
        check_gate(item, target)
    item["status"] = target
    item["history"].append({"at": now_iso(), "from": current, "to": target, "by": actor, "note": note})
    return item


def invalidate_approval_if_changed(item: dict, actor: str = "system") -> bool:
    """Drop an approval whose content hash no longer matches. Returns True if it was invalidated."""
    a = item["approval"]
    if a.get("status") == "approved" and a.get("content_hash") != content_hash(item):
        a.update(status="stale", notes="content changed after approval")
        if item["status"] in (APPROVED, SCHEDULED):
            item["status"] = READY_FOR_APPROVAL
            item["history"].append({"at": now_iso(), "from": APPROVED, "to": READY_FOR_APPROVAL,
                                    "by": actor, "note": "content changed; re-approval required"})
        return True
    return False
