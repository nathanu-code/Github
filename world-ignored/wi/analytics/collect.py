"""Daily analytics snapshot from each connected platform's official API.

state/analytics/<date>.json = {
  "collected_at": ..., "platforms": {p: {"connected": bool, "account": {...}, "posts": {item_id: {...}}, "error": ...}}
}
Metrics a platform doesn't provide are simply absent (never estimated).
"""
from __future__ import annotations

import json
from datetime import datetime

from .. import config
from ..models import now_iso
from ..publish.runner import ADAPTERS, adapter
from ..store import Store

SNAP_DIR = config.STATE_DIR / "analytics"


def collect(date_iso: str | None = None) -> dict:
    date_iso = date_iso or datetime.now(config.tz()).date().isoformat()
    store = Store()
    snap = {"date": date_iso, "collected_at": now_iso(), "platforms": {}}
    published = [i for i in store.all() if i.get("publish")]
    for name in ADAPTERS:
        ad = adapter(name)
        ok, why = ad.available()
        entry = {"connected": ok, "detail": why, "account": {}, "posts": {}}
        if ok:
            try:
                entry["account"] = ad.account_metrics()
            except Exception as exc:  # noqa: BLE001 - one platform failing must not stop the report
                entry["error"] = f"account: {exc.__class__.__name__}: {str(exc)[:160]}"
            for it in published:
                led = it["publish"].get(name, {})
                if led.get("post_id") and led.get("status") in ("published", "processing"):
                    try:
                        m = {k: v for k, v in ad.post_metrics(led["post_id"]).items() if v is not None}
                        entry["posts"][it["id"]] = m
                        it.setdefault("metrics", {})[name] = {**m, "at": now_iso()}
                        store.save(it)
                    except Exception as exc:  # noqa: BLE001
                        entry.setdefault("post_errors", []).append(f"{it['id']}: {str(exc)[:120]}")
        snap["platforms"][name] = entry
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    (SNAP_DIR / f"{date_iso}.json").write_text(json.dumps(snap, indent=1))
    return snap


def load(date_iso: str) -> dict | None:
    p = SNAP_DIR / f"{date_iso}.json"
    return json.loads(p.read_text()) if p.exists() else None
