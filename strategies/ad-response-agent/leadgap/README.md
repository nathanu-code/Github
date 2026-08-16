# leadgap

A Trojan Horse prospecting tracker for the [Ad Response Agent](../README.md)
strategy. Python 3.9+, standard library only, single-file, no install.

You poke a prospect's own funnel the way a real lead would. `leadgap` keeps the
stopwatch, grades the gap, and renders the audit you open the call with.

```bash
cd strategies/ad-response-agent/leadgap
export LEADGAP_DB=~/leadgap.db        # keep real prospect data out of the repo
python3 leadgap.py --help
```

## The loop

```bash
# 1. Source from the Meta Ad Library — the active-ad count is your budget proof
python3 leadgap.py add --name "Desert Bloom Med Spa" --niche "med spa" \
  --city "Albuquerque, NM" --phone "505-555-0142" --active-ads 7

# 2. Submit their contact form (organically — not via their paid ad), start the clock
python3 leadgap.py probe 1 --via form

# 3. Log anything that comes back. Relative times are fine.
python3 leadgap.py respond 1 --channel sms --at -20m

# 4. Work the hot list
python3 leadgap.py list --verdict hot

# 5. Call with the evidence already filled in
python3 leadgap.py script 1

# 6. Send the audit to everyone who didn't pick up
python3 leadgap.py report 1 --out ~/audits/desert-bloom.md
```

## Commands

| Command | Does |
| --- | --- |
| `add` | Record a prospect and their live ad count |
| `probe <id>` | Start the clock — you just submitted their form or called |
| `respond <id>` | Log a response on a channel (`call` `sms` `email` `dm` `other`) |
| `close <id>` | Stop the clock and freeze the grade |
| `show <id>` | Everything known about one prospect (`--json`) |
| `list` | The pipeline, hottest first (`--verdict` `--niche` `--city` `--json`) |
| `stats` | Counts and hot rate (`--json`) |
| `report <id>` | Client-ready speed-to-lead audit in markdown (`--out FILE`) |
| `script <id>` | Call script with this prospect's evidence substituted in |
| `export` | Dump the pipeline (`--format csv\|json`) |

## Times

Anywhere a `--at` is accepted: `now`, a relative offset (`-45m`, `-2h`, `-3d`,
`+90s`), or an ISO timestamp (`2026-08-16T14:30`, `2026-08-16 14:30-10:00`).
Bare ISO timestamps are read as your local time; everything is stored as UTC and
displayed back in local time.

## Grading

| Grade | First response | Verdict |
| --- | --- | --- |
| `INSTANT` | ≤ 5 sec | skip — they beat the bar named in the source reel |
| `COVERED` | ≤ 5 min | skip — re-probe in 90 days |
| `SLOW` | 5 min – 1 hr | warm |
| `COLD` | > 1 hr | **hot** |
| `GHOST` | nothing after 24 hr | **hot** |
| `PENDING` | nothing yet, < 24 hr | wait |
| `UNTESTED` | no probe run | `script` refuses — you have no evidence |

Boundaries are inclusive at the top of each tier. Reasoning behind the
thresholds is in [ANALYSIS.md §6](../ANALYSIS.md#6-the-scoring-model-as-implemented).

## Storage

One SQLite file — `./leadgap.db` by default, or `--db PATH`, or `$LEADGAP_DB`.
Three tables: `prospects`, `probes`, `responses`. Deleting a prospect cascades.
A prospect can hold multiple probes; grading always uses the newest, which is how
you re-probe without losing history.

The database holds real names and phone numbers. `.gitignore` covers `*.db`, but
pointing `LEADGAP_DB` outside the repo is better.

## Tests

```bash
python3 -m unittest test_leadgap -v      # 37 tests, no dependencies
```
