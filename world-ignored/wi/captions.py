"""Caption, title and hashtag generation in the World Ignored style.

Captions are assembled only from verified fields on the tracker item:
  event.title / location / country / event_date, event.summary (sourced sentences),
  event.facts [{text, source}] for damage/casualty figures, rights.attribution, event.sources.
Nothing is invented: a missing required field raises CaptionError instead of being guessed, and
damage or casualty figures appear only when they carry a source.
"""
from __future__ import annotations

import re
from datetime import date

LIMITS = {"x": 280, "threads": 500, "tiktok": 2200, "instagram_reels": 2200, "instagram_feed": 2200,
          "facebook_reels": 2200, "facebook_feed": 2200, "linkedin": 3000, "youtube_title": 100,
          "youtube_description": 5000}

EMOJI = {"flood": "🌊", "flash flood": "🌊", "landslide": "⛰️", "mudslide": "⛰️", "earthquake": "🌍",
         "tsunami": "🌊", "wildfire": "🔥", "fire": "🔥", "hurricane": "🌀", "typhoon": "🌀", "cyclone": "🌀",
         "tornado": "🌪️", "storm": "⛈️", "hail": "🧊", "volcano": "🌋", "eruption": "🌋", "avalanche": "🏔️",
         "blizzard": "❄️", "snowstorm": "❄️", "heatwave": "🌡️", "drought": "☀️", "sinkhole": "🕳️", "rescue": "🚁"}

TYPE_TAGS = {"flood": ["#Flooding", "#FlashFlood"], "flash flood": ["#FlashFlood", "#Flooding"],
             "landslide": ["#Landslide"], "mudslide": ["#Mudslide", "#Landslide"], "earthquake": ["#Earthquake"],
             "tsunami": ["#Tsunami"], "wildfire": ["#Wildfire"], "fire": ["#Wildfire"],
             "hurricane": ["#Hurricane"], "typhoon": ["#Typhoon"], "cyclone": ["#Cyclone"],
             "tornado": ["#Tornado"], "storm": ["#Storm", "#SevereWeather"], "hail": ["#Hailstorm"],
             "volcano": ["#Volcano"], "eruption": ["#VolcanicEruption"], "avalanche": ["#Avalanche"],
             "blizzard": ["#Blizzard"], "heatwave": ["#Heatwave"], "sinkhole": ["#Sinkhole"]}

BASE_TAGS = ["#WorldIgnored", "#NaturalDisasters", "#ExtremeWeather"]

# Words that signal casualty/damage claims; such sentences need a source.
_CLAIM = re.compile(r"\b(dead|died|killed|deaths?|fatalit|missing|injured|casualt|evacuat|displaced|destroyed|"
                    r"homes|houses|billion|million|\d)", re.I)


class CaptionError(ValueError):
    pass


def human_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return d.strftime("%B %-d, %Y")


def banner_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return d.strftime("%b %-d, %Y").upper()


def location_line(item: dict) -> str:
    e = item["event"]
    loc = e["location"].strip()
    country = e["country"].strip()
    place = loc if country.lower() in loc.lower() else f"{loc}, {country}"
    return f"{place.upper()}  |  {banner_date(e['event_date'])}"


def _country_tag(country: str) -> str:
    return "#" + re.sub(r"[^A-Za-z0-9ÀÿÜüÖöÇçŞşĞğİı]", "", country.title())


def hashtags(item: dict, n: int = 6) -> list[str]:
    t = item["event"]["type"].lower()
    tags = BASE_TAGS[:1] + TYPE_TAGS.get(t, ["#" + t.title().replace(" ", "")]) + [_country_tag(item["event"]["country"])]
    tags += BASE_TAGS[1:] + item["event"].get("extra_tags", [])
    seen, out = set(), []
    for x in tags:
        if x.lower() not in seen:
            seen.add(x.lower())
            out.append(x)
    return out[:n]


