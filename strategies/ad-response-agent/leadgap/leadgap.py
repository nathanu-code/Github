#!/usr/bin/env python3
"""leadgap — a Trojan Horse prospecting tracker for the Ad Response Agent strategy.

The strategy in one line: find businesses that are actively paying for leads,
prove they are dropping those leads on the floor, then sell them the fix.

This tool tracks the proof. You poke a prospect's own funnel the way a real lead
would, log every channel they answer on (or fail to answer on), and the tool
grades the gap and renders a client-ready audit you can open a call with.

Storage is a single SQLite file (default ./leadgap.db, override with --db or
the LEADGAP_DB environment variable). Standard library only.

Run `leadgap.py --help` for the command list, or see ../PLAYBOOK.md.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

# --- Grading thresholds -----------------------------------------------------
# 5 seconds is the bar named in the source reel. It is a rhetorical bar, not an
# operational one -- almost nobody hits it, which is precisely why it is useful
# as a hook. INSTANT is kept as its own tier so an honest audit can say "they
# actually did it" on the rare occasion that a prospect does.
INSTANT_MAX = 5              # seconds
COVERED_MAX = 5 * 60         # 5 minutes -- the real speed-to-lead benchmark
SLOW_MAX = 60 * 60           # 1 hour
GHOST_AFTER = 24 * 60 * 60   # silence past this point is a dead lead

CHANNELS = ("call", "sms", "email", "dm", "other")
CHANNEL_LABELS = {"call": "Call", "sms": "SMS", "email": "Email", "dm": "DM", "other": "Other"}
PROBE_VIAS = ("form", "call", "dm", "chat", "email")

GRADES = {
    "INSTANT": {
        "verdict": "skip",
        "headline": "Answered inside 5 seconds",
        "blurb": "They already solved speed-to-lead. There is no gap to sell. "
                 "Move on and spend the slot on someone bleeding.",
    },
    "COVERED": {
        "verdict": "skip",
        "headline": "Answered inside 5 minutes",
        "blurb": "Fast enough that the money argument does not land. Park them "
                 "and re-probe in 90 days -- staffing changes.",
    },
    "SLOW": {
        "verdict": "warm",
        "headline": "Answered, but slowly",
        "blurb": "They respond, just late enough to lose the buyers who called "
                 "three competitors. Sell the recovered percentage, not the robot.",
    },
    "COLD": {
        "verdict": "hot",
        "headline": "Hours late",
        "blurb": "By the time they called back, the lead had already booked with "
                 "someone else. The waste is concrete and datable.",
    },
    "GHOST": {
        "verdict": "hot",
        "headline": "Never responded at all",
        "blurb": "They paid for the click and never spoke to the human it "
                 "produced. This is the cleanest pitch you will ever get.",
    },
    "PENDING": {
        "verdict": "pending",
        "headline": "Clock still running",
        "blurb": "Probe is live and under 24 hours old. Let it breathe before "
                 "you call -- silence is the asset.",
    },
    "UNTESTED": {
        "verdict": "untested",
        "headline": "No probe run yet",
        "blurb": "You have no evidence. Do not call. Probe first.",
    },
}

VERDICT_ORDER = {"hot": 0, "warm": 1, "pending": 2, "untested": 3, "skip": 4}


# --- Time helpers -----------------------------------------------------------

_RELATIVE = re.compile(r"^([+-]?\d+(?:\.\d+)?)\s*(s|sec|secs|m|min|mins|h|hr|hrs|d|day|days)$", re.I)
_UNIT_SECONDS = {"s": 1, "sec": 1, "secs": 1, "m": 60, "min": 60, "mins": 60,
                 "h": 3600, "hr": 3600, "hrs": 3600, "d": 86400, "day": 86400, "days": 86400}


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_when(value: str | None, *, reference: datetime | None = None) -> datetime:
    """Parse 'now', a relative offset like '-45m', or an ISO 8601 timestamp.

    Naive ISO timestamps are read as local time, which is what you actually
    typed off your phone. Everything is normalised to UTC for storage.
    """
    reference = reference or now_utc()
    if value is None:
        return reference

    text = value.strip()
    if not text or text.lower() == "now":
        return reference

    match = _RELATIVE.match(text)
    if match:
        amount = float(match.group(1))
        seconds = amount * _UNIT_SECONDS[match.group(2).lower()]
        return (reference + timedelta(seconds=seconds)).replace(microsecond=0)

    candidate = text.replace("Z", "+00:00").replace(" ", "T", 1) if " " in text else text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(
            f"could not read time {value!r}. Use 'now', a relative offset "
            f"like '-90m' or '-2h', or an ISO timestamp like '2026-08-16T14:30'."
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def load(stamp: str | None) -> datetime | None:
    return datetime.fromisoformat(stamp).astimezone(timezone.utc) if stamp else None


def local(dt: datetime) -> str:
    """Render a timestamp in the operator's local time -- what goes in the audit."""
    shown = dt.astimezone()
    label = shown.strftime("%Z") or shown.strftime("%z")
    return shown.strftime("%a %b %-d, %Y at %-I:%M %p ") + label


