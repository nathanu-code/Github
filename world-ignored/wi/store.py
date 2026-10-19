"""Tracker store: state/tracker.json is the source of truth; a CSV export mirrors it to Google Sheets.

Writes are atomic (temp file + rename) and serialised with a file lock, so an interrupted job never
leaves a half-written tracker.
"""
from __future__ import annotations

import csv
import fcntl
import io
import json
import os
import re
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from . import config
from .models import now_iso

TRACKER = "tracker.json"
CONTROL = "control.json"

# Query parameters that only track the share and don't identify the video.
_TRACKING = {"s", "t", "si", "igsh", "igshid", "utm_source", "utm_medium", "utm_campaign", "ref", "feature", "share_id"}


def normalize_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    host = parts.netloc.lower().removeprefix("www.").removeprefix("m.").removeprefix("mobile.")
    host = {"twitter.com": "x.com", "youtu.be": "youtube.com"}.get(host, host)
    path = parts.path.rstrip("/")
    if parts.netloc.lower().endswith("youtu.be"):
        return f"youtube.com/watch?v={path.lstrip('/')}"
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parts.query) if k.lower() not in _TRACKING))
    return urlunsplit(("", host, path, query, "")).lstrip("/")


def event_key(item: dict) -> str:
    e = item["event"]
    loc = re.sub(r"[^a-z]", "", (e.get("location") or "").lower())[:20]
    country = re.sub(r"[^a-z]", "", (e.get("country") or "").lower())
    return f"{e.get('type','').lower()}|{country}|{loc}|{e.get('event_date','')}"


class Store:
    def __init__(self, state_dir: Path | None = None):
        self.dir = Path(state_dir or config.STATE_DIR)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / TRACKER

    @contextmanager
    def _locked(self):
        with open(self.dir / ".lock", "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _read(self) -> dict:
        if not self.path.exists():
            return {"version": 1, "items": {}, "updated_at": None}
        with open(self.path, encoding="utf-8") as fh:
            return json.load(fh)

    def _write(self, data: dict) -> None:
        data["updated_at"] = now_iso()
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, ensure_ascii=False, sort_keys=True)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.path)

    # --- reads -----------------------------------------------------------------------------
    def all(self) -> list[dict]:
        return list(self._read()["items"].values())

    def get(self, item_id: str) -> dict:
        items = self._read()["items"]
        if item_id not in items:
            raise KeyError(item_id)
        return items[item_id]

    def by_status(self, *statuses: str) -> list[dict]:
        return [i for i in self.all() if i["status"] in statuses]

    def find_duplicate(self, item: dict) -> dict | None:
        """Same footage URL, same raw file hash, or same event key = duplicate."""
        url = normalize_url(item["footage"].get("url", ""))
        sha = item["footage"].get("sha256")
        key = event_key(item)
        for other in self.all():
            if other["id"] == item["id"]:
                continue
            if url and normalize_url(other["footage"].get("url", "")) == url:
                return other
            if sha and other["footage"].get("sha256") == sha:
                return other
            if event_key(other) == key and other["status"] != "ARCHIVED":
                return other
        return None

    # --- writes ----------------------------------------------------------------------------
    def add(self, item: dict, *, allow_same_event: bool = False) -> dict:
        with self._locked():
            data = self._read()
            if item["id"] in data["items"]:
                raise ValueError(f"duplicate id {item['id']}")
            dup = self.find_duplicate(item)
            if dup and not (allow_same_event and normalize_url(dup["footage"]["url"]) != normalize_url(item["footage"]["url"])):
                raise ValueError(f"duplicate of {dup['id']}")
            data["items"][item["id"]] = item
            self._write(data)
            return item

    def save(self, item: dict) -> dict:
        with self._locked():
            data = self._read()
            item["updated_at"] = now_iso()
            data["items"][item["id"]] = item
            self._write(data)
            return item

    # --- control flags (pause / emergency stop) ----------------------------------------------
    def control(self) -> dict:
        p = self.dir / CONTROL
        if not p.exists():
            return {"paused": False, "emergency_stop": False, "reason": "", "by": "", "at": ""}
        return json.loads(p.read_text())

    def set_control(self, **flags) -> dict:
        with self._locked():
            c = self.control()
            c.update(flags, at=now_iso())
            p = self.dir / CONTROL
            tmp = p.with_suffix(".tmp")
            tmp.write_text(json.dumps(c, indent=1))
            os.replace(tmp, p)
            return c

    # --- Google Sheets mirror ----------------------------------------------------------------
    COLUMNS = ["Video ID", "Status", "Disaster", "Type", "Country", "Location", "Event date", "Source link",
               "Original filmer", "Rights status", "Licence", "Rights evidence", "Original file", "Edited 9:16",
               "Edited 4:5", "Verification sources", "Caption (main)", "Approval", "Approved by",
               "Scheduled", "Platforms", "Published links", "Views", "Engagements", "Errors", "Updated"]

    def to_csv(self) -> str:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(self.COLUMNS)
        for i in sorted(self.all(), key=lambda x: x["created_at"]):
            outs = i["edit"].get("outputs", {})
            pub = i.get("publish", {})
            m = i.get("metrics", {})
            w.writerow([
                i["id"], i["status"], i["event"]["title"], i["event"]["type"], i["event"]["country"],
                i["event"]["location"], i["event"]["event_date"], i["footage"]["url"],
                i["footage"].get("original_creator", ""), i["rights"]["status"], i["rights"].get("license_type", ""),
                i["rights"].get("evidence_ref", ""), i["footage"].get("raw_drive_id") or i["footage"].get("raw_path", ""),
                outs.get("v9x16", {}).get("drive_url", ""), outs.get("f4x5", {}).get("drive_url", ""),
                " ; ".join(s.get("url", "") for s in i["event"].get("sources", [])),
                i.get("captions", {}).get("instagram_feed", "")[:500], i["approval"]["status"], i["approval"].get("by", ""),
                f"{i['schedule'].get('date','')} {i['schedule'].get('time','')}".strip(),
                ",".join(i["approval"].get("platforms", [])),
                " ; ".join(f"{k}: {v.get('url','')}" for k, v in pub.items() if v.get("url")),
                sum(int(v.get("views") or 0) for v in m.values()) if m else "",
                sum(int(v.get("likes") or 0) + int(v.get("comments") or 0) + int(v.get("shares") or 0) for v in m.values()) if m else "",
                " ; ".join(e.get("msg", "") for e in i.get("errors", [])[-3:]),
                i.get("updated_at", i["created_at"]),
            ])
        return buf.getvalue()

    def log_error(self, item: dict, msg: str, *, stage: str) -> None:
        item.setdefault("errors", []).append({"at": now_iso(), "stage": stage, "msg": msg[:500]})
        self.save(item)
