# Playbook — running the Ad Response Agent strategy

The operating procedure. Every step has a command; the commands keep the
evidence so the call script writes itself.

All commands run from `leadgap/`. Set the database once per session:

```bash
cd strategies/ad-response-agent/leadgap
export LEADGAP_DB=~/leadgap.db     # keep it outside the repo — it holds real prospect data
```

---

## Daily numbers

A sustainable solo cadence, assuming ~2 focused hours:

| Activity | Target/day | Notes |
| --- | --- | --- |
| Prospects sourced from the Ad Library | 20 | 15 minutes of scrolling |
| Probes started | 20 | Batch them; the wait is free |
| Probes matured (24 hr+) and graded | 20 | Yesterday's batch |
| Hot prospects called | 8–12 | Only `hot` and `warm`; never `untested` |
| Audits sent | 5 | To everyone who didn't answer the phone |

Expect roughly half to three-quarters of probed prospects to grade `hot`. If you
are grading under 30% hot, your niche is too well-run — move to a sloppier
vertical or a smaller market.

---

## Step 1 — Pick one niche and one metro

Not "local businesses." One vertical, one city, for at least two weeks. Repetition
is what makes the call script sharp and the objections predictable.

Pick a vertical where a single recovered lead pays for months of the product:

> med spas · dental & cosmetic · roofing & restoration · HVAC · law firms
> · home remodelling · elective medical · solar · pool builders

Avoid anything with a sub-$500 average job. The arithmetic doesn't work and they
know it.

## Step 2 — Source from the Meta Ad Library

Go to **facebook.com/ads/library**, set *Ad category* to **All ads**, choose the
country, and search your niche plus the metro (`med spa Albuquerque`).

For each advertiser, capture: business name, how many ads are running right now,
their landing page, and their phone number. The active-ad count is your budget
proof — record it.

```bash
python3 leadgap.py add \
  --name "Desert Bloom Med Spa" \
  --niche "med spa" \
  --city "Albuquerque, NM" \
  --phone "505-555-0142" \
  --website "https://desertbloommedspa.example" \
  --ad-library-url "https://www.facebook.com/ads/library/?q=desert+bloom" \
  --active-ads 7
```

**Prioritise** advertisers running many ads at once, and ones whose ads have been
live for weeks — sustained spend means sustained lead flow.

## Step 3 — Run the Trojan Horse probe

Reach their funnel **organically**. Type the URL directly or use the landing page
link from the Ad Library. Do not click their paid ad to get there — that bills
them for your own sales research, and it is the first thing they'll notice if
they audit their spend after you call.

Submit the *Contact Us* / *Book a consult* form with a real name and a phone
number and email you will actually monitor. Then start the clock:

```bash
python3 leadgap.py probe 1 --via form --at now
```

Then **call their main line** and note whether a human picks up. If it rings out
to voicemail, that's a second data point in the same audit.

Now leave it alone. The waiting is the product.

## Step 4 — Log whatever comes back

Every time they contact you, record it. Relative times are fine:

```bash
python3 leadgap.py respond 1 --channel sms   --at -20m
python3 leadgap.py respond 1 --channel call  --at "2026-08-16T14:05"
python3 leadgap.py respond 1 --channel email --at now --notes "generic autoresponder, no human"
```

An automated "thanks, we got your request" autoresponder is **not** a response —
log it with a note, but the honest audit is about human contact. Say so on the
call if they push back; conceding the point makes the rest of the finding
credible.

## Step 5 — Probe again before you report

One probe is an anecdote. Run a second on a different day and a different time
of day before you build anything on it:

```bash
python3 leadgap.py probe 1 --via form --at now --notes "second probe, Saturday morning"
```

If probe two comes back fast, they're not broken — they had a bad Tuesday. Drop
them. Better to lose the prospect than to open a call with a finding they can
disprove in one sentence.

## Step 6 — Work the hot list

```bash
python3 leadgap.py list --verdict hot
python3 leadgap.py show 1
```

Freeze the clock on anything you're about to report, so the numbers stay stable:

```bash
python3 leadgap.py close 1
```

## Step 7 — Call with the evidence in front of you

```bash
python3 leadgap.py script 1
```

The script prints the verdict, the exact evidence sentence, the opener, the
bridge, and the objection handling — with their name, city, ad count, and gap
time already substituted. See [`assets/call-script.md`](assets/call-script.md)
for the reasoning behind each beat.

The rule: **you are reporting a finding, not pitching a product.** Do not say
"AI" in the first thirty seconds.

## Step 8 — Send the audit to everyone who didn't answer

```bash
python3 leadgap.py report 1 --out ~/audits/desert-bloom.md
```

It renders a client-ready speed-to-lead audit: what you did, what happened per
channel, what it cost, and the fix. Send it as the follow-up to a voicemail, as
the attachment to the email you promised on the call, or as the DM. Templates for
all three are in [`assets/outreach-templates.md`](assets/outreach-templates.md).

## Step 9 — Track the funnel

```bash
python3 leadgap.py stats
python3 leadgap.py export --format csv > ~/pipeline.csv
```

Watch the hot rate. If it collapses, your niche has caught up and it's time to
move.

---

## Guardrails

Non-negotiable, in rough order of how badly it goes if you skip them:

1. **Never call an `UNTESTED` prospect.** Without evidence you are just another
   AI cold caller, and the whole edge of this strategy is gone. The tool refuses
   to print a script for one.
2. **Reach the funnel organically.** Never through their paid ad.
3. **Don't fabricate an identity.** Use a real name and real contact details on
   the form. You are going to reference this interaction to their face.
4. **Two probes before any written report.**
5. **Settle compliance before your first install** — A2P 10DLC registration for
   SMS, consent language on the form, and the FCC's 2024 position on AI voice in
   outbound calls. See [ANALYSIS.md §5](ANALYSIS.md#5-what-the-reel-leaves-out-entirely).
6. **Keep the database out of the repo.** It holds real names and phone numbers.
   `.gitignore` covers `*.db`, but `LEADGAP_DB` pointing outside the repo is
   better.

---

## Run it on yourself first

Before selling this to anyone, probe your own businesses. Fill out your own
contact form from a phone that isn't yours and start the same clock. If your own
grade comes back `COLD`, you just found the demo — and the case study.