def spoken(dt: datetime) -> str:
    """A timestamp you can say out loud on a call, not read off a receipt."""
    shown = dt.astimezone()
    return shown.strftime("%-I:%M %p on %A")


def humanize(seconds: float | None) -> str:
    if seconds is None:
        return "never"
    seconds = int(round(seconds))
    if seconds < 0:
        return "before the probe"
    if seconds < 60:
        return f"{seconds} sec"
    if seconds < 3600:
        minutes, rest = divmod(seconds, 60)
        return f"{minutes} min" + (f" {rest} sec" if rest and minutes < 5 else "")
    if seconds < 86400:
        hours, rest = divmod(seconds, 3600)
        minutes = rest // 60
        return f"{hours} hr" + (f" {minutes} min" if minutes else "")
    days, rest = divmod(seconds, 86400)
    hours = rest // 3600
    return f"{days} day" + ("s" if days != 1 else "") + (f" {hours} hr" if hours else "")


# --- Grading ----------------------------------------------------------------

def grade_probe(probe: dict, responses: list[dict], *, reference: datetime | None = None) -> dict:
    """Score one probe. Returns grade, verdict, latency and elapsed silence."""
    reference = reference or now_utc()
    probed_at = load(probe["probed_at"])
    horizon = load(probe.get("closed_at")) or reference
    elapsed = max(0.0, (horizon - probed_at).total_seconds())

    replies = sorted(
        (r for r in responses if load(r["received_at"]) >= probed_at),
        key=lambda r: r["received_at"],
    )
    if not replies:
        grade = "GHOST" if elapsed >= GHOST_AFTER else "PENDING"
        return {
            "grade": grade,
            "verdict": GRADES[grade]["verdict"],
            "latency": None,
            "elapsed": elapsed,
            "first_channel": None,
            "channels": [],
        }

    first = replies[0]
    latency = (load(first["received_at"]) - probed_at).total_seconds()
    if latency <= INSTANT_MAX:
        grade = "INSTANT"
    elif latency <= COVERED_MAX:
        grade = "COVERED"
    elif latency <= SLOW_MAX:
        grade = "SLOW"
    else:
        grade = "COLD"
    return {
        "grade": grade,
        "verdict": GRADES[grade]["verdict"],
        "latency": latency,
        "elapsed": elapsed,
        "first_channel": first["channel"],
        "channels": sorted({r["channel"] for r in replies}),
    }


# --- Storage ----------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS prospects (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    niche          TEXT NOT NULL DEFAULT '',
    city           TEXT NOT NULL DEFAULT '',
    phone          TEXT NOT NULL DEFAULT '',
    website        TEXT NOT NULL DEFAULT '',
    ad_library_url TEXT NOT NULL DEFAULT '',
    active_ads     INTEGER NOT NULL DEFAULT 0,
    notes          TEXT NOT NULL DEFAULT '',
    created_at     TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS probes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    prospect_id INTEGER NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    via         TEXT NOT NULL,
    probed_at   TEXT NOT NULL,
    closed_at   TEXT,
    notes       TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS responses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    probe_id    INTEGER NOT NULL REFERENCES probes(id) ON DELETE CASCADE,
    channel     TEXT NOT NULL,
    received_at TEXT NOT NULL,
    notes       TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_probes_prospect ON probes(prospect_id);