def _require(item: dict) -> None:
    e, r = item["event"], item["rights"]
    missing = [k for k, v in {"event.title": e.get("title"), "event.location": e.get("location"),
                              "event.country": e.get("country"), "event.event_date": e.get("event_date"),
                              "event.summary": e.get("summary"),
                              "rights.attribution": r.get("attribution")}.items() if not v]
    if missing:
        raise CaptionError("missing verified fields: " + ", ".join(missing))
    if not e.get("sources"):
        raise CaptionError("no verification sources on record")
    for sentence in re.split(r"(?<=[.!?])\s+", e["summary"]):
        if _CLAIM.search(sentence) and not e.get("summary_sourced"):
            raise CaptionError(f"summary makes a damage/casualty claim without a source flag: '{sentence[:80]}'")


def _facts(item: dict) -> list[str]:
    return [f["text"].strip() for f in item["event"].get("facts", []) if f.get("text") and f.get("source")]


def _source_names(item: dict, k: int = 3) -> str:
    names = [s.get("name") or s.get("url", "") for s in item["event"]["sources"][:k]]
    return ", ".join(n for n in names if n)


def _emoji(item: dict) -> str:
    t = item["event"]["type"].lower()
    lead = item["event"].get("emoji") or EMOJI.get(t, "⚠️")
    return lead


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    raise CaptionError(f"caption is {len(text)} chars, over the {limit} limit")


def _x_len(text: str) -> int:
    """X counts most emoji and CJK as 2; URLs as 23. Approximate conservatively."""
    n = 0
    for ch in text:
        n += 2 if ord(ch) > 0x2FFF else 1
    return n


def build(item: dict) -> dict:
    _require(item)
    e = item["event"]
    head = e["title"].upper().rstrip(".")
    emoji = _emoji(item)
    place = e["location"] if e["country"].lower() in e["location"].lower() else f"{e['location']}, {e['country']}"
    when = human_date(e["event_date"])
    summary = e["summary"].strip()
    facts = _facts(item)
    credit = item["rights"]["attribution"].strip()
    sources = _source_names(item)
    tags = hashtags(item)

    body = summary + ("\n\n" + "\n".join(facts) if facts else "")
    long_caption = (f"{emoji} {head}\n\n{body}\n\n📍 {place}\n📅 {when}\n\n"
                    f"Footage: {credit}\nSources: {sources}\n\n{' '.join(tags)}")

    first_sentence = re.split(r"(?<=[.!?])\s+", summary)[0]
    tiktok = (f"{emoji} {head}\n\n{first_sentence}\n\n📍 {place} | 📅 {when}\n"
              f"Footage: {credit}\n\n{' '.join(tags[:5])}")

    threads = f"{emoji} {head}\n\n{first_sentence}\n\n📍 {place} · {when}\nFootage: {credit}\n\n{tags[0]}"
    if len(threads) > LIMITS["threads"]:
        threads = f"{emoji} {head}\n\n📍 {place} · {when}\nFootage: {credit}\n\n{tags[0]}"

    # X: no links (they cost extra and hurt reach), short credit, two tags.
    x = f"{emoji} {head}\n\n📍 {place} · {when}\n🎥 {credit}\n\n{tags[0]} {tags[1]}"
    if _x_len(x) > LIMITS["x"]:
        x = f"{emoji} {head}\n📍 {place} · {when}\n🎥 {credit}"
    if _x_len(x) > LIMITS["x"]:
        raise CaptionError("X caption over 280 even in short form; shorten the headline")

    linkedin = (f"{head}\n\n{body}\n\n📍 {place}\n📅 {when}\n\nFootage: {credit}\nSources: {sources}\n\n"
                f"{' '.join(tags[:4])}")

    yt_title = f"{e['title'].strip().rstrip('.')} | {e['location'].split(',')[0].strip()} #Shorts"
    if len(yt_title) > LIMITS["youtube_title"]:
        yt_title = f"{e['title'].strip().rstrip('.')}"[: LIMITS["youtube_title"] - 8].rstrip() + " #Shorts"
    src_lines = "\n".join(f"- {s.get('name','')}: {s.get('url','')}" for s in e["sources"][:5])
    yt_desc = (f"{head}\n\n{body}\n\n📍 {place}\n📅 {when}\n\nFootage: {credit}\nSources:\n{src_lines}\n\n"
               f"World Ignored covers natural disasters around the world.\n\n{' '.join(tags)}")

    caps = {
        "instagram_reels": _clip(long_caption, LIMITS["instagram_reels"]),
        "instagram_feed": _clip(long_caption, LIMITS["instagram_feed"]),
        "facebook_reels": _clip(long_caption, LIMITS["facebook_reels"]),
        "facebook_feed": _clip(long_caption, LIMITS["facebook_feed"]),
        "tiktok": _clip(tiktok, LIMITS["tiktok"]),
        "threads": _clip(threads, LIMITS["threads"]),
        "x": x,
        "linkedin": _clip(linkedin, LIMITS["linkedin"]),
        "youtube_title": yt_title,
        "youtube_description": _clip(yt_desc, LIMITS["youtube_description"]),
    }
    return caps


