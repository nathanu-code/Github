# Ad Response Agent

A transcribed, analysed, and implemented sales strategy for selling AI voice /
automation services to local businesses.

**Source:** [instagram.com/reel/DcBUmWpq7Pa](https://www.instagram.com/reel/DcBUmWpq7Pa/)
· [@davidhvnter](https://www.instagram.com/davidhvnter/) · captured 2026-08-16

---

## The strategy in one paragraph

Stop selling "AI receptionist" as a category. Sell one narrow outcome — **answer
inbound ad leads instantly** — to businesses you have already *proven* are
failing at it. Find them in the Meta Ad Library, because appearing there means
they have budget and live lead flow. Submit their own contact form and start a
stopwatch. When nobody calls back, you no longer have a cold call; you have a
findings report with a timestamp on it.

Three moves:

1. **Rename the product.** "Ad response agent," not "AI receptionist" — it moves
   the purchase from *new headcount cost* to *recovering ad spend already
   committed*.
2. **Source from the Meta Ad Library.** A business advertising right now has
   self-certified budget, inbound flow, and a measurable leak.
3. **Run the Trojan Horse probe.** Test their funnel before you contact them.
   The ones who respond fast get disqualified for free; the ones who don't hand
   you your opener.

## What's here

| File | What it is |
| --- | --- |
| [`TRANSCRIPT.md`](TRANSCRIPT.md) | Full timestamped transcript, on-screen text, source metadata, and corrections for the ASR errors |
| [`ANALYSIS.md`](ANALYSIS.md) | What's sharp, what's oversold, what's missing — including the compliance exposure the reel never mentions |
| [`PLAYBOOK.md`](PLAYBOOK.md) | The operating procedure: daily numbers, nine steps, guardrails |
| [`leadgap/`](leadgap/) | Working CLI that tracks probes, grades the gap, and renders the audit and call script |
| [`assets/call-script.md`](assets/call-script.md) | The call, beat by beat, with the reasoning behind each line |
| [`assets/outreach-templates.md`](assets/outreach-templates.md) | Email, SMS, DM, LinkedIn, and the 14-day follow-up sequence |

## Quickstart

```bash
cd strategies/ad-response-agent/leadgap
export LEADGAP_DB=~/leadgap.db

python3 leadgap.py add --name "Desert Bloom Med Spa" --niche "med spa" \
  --city "Albuquerque, NM" --phone "505-555-0142" --active-ads 7
python3 leadgap.py probe 1 --via form      # submit their form, start the clock
# ...wait...
python3 leadgap.py list --verdict hot
python3 leadgap.py script 1                # call script, evidence filled in
python3 leadgap.py report 1                # the audit you send them
```

## Changes made to the source strategy

The reel is a two-minute monologue; a few things were wrong or missing and are
corrected here rather than reproduced. Full reasoning in
[ANALYSIS.md](ANALYSIS.md).

| Reel says | This implementation |
| --- | --- |
| "No callback in **5 seconds** → they need it" | Keeps 5s as its own `INSTANT` tier, but grades against a **5-minute** benchmark. Nobody hits 5 seconds, so as a filter it qualifies everyone and therefore no one. |
| One probe proves need | **Two probes**, different days and times, before any written report. A finding you can't reproduce blows up on the call. |
| "So you're not interested in making more money on autopilot? Help me understand that." | Prints both that line and a rewrite that keeps the reframe without the loaded question. |
| "I invented this" | Mystery-shopper audits predate the reel by decades. Doesn't matter — it still works. |
| (Nothing on how you reach the funnel) | Reach it **organically**. Clicking their paid ad bills them for your own sales research. |
| (Nothing on compliance) | A2P 10DLC for SMS, consent language, and the FCC's 2024 position on AI voice — settle it before the first install. |
| (Nothing on who buys) | High-ticket, appointment-driven local services. A business with an $80 average job will not care. |

## Status

Implemented and tested — `python3 -m unittest test_leadgap` (37 tests, standard
library only).
