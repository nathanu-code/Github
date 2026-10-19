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

# Hazard hashtags, then the matching safety hashtag (house style: #FlashFlood #FloodSafety).
TYPE_TAGS = {"flood": ["#Flooding", "#FloodSafety"], "flash flood": ["#FlashFlood", "#FloodSafety"],
             "landslide": ["#Landslide", "#LandslideSafety"], "mudslide": ["#Mudslide", "#LandslideSafety"],
             "earthquake": ["#Earthquake", "#EarthquakeSafety"], "tsunami": ["#Tsunami", "#TsunamiSafety"],
             "wildfire": ["#Wildfire", "#WildfireSafety"], "fire": ["#Fire", "#FireSafety"],
             "hurricane": ["#Hurricane", "#HurricaneSafety"], "typhoon": ["#Typhoon", "#TyphoonSafety"],
             "cyclone": ["#Cyclone", "#StormSafety"], "tornado": ["#Tornado", "#TornadoSafety"],
             "storm": ["#Storm", "#StormSafety"], "hail": ["#Hailstorm", "#StormSafety"],
             "volcano": ["#Volcano", "#VolcanoSafety"], "eruption": ["#VolcanicEruption", "#VolcanoSafety"],
             "avalanche": ["#Avalanche", "#AvalancheSafety"], "blizzard": ["#Blizzard", "#WinterSafety"],
             "heatwave": ["#Heatwave", "#HeatSafety"], "sinkhole": ["#Sinkhole", "#DisasterSafety"]}

BRAND_TAG = "#WorldUnignored"   # as used on the posted captions (Sep 2026)
PREP_TAG = "#DisasterPreparedness"
AUTHORITIES_LINE = "Follow instructions from local authorities during an active emergency."

# Caption safety advice (sentence case). Reviewers can override per video with edit.caption_safety.
CAPTION_SAFETY = {
    "flood": "Move to higher ground when told to evacuate. Stay away from riverbanks and never enter floodwater.",
    "flash flood": "Never drive or walk into floodwater; just a few inches of moving water can sweep a car away. "
                   "Move to higher ground and stay away from riverbanks.",
    "landslide": "Leave slopes and valleys when authorities advise. Listen for unusual rumbling and stay away from the slide area.",
    "mudslide": "Leave slopes and valleys when authorities advise. Listen for unusual rumbling and stay away from the slide area.",
    "earthquake": "During shaking: Drop • Cover • Hold On. Stay out of damaged buildings after the shaking stops.",
    "tsunami": "If the ground shakes near the coast or the sea pulls back, move to high ground immediately and stay there.",
    "wildfire": "Leave early when told to evacuate. Don't wait to see the flames.",
    "fire": "If you see a building fire, move away from smoke, use the nearest safe exit, and call emergency services.",
    "hurricane": "Follow evacuation orders. Storm surge and flooding cause most hurricane deaths.",
    "typhoon": "Follow evacuation orders. Storm surge and flooding cause most typhoon deaths.",
    "cyclone": "Follow evacuation orders. Storm surge and flooding cause most cyclone deaths.",
    "tornado": "Shelter in an interior room on the lowest floor, away from windows. A car is not a safe shelter.",
    "storm": "Stay indoors until the storm passes and keep away from fallen trees and power lines.",
    "hail": "Take cover indoors and stay away from windows until the hail stops.",
    "volcano": "Respect volcanic exclusion zones and evacuation orders. Never enter a restricted crater area.",
    "eruption": "Respect volcanic exclusion zones and evacuation orders. Never enter a restricted crater area.",
    "avalanche": "Check avalanche warnings before heading into the mountains and avoid closed slopes.",
}


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


def _place_tag(location: str) -> str:
    first = location.split(",")[0]
    return "#" + re.sub(r"[^A-Za-z0-9ÀÿÜüÖöÇçŞşĞğİı]", "", first.title())


def hashtags(item: dict, n: int = 6) -> list[str]:
    """House order: #Country #Place #Hazard #HazardSafety #DisasterPreparedness #WorldUnignored."""
    e = item["event"]
    t = e["type"].lower()
    hazard = TYPE_TAGS.get(t, ["#" + t.title().replace(" ", ""), "#DisasterSafety"])
    tags = [_country_tag(e["country"]), _place_tag(e["location"])] + hazard + e.get("extra_tags", []) + [PREP_TAG]
    seen, out = set(), []
    for x in tags:
        if x.lower() not in seen:
            seen.add(x.lower())
            out.append(x)
    return out[: n - 1] + [BRAND_TAG]


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


