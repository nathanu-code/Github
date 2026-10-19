"""Authoritative disaster feeds used to discover events and to verify that a claimed event happened.

  USGS   earthquakes (M5+), public domain             https://earthquake.usgs.gov
  GDACS  floods, cyclones, quakes, volcanoes, fires   https://www.gdacs.org (public domain RSS)
  EONET  NASA natural events (storms, fires, volcanoes)
  GDELT  global news article index (for news coverage + footage leads)

Every function returns normalised event dicts:
  {feed, type, title, country, location, lat, lon, date, url, severity, id}
"""
from __future__ import annotations

import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import requests

UA = {"User-Agent": "WorldIgnoredResearch/1.0 (contact: admin@grandeurdesignsupply.com)"}
TIMEOUT = 25

GDACS_TYPES = {"EQ": "earthquake", "TC": "cyclone", "FL": "flood", "VO": "volcano", "WF": "wildfire", "DR": "drought"}
EONET_TYPES = {"severeStorms": "storm", "wildfires": "wildfire", "volcanoes": "volcano", "floods": "flood",
               "landslides": "landslide", "earthquakes": "earthquake", "snow": "blizzard"}


def _get(url: str, **kw) -> requests.Response:
    r = requests.get(url, headers=UA, timeout=TIMEOUT, **kw)
    r.raise_for_status()
    return r