def banner_texts(item: dict) -> dict:
    ed = item["edit"]
    missing = [k for k in ("headline", "closing_headline", "closing_subhead") if not ed.get(k)]
    if missing:
        raise CaptionError("banner text missing: " + ", ".join(missing))
    return {"headline": ed["headline"], "subhead": ed.get("subhead", ""), "location_line": location_line(item),
            "closing_headline": ed["closing_headline"], "closing_subhead": ed["closing_subhead"]}


# Default closing safety messages by disaster type (reviewers can override per video).
SAFETY = {
    "flood": ("FLOODWATERS CAN DESTROY FOUNDATIONS", "STAY AWAY FROM FLOODED STRUCTURES"),
    "flash flood": ("MOVING FLOODWATER CAN SWEEP CARS AWAY", "AVOID FLOODED ROADS"),
    "landslide": ("SLOPES CAN FAIL WITHOUT WARNING", "EVACUATE WHEN AUTHORITIES ADVISE"),
    "earthquake": ("AFTERSHOCKS CAN TOPPLE DAMAGED BUILDINGS", "STAY OUT OF CRACKED STRUCTURES"),
    "tsunami": ("A TSUNAMI CAN ARRIVE IN MULTIPLE WAVES", "MOVE TO HIGH GROUND AND STAY THERE"),
    "wildfire": ("WILDFIRES CAN SPREAD FASTER THAN YOU CAN RUN", "LEAVE EARLY WHEN TOLD TO EVACUATE"),
    "hurricane": ("STORM SURGE IS THE DEADLIEST HURRICANE HAZARD", "FOLLOW EVACUATION ORDERS"),
    "typhoon": ("STORM SURGE IS THE DEADLIEST TYPHOON HAZARD", "FOLLOW EVACUATION ORDERS"),
    "cyclone": ("STORM SURGE IS THE DEADLIEST CYCLONE HAZARD", "FOLLOW EVACUATION ORDERS"),
    "tornado": ("TORNADO WINDS CAN LIFT VEHICLES", "SHELTER IN AN INTERIOR ROOM, NOT A CAR"),
    "storm": ("FALLING TREES AND POWER LINES KILL IN STORMS", "STAY INDOORS UNTIL IT PASSES"),
    "hail": ("LARGE HAIL CAN CAUSE SERIOUS INJURY", "TAKE COVER INDOORS"),
    "volcano": ("VOLCANIC ASH AND GAS ARE DANGEROUS TO BREATHE", "FOLLOW EXCLUSION ZONE ORDERS"),
    "avalanche": ("AVALANCHES CAN BURY PEOPLE IN SECONDS", "CHECK AVALANCHE WARNINGS BEFORE TRAVEL"),
}


def default_safety(event_type: str) -> tuple[str, str]:
    return SAFETY.get(event_type.lower(), ("DISASTERS CAN ESCALATE QUICKLY", "FOLLOW OFFICIAL WARNINGS"))
