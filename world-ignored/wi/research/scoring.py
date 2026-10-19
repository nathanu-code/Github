"""Rank footage candidates and pick up to three daily slots.

A candidate is scored 0..1 on each criterion (in the brief's priority order). Sub-scores come from
the researcher's assessment; recency, originality and rights availability are computed here from
the tracker so repeats are penalised consistently.

Slots are filled only with candidates that reach `min_score_to_recommend` and are not repeats.
Fewer than three good candidates means fewer than three recommendations: weak or unverified
footage never fills a slot.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone

from .. import config
from ..store import normalize_url

CRITERIA = ["human_impact", "disaster_activity_on_camera", "newsworthiness", "recency",
            "verification_confidence", "video_quality", "originality", "rights_availability"]

RIGHTS_SCORE = {"cleared": 1.0, "requested": 0.6, "agency_available": 0.7, "contactable": 0.45,
                "unknown": 0.2, "refused": 0.0}


def recency_score(filmed_or_event_date: str, today: date | None = None) -> float:
    today = today or datetime.now(config.tz()).date()
    try:
        d = date.fromisoformat(filmed_or_event_date)
    except (TypeError, ValueError):
        return 0.2
    age = (today - d).days
    return 1.0 if age <= 1 else 0.8 if age == 2 else 0.6 if age == 3 else 0.3 if age <= 7 else 0.0


def repeat_info(cand: dict, history: list[dict]) -> dict:
    """How similar is this candidate to what we already posted or queued?"""
    window = config.settings()["research"]["repeat_window_days"]
    today = datetime.now(config.tz()).date()
    url = normalize_url(cand.get("footage_url", ""))
    same_event, same_country, same_type, same_url = [], 0, 0, False
    for h in history:
        if h["status"] in ("ARCHIVED",):
            continue
        if url and normalize_url(h["footage"].get("url", "")) == url:
            same_url = True
        try:
            hd = date.fromisoformat(h["event"]["event_date"])
        except (TypeError, ValueError):
            continue
        recent = (today - hd).days <= window
        if not recent:
            continue
        if h["event"]["country"].lower() == cand.get("country", "").lower():
            same_country += 1
            if h["event"]["type"].lower() == cand.get("type", "").lower() and \
               (h["event"]["location"].lower() in cand.get("location", "").lower()
                    or cand.get("location", "").lower() in h["event"]["location"].lower()):
                same_event.append(h["id"])
        if h["event"]["type"].lower() == cand.get("type", "").lower():
            same_type += 1
    return {"same_url": same_url, "same_event": same_event, "same_country_recent": same_country,
            "same_type_recent": same_type}


def score(cand: dict, history: list[dict]) -> dict:
    w = config.settings()["research"]["weights"]
    sub = {k: float(cand.get("scores", {}).get(k, 0.0)) for k in CRITERIA}
    filmed = cand.get("filmed_date") or ""
    sub["recency"] = recency_score(filmed if re.fullmatch(r"\d{4}-\d{2}-\d{2}", filmed) else cand.get("event_date"))
    rep = repeat_info(cand, history)
    orig = 1.0 - min(0.6, 0.15 * rep["same_country_recent"] + 0.1 * rep["same_type_recent"])
    if rep["same_event"] and not cand.get("significant_new_development"):
        orig = 0.0
    sub["originality"] = round(orig, 2)
    sub["rights_availability"] = RIGHTS_SCORE.get(cand.get("rights_outlook", "unknown"), 0.2)
    total = sum(w[k] * sub[k] for k in CRITERIA)
    blockers = []
    if rep["same_url"]:
        blockers.append("already in tracker (same footage URL)")
    if rep["same_event"] and not cand.get("significant_new_development"):
        blockers.append(f"repeat of {', '.join(rep['same_event'])}")
    if sub["recency"] == 0.0 and not cand.get("significant_new_development"):
        blockers.append("too old (more than 7 days since filming/event)")
    if sub["disaster_activity_on_camera"] < 0.3:
        blockers.append("no real disaster impact on camera")
    if sub["verification_confidence"] < 0.5:
        blockers.append("verification confidence too low")
    if cand.get("rights_outlook") == "refused":
        blockers.append("rights holder refused")
    return {**cand, "sub_scores": sub, "score": round(total, 3), "repeat": rep, "blockers": blockers}


def pick_slots(scored: list[dict], n: int = 3) -> list[dict]:
    """Greedy pick by score with diversity: avoid same country or disaster type where possible."""
    th = config.settings()["research"]["min_score_to_recommend"]
    pool = sorted([c for c in scored if not c["blockers"] and c["score"] >= th], key=lambda c: -c["score"])
    picks: list[dict] = []
    for c in pool:
        if len(picks) == n:
            break
        clash = any(p["country"].lower() == c["country"].lower() or p["type"].lower() == c["type"].lower() for p in picks)
        if clash and any(not any(p["country"].lower() == o["country"].lower() or p["type"].lower() == o["type"].lower()
                                 for p in picks) for o in pool if o not in picks and o["score"] >= c["score"] - 0.08):
            continue   # a near-equal, more varied option exists; take that one instead
        picks.append(c)
    for c in pool:   # fill remaining slots if variety alone left gaps
        if len(picks) == n:
            break
        if c not in picks:
            picks.append(c)
    return picks