def usgs(hours: int = 72, min_mag: float = 5.0) -> list[dict]:
    feed = "4.5_week" if hours > 24 else "4.5_day"
    data = _get(f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{feed}.geojson").json()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    out = []
    for f in data["features"]:
        p = f["properties"]
        t = datetime.fromtimestamp(p["time"] / 1000, timezone.utc)
        if t < cutoff or (p.get("mag") or 0) < min_mag:
            continue
        place = p.get("place") or ""
        country = place.split(",")[-1].strip() if "," in place else place
        lon, lat, _ = f["geometry"]["coordinates"]
        out.append({"feed": "USGS", "id": f["id"], "type": "earthquake", "title": p["title"], "country": country,
                    "location": place, "lat": lat, "lon": lon, "date": t.date().isoformat(), "url": p["url"],
                    "severity": {"magnitude": p.get("mag"), "alert": p.get("alert"), "tsunami": p.get("tsunami"),
                                 "felt": p.get("felt")}})
    return out


def gdacs(hours: int = 72) -> list[dict]:
    xml = _get("https://www.gdacs.org/xml/rss.xml").content
    ns = {"gdacs": "http://www.gdacs.org", "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#"}
    root = ET.fromstring(xml)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    out = []
    for it in root.iter("item"):
        def g(tag):
            el = it.find(tag, ns)
            return el.text if el is not None else None
        try:
            to = parsedate_to_datetime(g("gdacs:todate") or g("pubDate"))
        except (TypeError, ValueError):
            continue
        if to < cutoff:
            continue
        etype = GDACS_TYPES.get(g("gdacs:eventtype") or "", (g("gdacs:eventtype") or "").lower())
        out.append({"feed": "GDACS", "id": f"{g('gdacs:eventtype')}{g('gdacs:eventid')}", "type": etype,
                    "title": g("title"), "country": g("gdacs:country") or "", "location": g("gdacs:country") or "",
                    "lat": float(g("geo:Point/geo:lat") or 0), "lon": float(g("geo:Point/geo:long") or 0),
                    "date": parsedate_to_datetime(g("gdacs:fromdate") or g("pubDate")).date().isoformat(),
                    "url": g("link"), "severity": {"alert": g("gdacs:alertlevel"), "score": g("gdacs:alertscore"),
                                                    "population": g("gdacs:population")}})
    return out


def eonet(days: int = 3) -> list[dict]:
    data = _get(f"https://eonet.gsfc.nasa.gov/api/v3/events?status=all&days={days}").json()
    out = []
    for e in data["events"]:
        cat = e["categories"][0]["id"] if e["categories"] else ""
        geo = e["geometry"][-1] if e["geometry"] else {}
        coords = geo.get("coordinates") or [0, 0]
        if isinstance(coords[0], list):
            coords = coords[0][0] if isinstance(coords[0][0], list) else coords[0]
        out.append({"feed": "EONET", "id": e["id"], "type": EONET_TYPES.get(cat, cat), "title": e["title"],
                    "country": "", "location": e["title"], "lat": coords[1], "lon": coords[0],
                    "date": (geo.get("date") or "")[:10], "url": e["link"],
                    "severity": {"magnitude": geo.get("magnitudeValue"), "unit": geo.get("magnitudeUnit")},
                    "sources": [s["url"] for s in e.get("sources", [])]})
    return out


DEFAULT_NEWS_QUERIES = [
    '(flood OR "flash flood") (video OR footage) (swept OR collapse OR rescue)',
    "(landslide OR mudslide) (video OR footage)",
    '(tornado OR hurricane OR typhoon OR cyclone) (video OR footage) damage',
    "(wildfire OR bushfire) (video OR footage) homes",
    "earthquake (video OR footage) collapse",
]


def gdelt(query: str, hours: int = 48, limit: int = 25) -> list[dict]:
    q = quote(f"{query} sourcelang:english")
    url = (f"https://api.gdeltproject.org/api/v2/doc/doc?query={q}&mode=artlist&format=json"
           f"&timespan={hours}h&maxrecords={limit}&sort=datedesc")
    r = _get(url)
    try:
        arts = r.json().get("articles", [])
    except json.JSONDecodeError:   # GDELT returns plain-text errors for bad queries
        return []
    return [{"feed": "GDELT", "id": a["url"], "type": "news", "title": a["title"], "country": a.get("sourcecountry", ""),
             "location": "", "lat": None, "lon": None, "date": a["seendate"][:8], "url": a["url"],
             "severity": {}, "domain": a.get("domain")} for a in arts]


def collect(hours: int = 72) -> dict:
    """Run all feeds; a failing feed is reported, not fatal."""
    result, errors = {"events": [], "news": []}, []
    for name, fn in (("USGS", lambda: usgs(hours)), ("GDACS", lambda: gdacs(hours)), ("EONET", lambda: eonet(max(1, hours // 24)))):
        try:
            result["events"] += fn()
        except Exception as exc:  # noqa: BLE001 - feed outages are expected and reported
            errors.append(f"{name}: {exc.__class__.__name__}: {str(exc)[:120]}")
    for i, q in enumerate(DEFAULT_NEWS_QUERIES):
        if i:
            time.sleep(6)   # GDELT allows one request per 5 seconds
        try:
            result["news"] += gdelt(q, min(hours, 72))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"GDELT: {exc.__class__.__name__}: {str(exc)[:120]}")
    seen, news = set(), []
    for n in result["news"]:
        key = re.sub(r"\W+", "", n["title"].lower())[:60]
        if key not in seen:
            seen.add(key)
            news.append(n)
    result["news"] = news
    result["errors"] = errors
    result["collected_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return result


def corroborate(event_type: str, country: str, date_iso: str, events: list[dict], days: int = 2) -> list[dict]:
    """Feed events that match a claimed disaster (same type family, country, +/- days)."""
    fam = {"flash flood": "flood", "mudslide": "landslide", "typhoon": "cyclone", "hurricane": "cyclone", "fire": "wildfire"}
    want = fam.get(event_type.lower(), event_type.lower())
    d0 = datetime.fromisoformat(date_iso).date()
    hits = []
    for e in events:
        et = fam.get(e["type"], e["type"])
        if et != want:
            continue
        if country and country.lower() not in (e.get("country", "") + " " + e.get("location", "") + " " + e.get("title", "")).lower():
            continue
        try:
            ed = datetime.fromisoformat(e["date"]).date()
        except ValueError:
            continue
        if abs((ed - d0).days) <= days:
            hits.append(e)
    return hits