CREATE INDEX IF NOT EXISTS idx_responses_probe ON responses(probe_id);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def get_prospect(conn: sqlite3.Connection, prospect_id: int) -> dict:
    row = conn.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,)).fetchone()
    if row is None:
        raise SystemExit(f"error: no prospect with id {prospect_id}. Try `leadgap.py list`.")
    return dict(row)


def latest_probe(conn: sqlite3.Connection, prospect_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM probes WHERE prospect_id = ? ORDER BY probed_at DESC, id DESC LIMIT 1",
        (prospect_id,),
    ).fetchone()
    return dict(row) if row else None


def probe_responses(conn: sqlite3.Connection, probe_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM responses WHERE probe_id = ? ORDER BY received_at, id", (probe_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def assess(conn: sqlite3.Connection, prospect: dict, *, reference: datetime | None = None) -> dict:
    """Full picture for one prospect: newest probe, its responses, its grade."""
    probe = latest_probe(conn, prospect["id"])
    if probe is None:
        return {
            "prospect": prospect, "probe": None, "responses": [],
            "grade": "UNTESTED", "verdict": "untested",
            "latency": None, "elapsed": None, "first_channel": None, "channels": [],
        }
    responses = probe_responses(conn, probe["id"])
    scored = grade_probe(probe, responses, reference=reference)
    return {"prospect": prospect, "probe": probe, "responses": responses, **scored}


# --- Rendering --------------------------------------------------------------

def gap_sentence(row: dict) -> str:
    """The one line you say out loud on the call."""
    name = row["prospect"]["name"]
    if row["grade"] == "UNTESTED":
        return f"{name} has not been probed yet."
    when = local(load(row["probe"]["probed_at"]))
    if row["latency"] is None:
        if row["grade"] == "GHOST":
            return (f"An inquiry was submitted to {name} on {when}. "
                    f"{humanize(row['elapsed'])} later, nobody had called, texted, or emailed.")
        return (f"An inquiry was submitted to {name} on {when}. "
                f"{humanize(row['elapsed'])} in, still no response -- clock is running.")
    return (f"An inquiry was submitted to {name} on {when}. "
            f"The first response came by {CHANNEL_LABELS[row['first_channel']]} "
            f"{humanize(row['latency'])} later.")


def render_report(row: dict) -> str:
    """A client-ready speed-to-lead audit in markdown. This is the door opener."""
    p = row["prospect"]
    grade = GRADES[row["grade"]]
    lines: list[str] = []
    subtitle = " · ".join(x for x in (p["city"], p["niche"]) if x)

    lines.append(f"# Speed-to-Lead Audit — {p['name']}")
    if subtitle:
        lines.append(f"_{subtitle}_")
    lines.append("")
    lines.append(f"**Finding: {grade['headline']}.**")
    lines.append("")

    if row["probe"] is None:
        lines.append("No probe has been run against this business yet, so there is nothing to")
        lines.append("show them. Run `leadgap.py probe` first — the audit *is* the pitch.")
        return "\n".join(lines) + "\n"

    probed_at = load(row["probe"]["probed_at"])
    lines.append("## What we did")
    lines.append("")
    lines.append(
        f"On **{local(probed_at)}** we submitted an inquiry through your "
        f"{row['probe']['via']} — the same path any prospect takes after clicking one of your ads."
    )
    if p["active_ads"]:
        lines.append("")
        lines.append(
            f"At the time of the test you had **{p['active_ads']} active ad"
            f"{'s' if p['active_ads'] != 1 else ''}** running on Meta"
            + (f" ([ad library]({p['ad_library_url']}))" if p["ad_library_url"] else "")
            + ". Every one of them points at the intake we tested."
        )
    lines.append("")

    lines.append("## What happened")
    lines.append("")
    lines.append("| Channel | First response | Time to respond |")
    lines.append("| --- | --- | --- |")
    seen = {}
    for r in row["responses"]:
        seen.setdefault(r["channel"], r)
    for channel in CHANNELS:
        hit = seen.get(channel)
        label = CHANNEL_LABELS[channel]
        if hit:
            delta = (load(hit["received_at"]) - probed_at).total_seconds()
            lines.append(f"| {label} | {local(load(hit['received_at']))} | {humanize(delta)} |")
        elif channel != "other":
            lines.append(f"| {label} | — | no response in {humanize(row['elapsed'])} |")
    lines.append("")

    lines.append("## What it cost")
    lines.append("")
    if row["latency"] is None:
        lines.append(
            "You paid for the click. A real person raised their hand, gave you their "
            f"number, and waited. {humanize(row['elapsed'])} later they had still not heard "
            "from anyone. That lead did not disappear — they called a competitor."
        )
    else:
        lines.append(
            f"You paid for the click and you did respond — {humanize(row['latency'])} later. "
            "Industry response-time research consistently finds that contact and "
            "qualification rates fall off sharply after the first few minutes, so a "
            f"{humanize(row['latency'])} delay is not a small penalty on the ad spend that "
            "produced the lead."
        )
    lines.append("")
    lines.append(f"_{grade['blurb']}_")
    lines.append("")

    lines.append("## The fix")
    lines.append("")
    lines.append(
        "An **ad response agent** sits on the intake you already have. When a form is "
        "submitted or a call is missed, it responds in seconds — by text first, because "
        "text gets answered — qualifies the lead, and books it into your calendar. It does "
        "not replace your front desk. It covers the window your front desk cannot: nights, "
        "weekends, and the ninety seconds while someone is already on the other line."
    )
    lines.append("")
    lines.append("---")
    lines.append(f"_Audit generated {local(now_utc())} · leadgap_")
    return "\n".join(lines) + "\n"


def render_script(row: dict) -> str:
    """The call script, with this prospect's evidence already filled in."""
    p = row["prospect"]
    proof = gap_sentence(row)
    gap_time = humanize(row["elapsed"] if row["latency"] is None else row["latency"])
    ads = (f"{p['active_ads']} ads" if p["active_ads"] else "ads")

    return f"""CALL SCRIPT — {p['name']}{' · ' + p['phone'] if p['phone'] else ''}
{'=' * 68}

VERDICT: {row['verdict'].upper()} ({row['grade']}) — {GRADES[row['grade']]['headline']}
EVIDENCE: {proof}

--- OPEN (do not pitch, report a finding) -------------------------------
"Hi, is this the owner? Great — my name's ___. I'll be quick and this
 isn't really a sales call yet. I saw you're running {ads} for
 {p['niche'] or 'your business'}{' in ' + p['city'] if p['city'] else ''}, so I filled out your form to see what
 happens on the other side. Nobody got back to me for {gap_time}.
 I wanted to check whether that's normal or whether I just caught you
 on a bad day."

--- THEN SHUT UP --------------------------------------------------------
Let them explain. They will either (a) get defensive, (b) admit it, or
(c) blame a staff member. All three open the same door.

--- BRIDGE --------------------------------------------------------------
"That's what I figured. Here's why I called: you're already paying for
 those clicks. The leads are showing up. The only thing broken is the
 first ninety seconds. I put in an ad response agent that texts them back
 in about five seconds and books the ones worth booking. It doesn't touch
 anything else you've got running."

--- OBJECTION: "We're not interested." ----------------------------------
Source version (aggressive, high risk of ending the call):
  "So you're not interested in making more money automatically, on
   autopilot, for your business? Help me understand that."

Recommended version (same reframe, keeps them talking):
  "Fair enough. Can I ask one thing before I go — is it that the timing's
   bad, or that you don't think the missed ones are worth chasing? I ask
   because I've got the timestamp on mine and I'd rather be wrong out loud."

--- OBJECTION: "We already have someone who handles that." --------------
  "Totally — and I'm not trying to replace them. They just weren't there at
   {spoken(load(row['probe']['probed_at'])) if row['probe'] else 'the time I tested'}. Nobody can be. That's the only gap I'm filling."

--- OBJECTION: "How much?" ----------------------------------------------
  Do not quote on this call. "Depends on volume — how many form fills or
   calls a week are you getting off those ads right now?" That question
   prices the deal and qualifies them in one move.

--- CLOSE ---------------------------------------------------------------
  "Let me send you the two-minute version of what I found — timestamps and
   all. If it looks off, tell me and I'll drop it. What's the best email?"
"""


# --- Commands ---------------------------------------------------------------

def cmd_add(conn, args) -> int:
    cur = conn.execute(
        """INSERT INTO prospects (name, niche, city, phone, website, ad_library_url,
                                  active_ads, notes, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (args.name, args.niche, args.city, args.phone, args.website,
         args.ad_library_url, args.active_ads, args.notes, iso(now_utc())),
    )
    conn.commit()
    print(f"added #{cur.lastrowid}  {args.name}")
    print("next: run the probe, then wait. `leadgap.py probe %d --via form`" % cur.lastrowid)
    return 0


def cmd_probe(conn, args) -> int:
    prospect = get_prospect(conn, args.prospect_id)
    when = parse_when(args.at)
    cur = conn.execute(
        "INSERT INTO probes (prospect_id, via, probed_at, notes) VALUES (?, ?, ?, ?)",
        (prospect["id"], args.via, iso(when), args.notes),
    )
    conn.commit()
    print(f"probe #{cur.lastrowid} started on {prospect['name']} via {args.via}")
    print(f"clock started {local(when)}")
    print("reminder: reach their funnel organically. Clicking their paid ad to run")
    print("this test bills them for your own audit, and they will notice.")
    return 0


def cmd_respond(conn, args) -> int:
    prospect = get_prospect(conn, args.prospect_id)
    probe = latest_probe(conn, prospect["id"])
    if probe is None:
        raise SystemExit(f"error: {prospect['name']} has no probe yet. Run `probe` first.")
    if args.probe:
        row = conn.execute(
            "SELECT * FROM probes WHERE id = ? AND prospect_id = ?", (args.probe, prospect["id"])
        ).fetchone()
        if row is None:
            raise SystemExit(f"error: probe {args.probe} does not belong to {prospect['name']}.")
        probe = dict(row)

    when = parse_when(args.at)
    probed_at = load(probe["probed_at"])
    if when < probed_at:
        raise SystemExit(
            f"error: response at {local(when)} predates the probe at {local(probed_at)}."
        )
    conn.execute(
        "INSERT INTO responses (probe_id, channel, received_at, notes) VALUES (?, ?, ?, ?)",
        (probe["id"], args.channel, iso(when), args.notes),
    )
    conn.commit()
    delta = (when - probed_at).total_seconds()
    print(f"logged {args.channel} response after {humanize(delta)}")
    print_verdict(assess(conn, prospect))
    return 0


def cmd_close(conn, args) -> int:
    prospect = get_prospect(conn, args.prospect_id)
    probe = latest_probe(conn, prospect["id"])
    if probe is None:
        raise SystemExit(f"error: {prospect['name']} has no probe to close.")
    when = parse_when(args.at)
    conn.execute("UPDATE probes SET closed_at = ? WHERE id = ?", (iso(when), probe["id"]))
    conn.commit()
    print(f"probe #{probe['id']} closed at {local(when)} — grade is now frozen")
    print_verdict(assess(conn, prospect))
    return 0


def print_verdict(row: dict) -> None:
    grade = GRADES[row["grade"]]
    print(f"  {row['prospect']['name']}: {row['verdict'].upper()} / {row['grade']} — {grade['headline']}")
    print(f"  {gap_sentence(row)}")


def cmd_show(conn, args) -> int:
    row = assess(conn, get_prospect(conn, args.prospect_id))
    if args.json:
        print(json.dumps(serialize(row), indent=2))
        return 0
    p = row["prospect"]
    print(f"#{p['id']}  {p['name']}")
    for label, key in (("niche", "niche"), ("city", "city"), ("phone", "phone"),
                       ("website", "website"), ("ads", "active_ads"),
                       ("ad library", "ad_library_url"), ("notes", "notes")):
        if p[key]:
            print(f"  {label:<11} {p[key]}")
    print()
    print_verdict(row)
    if row["probe"]:
        print(f"\n  probe #{row['probe']['id']} via {row['probe']['via']}, "
              f"started {local(load(row['probe']['probed_at']))}")
        if row["probe"]["closed_at"]:
            print(f"  closed {local(load(row['probe']['closed_at']))}")
        if row["responses"]:
            print("  responses:")
            for r in row["responses"]:
                delta = (load(r["received_at"]) - load(row["probe"]["probed_at"])).total_seconds()
                note = f"  ({r['notes']})" if r["notes"] else ""
                print(f"    {CHANNEL_LABELS[r['channel']]:<6} +{humanize(delta)}{note}")
        else:
            print("  responses: none")
    print(f"\n  {GRADES[row['grade']]['blurb']}")
    return 0


def collect(conn, *, verdict=None, niche=None, city=None, reference=None) -> list[dict]:
    rows = [assess(conn, dict(p), reference=reference)
            for p in conn.execute("SELECT * FROM prospects ORDER BY id").fetchall()]
    if verdict:
        rows = [r for r in rows if r["verdict"] == verdict]
    if niche:
        rows = [r for r in rows if niche.lower() in r["prospect"]["niche"].lower()]
    if city:
        rows = [r for r in rows if city.lower() in r["prospect"]["city"].lower()]
    rows.sort(key=lambda r: (VERDICT_ORDER[r["verdict"]], -(r["elapsed"] or 0)))
    return rows


def serialize(row: dict) -> dict:
    return {
        "id": row["prospect"]["id"],
        "name": row["prospect"]["name"],
        "niche": row["prospect"]["niche"],
        "city": row["prospect"]["city"],
        "phone": row["prospect"]["phone"],
        "active_ads": row["prospect"]["active_ads"],
        "grade": row["grade"],
        "verdict": row["verdict"],
        "latency_seconds": row["latency"],
        "elapsed_seconds": row["elapsed"],
        "first_channel": row["first_channel"],
        "responded_on": row["channels"],
        "probed_at": row["probe"]["probed_at"] if row["probe"] else None,
        "evidence": gap_sentence(row),
    }


def cmd_list(conn, args) -> int:
    rows = collect(conn, verdict=args.verdict, niche=args.niche, city=args.city)
    if args.json:
        print(json.dumps([serialize(r) for r in rows], indent=2))
        return 0
    if not rows:
        print("no prospects match. `leadgap.py add --name ...` to start.")
        return 0
    print(f"{'ID':<4} {'VERDICT':<9} {'GRADE':<8} {'GAP':<14} {'ADS':<4} NAME")
    for row in rows:
        gap = humanize(row["elapsed"] if row["latency"] is None else row["latency"]) \
            if row["probe"] else "-"
        print(f"{row['prospect']['id']:<4} {row['verdict'].upper():<9} {row['grade']:<8} "
              f"{gap:<14} {row['prospect']['active_ads'] or '-':<4} {row['prospect']['name']}")
    return 0


def cmd_stats(conn, args) -> int:
    rows = collect(conn)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    tested = [r for r in rows if r["probe"]]
    hot = counts.get("hot", 0)
    payload = {
        "prospects": len(rows),
        "probed": len(tested),
        "by_verdict": counts,
        "hot_rate": round(hot / len(tested), 3) if tested else None,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0
    print(f"prospects   {payload['prospects']}")
    print(f"probed      {payload['probed']}")
    for verdict in sorted(counts, key=lambda v: VERDICT_ORDER[v]):
        print(f"  {verdict:<9} {counts[verdict]}")
    if payload["hot_rate"] is not None:
        print(f"hot rate    {payload['hot_rate']:.0%} of probed prospects have a sellable gap")
    return 0


def cmd_report(conn, args) -> int:
    row = assess(conn, get_prospect(conn, args.prospect_id))
    text = render_report(row)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(text)
    return 0


def cmd_script(conn, args) -> int:
    row = assess(conn, get_prospect(conn, args.prospect_id))
    if row["grade"] == "UNTESTED":
        raise SystemExit(
            f"error: {row['prospect']['name']} has no probe. The script is built out of the "
            "evidence — without it you are just another cold caller. Run `probe` first."
        )
    sys.stdout.write(render_script(row))
    return 0


def cmd_export(conn, args) -> int:
    rows = [serialize(r) for r in collect(conn)]
    if args.format == "json":
        print(json.dumps(rows, indent=2))
        return 0
    buf = io.StringIO()
    fields = ["id", "name", "niche", "city", "phone", "active_ads", "grade", "verdict",
              "latency_seconds", "elapsed_seconds", "first_channel", "probed_at", "evidence"]
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    sys.stdout.write(buf.getvalue())
    return 0


# --- CLI --------------------------------------------------------------------

_TIME_FLAGS = ("--at",)


def normalize_argv(argv: list[str]) -> list[str]:
    """Glue relative times onto their flag: argparse reads '-48h' as an option.

    Typing `--at -48h` is the natural thing to do, so accept it rather than
    forcing `--at=-48h` on anyone.
    """
    out: list[str] = []
    skip = False
    for index, token in enumerate(argv):
        if skip:
            skip = False
            continue
        following = argv[index + 1] if index + 1 < len(argv) else None
        if token in _TIME_FLAGS and following and following.startswith("-") and following != "-":
            out.append(f"{token}={following}")
            skip = True
        else:
            out.append(token)
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="leadgap",
        description="Trojan Horse prospecting tracker for the Ad Response Agent strategy.",
        epilog="Find who is paying for leads, prove they are dropping them, sell the fix.",
    )
    parser.add_argument("--db", default=os.environ.get("LEADGAP_DB", "leadgap.db"),
                        help="SQLite database path (default: ./leadgap.db or $LEADGAP_DB)")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a prospect pulled from the Meta Ad Library")
    add.add_argument("--name", required=True)
    add.add_argument("--niche", default="", help="e.g. 'med spa', 'roofing'")
    add.add_argument("--city", default="")
    add.add_argument("--phone", default="")
    add.add_argument("--website", default="")
    add.add_argument("--ad-library-url", dest="ad_library_url", default="")
    add.add_argument("--active-ads", dest="active_ads", type=int, default=0,
                     help="how many ads they are running right now — this is the budget proof")
    add.add_argument("--notes", default="")
    add.set_defaults(func=cmd_add)

    probe = sub.add_parser("probe", help="start the clock: you just poked their funnel")
    probe.add_argument("prospect_id", type=int)
    probe.add_argument("--via", choices=PROBE_VIAS, default="form")
    probe.add_argument("--at", default="now", help="'now', '-45m', or an ISO timestamp")
    probe.add_argument("--notes", default="")
    probe.set_defaults(func=cmd_probe)

    respond = sub.add_parser("respond", help="log a response they sent you")
    respond.add_argument("prospect_id", type=int)
    respond.add_argument("--channel", choices=CHANNELS, required=True)
    respond.add_argument("--at", default="now")
    respond.add_argument("--probe", type=int, help="target an older probe instead of the newest")
    respond.add_argument("--notes", default="")
    respond.set_defaults(func=cmd_respond)

    close = sub.add_parser("close", help="stop the clock and freeze the grade")
    close.add_argument("prospect_id", type=int)
    close.add_argument("--at", default="now")
    close.set_defaults(func=cmd_close)

    show = sub.add_parser("show", help="everything known about one prospect")
    show.add_argument("prospect_id", type=int)
    show.add_argument("--json", action="store_true")
    show.set_defaults(func=cmd_show)

    listing = sub.add_parser("list", help="the pipeline, hottest first")
    listing.add_argument("--verdict", choices=sorted(VERDICT_ORDER))
    listing.add_argument("--niche")
    listing.add_argument("--city")
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(func=cmd_list)

    stats = sub.add_parser("stats", help="pipeline counts and hot rate")
    stats.add_argument("--json", action="store_true")
    stats.set_defaults(func=cmd_stats)

    report = sub.add_parser("report", help="render the client-ready audit")
    report.add_argument("prospect_id", type=int)
    report.add_argument("--out", help="write to a file instead of stdout")
    report.set_defaults(func=cmd_report)

    script = sub.add_parser("script", help="render the call script with their evidence in it")
    script.add_argument("prospect_id", type=int)
    script.set_defaults(func=cmd_script)

    export = sub.add_parser("export", help="dump the pipeline")
    export.add_argument("--format", choices=("csv", "json"), default="csv")
    export.set_defaults(func=cmd_export)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(normalize_argv(list(argv if argv is not None else sys.argv[1:])))
    conn = connect(args.db)
    try:
        return args.func(conn, args)
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from exc
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
