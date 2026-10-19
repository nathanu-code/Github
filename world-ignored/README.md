# World Ignored: content automation

Finds disaster footage, verifies it, tracks rights, edits it full-frame for every platform, writes
captions, sends review packages to Slack, publishes approved videos up to three times a day, and
reports performance every morning at 07:00 PHT.

The team handles **approvals, rights and exceptions**. Everything repetitive is automated.

## How it runs

```
             Claude Code Routines (Anthropic cloud, no laptop needed)
 05:45 PHT  morning_research ─┐   06:50 PHT daily_report     07:45 / 12:45 / 18:45 publish_slot (post1-3)
                              │          │                               │
                              ▼          ▼                               ▼
   ┌─────────────────────────── python -m wi <command> ──────────────────────────────────┐
   │ research/feeds   USGS, GDACS, NASA EONET, GDELT  →  event list for verification     │
   │ research/scoring rank candidates, repeat/variety checks, pick ≤3 slots              │
   │ models           status workflow + gates (verified? rights evidence? approved?)    │
   │ edit/analyze     YOLOX people/vehicles, YuNet faces, motion, saliency, OCR text    │
   │ edit/reframe     full-frame crop path that follows the action (no stretch, no blur) │
   │ edit/layout      banner placed where it covers the least action/on-screen text     │
   │ edit/render      one decode → 9:16 1080×1920, 4:5 1080×1350, X 720×1280; audio kept │
   │ edit/qc          resolution, borders, distortion, safe zones, padding, audio, previews│
   │ captions         per-platform captions/titles from verified fields only            │
   │ slack            review packages, confirmations, alerts, report                    │
   │ approvals        approver + version-code check; silence ≠ approval                 │
   │ publish/*        official APIs, idempotent ledger, safe retry, manual fallback      │
   │ analytics/report daily snapshots → 7 AM report, Google Sheets history              │
   └──────────────────────────────────────────────────────────────────────────────────────┘
        │ state/ (tracker.json, research, analytics)  → git branch world-ignored-ops
        │ media (raw, edits, previews, captions)      → Google Drive "World Ignored/…"
        └ tracker mirror                              → Google Sheet "World Ignored — Content Tracker"
```

Claude does what needs judgment (finding footage, checking it against sources, writing factual
headlines, reading Slack threads). Deterministic code does the rest and enforces the rules. A
Claude session can't publish uncleared or unapproved content because `wi/models.py` and
`wi/publish/runner.py` refuse.

## Content workflow

`UNVERIFIED → EVENT_VERIFIED/FOOTAGE_UNVERIFIED → FOOTAGE_VERIFIED/RIGHTS_PENDING → RIGHTS_CLEARED →
READY_FOR_EDITING → EDITED → READY_FOR_APPROVAL → APPROVED → SCHEDULED → PUBLISHED` (plus `FAILED`,
`ARCHIVED`).

| Gate | Enforced by |
|---|---|
| Event confirmed by sources before it can advance | `models.check_gate` |
| Rights cleared needs a clearing licence type (credit-only never clears), named holder, stored evidence, permitted platforms | `models.rights_clear` |
| Editing needs an authorised raw file on record | `models.check_gate` |
| Review needs every export to pass QC, plus captions | `models.check_gate` |
| Approval must come from a listed approver, quote the current version code, and name the platforms | `approvals.apply` |
| Any change to video or captions after approval voids the approval | `models.invalidate_approval_if_changed` |
| Publishing blocked if paused/stopped, not live, unapproved, rights missing for that platform | `publish/runner.publish_item` |
| One post per platform per approved version; interrupted uploads are checked, not re-posted | publish ledger |

## Slack commands (approvers: Nathan, Admin)

In the review thread: `APPROVE <version>` · `APPROVE <version> tiktok,youtube_shorts` ·
`REQUEST CHANGES <version> <what>` · `HOLD <version>` · `REJECT <version> <why>`.
In the channel: `WI PAUSE` · `WI RESUME` · `WI STOP` (emergency stop: nothing publishes until `WI RESUME`).

## Editing style

- Opening banner: bold white uppercase headline (Montserrat ExtraBold), optional subhead, then
  `LOCATION, COUNTRY | MON D, YYYY`, on a dark semi-transparent banner with fixed padding. Text is
  auto-sized and refused if it can't fit (shorten the headline).
- Closing banner: a safety hazard line plus an action line, during the final ~4 s.
- Placement: banners stay inside each platform's UI safe zone and go where they cover the least action
  (people, vehicles, motion, faces) and least burned-in text.
- Full frame: the footage fills the frame. The crop follows the action and holds still when a fixed
  crop is as good. If the crop would lose too much action, QC flags "MANUAL REVIEW". A blurred
  background is only rendered when a reviewer asks (`wi edit <id> --fit blur`).
- Audio: the original audio is kept with tiny edge fades. Nothing is added or looped. Silent sources
  get a silent track (and a flag).

## Common tasks

```bash
cd world-ignored && bash scripts/setup.sh
python -m wi health                       # what's connected, queue, control flags
python -m pytest -q tests                 # unit tests
python -m wi show <id>                    # one item
python -m wi tracker-csv                  # whole tracker
python -m wi control pause --by Nathan    # pause / resume / stop / unstop
```

**Change the schedule.** Edit `config/settings.yaml → schedule.slots`, and update the routine times
(ask Claude: "move the post2 routine to 2 PM").
**Change the style.** `config/settings.yaml → editing` (colours, durations, safe zones, QC thresholds)
and `wi/edit/banners.py` (sizes and weights).
**Add an approver.** Add their Slack user ID to `slack.approvers`.
**Go live.** Set `control.publishing_live: true` once accounts, rights and approvals are in place
(see `docs/SETUP.md`).

## Docs
- `docs/AUDIT.md`: what exists today, per-platform status, blockers
- `docs/SETUP.md`: every credential and how to add it
- `docs/PLATFORM_SPECS.md`: verified video and API specs (Oct 2026)
- `docs/COSTS.md`: operating cost estimate
- `ops/*.md`: runbooks the scheduled sessions follow