def _fact_sources(item: dict, k: int = 2, links: bool = True) -> str:
    srcs = [s for s in item["event"]["sources"][:k] if s.get("name") or s.get("url")]
    parts = [f"{s.get('name') or s['url']} — {s['url']}" if links and s.get("url") and s.get("name")
             else (s.get("name") or s["url"]) for s in srcs]
    label = "Fact source" if len(parts) == 1 else "Fact sources"
    return f"{label}: " + " ; ".join(parts)


def caption_safety(item: dict) -> str:
    return (item["edit"].get("caption_safety")
            or CAPTION_SAFETY.get(item["event"]["type"].lower(), "Follow official warnings and evacuation orders."))


def _dated_lead(summary: str, when: str) -> str:
    """House captions open with the date: "On 19 October 2026, a flash flood ..."."""
    if summary.lower().startswith("on ") or when in summary:
        return summary
    first, _, rest = summary.partition(" ")
    if first in ("The", "A", "An"):
        return f"On {when}, {first.lower()} {rest}"
    return summary


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
    """Captions in the house style taken from the posted World Ignored captions:

    HEADLINE (uppercase, no emoji)
    On <date>, <what happened, from the sourced summary and facts>
    📍 <place>
    <safety advice>
    Follow instructions from local authorities during an active emergency.
    🎥 <filmer / credit>
    Fact source: <name> — <url>
    #Country #Place #Hazard #HazardSafety #DisasterPreparedness #WorldUnignored
    """
    _require(item)
    e = item["event"]
    head = (item["edit"].get("headline") or e["title"]).upper().rstrip(".")
    place = e["location"] if e["country"].lower() in e["location"].lower() else f"{e['location']}, {e['country']}"
    when = human_date(e["event_date"])
    lead = _dated_lead(e["summary"].strip(), when)
    dated = when in lead
    place_line = f"📍 {place}" + ("" if dated else f" · {when}")
    body = " ".join([lead] + _facts(item))
    safety = caption_safety(item)
    credit = item["rights"]["attribution"].strip()
    credit_line = f"🎥 {credit}"
    tags = hashtags(item)

    long_caption = (f"{head}\n\n{body}\n\n{place_line}\n{safety}\n{AUTHORITIES_LINE}\n\n"
                    f"{credit_line}\n{_fact_sources(item)}\n\n{' '.join(tags)}")

    # TikTok and Threads: links aren't clickable or hurt reach, so sources are named without URLs.
    tiktok = (f"{head}\n\n{lead}\n\n{place_line}\n{safety}\n\n{credit_line}\n"
              f"{_fact_sources(item, links=False)}\n\n{' '.join(tags[:4] + tags[-1:])}")

    threads = f"{head}\n\n{lead}\n\n{place_line}\n{safety}\n\n{credit_line}\n\n{tags[-1]}"
    if len(threads) > LIMITS["threads"]:
        threads = f"{head}\n\n{place_line}\n{safety}\n\n{credit_line}\n\n{tags[-1]}"

    # X: no links (they cost extra and hurt reach), one safety hashtag. Shrinks until it fits.
    first_safety = re.split(r"(?<=[.!?;])\s+", safety)[0].rstrip(";.") + "."
    hazard_safety = tags[3] if len(tags) > 3 else tags[-1]
    x_forms = [f"{head}\n\n{lead}\n\n{place_line}\n{safety}\n🎥 {credit}\n\n{hazard_safety}",
               f"{head}\n\n{place_line}\n{safety}\n🎥 {credit}\n\n{hazard_safety}",
               f"{head}\n\n{place_line}\n{first_safety}\n🎥 {credit}\n\n{hazard_safety}",
               f"{head}\n{place_line}\n🎥 {credit}"]
    x = next((f for f in x_forms if _x_len(f) <= LIMITS["x"]), None)
    if x is None:
        raise CaptionError("X caption over 280 even in short form; shorten the headline")

    linkedin = (f"{head}\n\n{body}\n\n{place_line}\n\nPreparedness matters when seconds count. {safety}\n"
                f"{AUTHORITIES_LINE}\n\n{credit_line}\n{_fact_sources(item)}\n\n{' '.join(tags[2:])}")

    title = (e.get("youtube_title") or e["title"]).strip().rstrip(".")
    title = title if title != title.upper() else title.title()
    yt_title = f"{title} | {e['location'].split(',')[0].strip()}"
    if len(yt_title) > LIMITS["youtube_title"] - 8:
        yt_title = title[: LIMITS["youtube_title"] - 8].rstrip()
    yt_title += " #Shorts"
    yt_desc = (f"{body}\n\n{place_line}\n{safety}\n{AUTHORITIES_LINE}\n\n{credit_line}\n{_fact_sources(item, k=5)}\n\n"
               f"{' '.join(tags + ['#Shorts'])}")

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
