# Github

An operations and agent-configuration workspace, carrying a curated subset of
[ECC](https://github.com/affaan-m/ECC) skills chosen for a cabinetry supply and
design business importing into Hawaii.

## What's here

| Path | Contents |
| --- | --- |
| `.claude/skills/` | 26 vendored skills — trade compliance, logistics, inventory, quality, marketing, research |
| `.claude/agents/` | 7 vendored subagent definitions |
| `.claude/rules/` | 2 shared standards files |
| `docs/ECC-EVALUATION.md` | Assessment of ECC and the rationale for what was taken |
| `scripts/sync-ecc.sh` | Refresh the vendored subset from a pinned upstream commit |
| `THIRD_PARTY_LICENSES.md` | MIT + Apache-2.0 attribution |

Claude Code picks the skills up automatically — they load on demand when a task
matches, and cost nothing when idle.

## The vendored skills

**Trade and supply chain** — the highest-value group, since imported cabinetry
runs into HTS classification, antidumping exposure, and ocean freight to a
non-contiguous state:
`customs-trade-compliance` · `logistics-exception-management` ·
`carrier-relationship-management` · `inventory-demand-planning` ·
`returns-reverse-logistics` · `quality-nonconformance` · `production-scheduling`

**Revenue and marketing:** `lead-intelligence` · `market-research` ·
`marketing-campaign` · `seo` · `brand-voice` ·
`competitive-platform-analysis` · `customer-billing-ops`

**Research:** `deep-research` · `research-ops` · `documentation-lookup`

**Skill maintenance:** `skill-scout` · `skill-stocktake` · `context-budget` ·
`token-budget-advisor` · `verification-loop`

**Engineering:** `coding-standards` · `git-workflow` · `github-ops` ·
`security-review`

## Why a subset instead of all of ECC

Upstream ships 284 skills across ~62 MB. Every installed skill's description
competes for selection attention, so installing all of it to reach the dozen
that matter makes routing worse, not better. This repo vendors ~592 KB.

ECC's 23 enforcement hooks are also excluded — they fire on every tool call and
run a large privileged JavaScript surface. Skills are inert Markdown and carry
none of that risk. Full reasoning in
[`docs/ECC-EVALUATION.md`](docs/ECC-EVALUATION.md).

If you do want the whole thing, it is two commands in Claude Code:

```text
/plugin marketplace add https://github.com/affaan-m/ECC
/plugin install ecc@ecc
```

## Updating

```bash
scripts/sync-ecc.sh                # sync at the pinned commit
ECC_REF=main scripts/sync-ecc.sh   # preview upstream tip
```

Review `git diff .claude` before committing. `scripts/sync-ecc.sh` is the source
of truth for what is vendored — add or drop entries there, then re-run it.

## Caveat

The trade, logistics, and quality skills cite specific regulations. They are
decision support, not legal advice. Verify current tariff rates, AD/CVD orders,
filing deadlines, and penalty amounts against primary sources before acting.
