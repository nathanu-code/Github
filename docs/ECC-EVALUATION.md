# ECC Evaluation

An assessment of [affaan-m/ECC](https://github.com/affaan-m/ECC) and a record of
what this repository vendored from it, what it skipped, and why.

Evaluated at upstream commit `c9de8f5b2b3a225bca9befa2b7700aa5e3a4d1b8`
(2026-08-13).

## What ECC is

ECC ("Everything Claude Code") is a large, actively maintained configuration
layer for AI coding agents. It is not an application and it is not a library —
it ships almost no runtime product code. It is a **content pack plus an
enforcement runtime**:

| Component | Count | What it is |
| --- | ---: | --- |
| Skills | 284 | Markdown playbooks with YAML frontmatter, loaded on demand |
| Agents | 68 | Subagent definitions (role prompt + tool allowlist + model) |
| Commands | 94 shims | Legacy slash-command entry points |
| Hooks | 23 entries | Node scripts fired on tool-use events |
| Rules | selective | Always-loaded standards, opt-in per language/project |
| AgentShield | included | Scanner for prompts, hooks, MCP config, secrets |

Its stated pipeline is `plan -> test -> implement -> review -> verify ->
remember -> improve`. The pitch is that you install that process once instead of
re-prompting it every session.

Scale and health signals: 3,479 tracked files (~62 MB excluding git history),
2,510 of them Markdown; 2,784 merged pull requests; 240 test files; 11 CI
workflows including SLSA3 provenance publishing and a supply-chain watch job.
Last commit was two days before this evaluation. It is MIT-licensed with a
commercial hosted tier (ECC Pro) layered on top.

## Verdict: useful, but only in parts

**The content is real.** This was the main thing worth checking, because a repo
with 284 AI-authored-looking skill files is exactly where you would expect
padding. Spot checks did not find it. The `customs-trade-compliance` skill
cites 19 CFR § 141.86, 19 USC § 1592, the ISF 10+2 filing window with the
correct $5,000-per-violation liquidated damages figure, the General Rules of
Interpretation in their correct precedence order, and the Incoterms 2020 change
requiring Institute Cargo Clauses (A) for CIP. Those are accurate and specific.
`production-scheduling` covers drum-buffer-rope, SMED, and OEE properly.
`inventory-demand-planning` handles ABC/XYZ classification and safety stock
under lead-time variability. Eight of these operations skills carry
`license: Apache-2.0` and an `author: evos` tag, suggesting they came from
someone with actual domain background rather than from a prompt.

**The breadth is the problem.** 284 skills is far more than any single operation
needs, and in Claude Code every installed skill's description competes for
selection attention. Installing all of ECC to get the twelve skills you care
about means the other 272 are noise in every routing decision. This is a real
cost, not a theoretical one.

**The hooks are the risky part.** ECC ships 23 hook entries, several matching
`*` — meaning they run on *every* tool call. Each one bootstraps through an
inlined ~700-character Node resolver that walks `~/.claude`, then
`~/.claude/plugins`, then a plugin cache tree, trying six different directory
names to locate its own root before executing. That is a lot of filesystem
probing and process spawning on every single action the agent takes. The
`scripts/` tree behind it is roughly 64,000 lines of JavaScript.

To be fair to ECC: the recent commit history is dominated by security hardening
of exactly this surface — reparse-point rejection, no-follow semantics on
Windows, installer filesystem race fixes, checkpointed migrations. The
maintainer is clearly taking it seriously. No telemetry or outbound network
calls were found in the hook scripts. But "large privileged surface, actively
being hardened" still means you should adopt it deliberately rather than by
default.

**Sustainability.** One maintainer shipping across seven harnesses is
impressive and also a bus-factor risk. Vendoring a pinned subset hedges this:
if upstream stalls or changes direction, what we depend on keeps working.

## What this repo took

26 skills, 7 agents, and 2 rule files — about 592 KB versus 62 MB upstream.
Selection was driven by the actual business: cabinetry supply and design,
importing into Hawaii.

**Trade and supply chain** — the highest-value group here, because imported
cabinetry runs straight into HTS classification, antidumping exposure, and
ocean freight to a non-contiguous state:
`customs-trade-compliance`, `logistics-exception-management`,
`carrier-relationship-management`, `inventory-demand-planning`,
`returns-reverse-logistics`, `quality-nonconformance`, `production-scheduling`

**Revenue and marketing:**
`lead-intelligence`, `market-research`, `marketing-campaign`, `seo`,
`brand-voice`, `competitive-platform-analysis`, `customer-billing-ops`

**Research and knowledge:**
`deep-research`, `research-ops`, `documentation-lookup`

**Skill maintenance** — for keeping our own existing skills healthy:
`skill-scout`, `skill-stocktake`, `context-budget`, `token-budget-advisor`,
`verification-loop`

**Light engineering:**
`coding-standards`, `git-workflow`, `github-ops`, `security-review`

**Agents:** `chief-of-staff`, `marketing-agent`, `seo-specialist`, `planner`,
`code-reviewer`, `security-reviewer`, `docs-lookup`

## What this repo deliberately skipped

**All 23 hooks.** This is the main judgment call. Enforcement hooks that fire on
every tool call are the highest-risk, highest-latency part of ECC, and their
value is mostly for large engineering teams enforcing test discipline across
many contributors. Skills give most of the benefit at none of the risk. Skills
are inert Markdown; they only ever influence the agent by being read.

**The other 258 skills.** Framework playbooks (Laravel, Quarkus, SpringBoot,
Flutter, SwiftUI), language toolchains, homelab networking, healthcare/HIPAA,
DeFi and prediction-market tooling, video generation. All fine work, none of it
load-bearing for this business.

**The installer, npm packages, and GitHub App.** Not needed for a vendored
subset, and the installer is the piece with the most privileged filesystem
behavior.

**The 94 legacy command shims.** Upstream is itself migrating away from these
toward a skills-first surface.

## Maintenance

`scripts/sync-ecc.sh` re-pulls the vendored subset from a pinned upstream
commit. The pin lives in that script. To take upstream updates, bump
`ECC_REF`, run the script, and review the resulting diff before committing —
never sync blind, since these files steer agent behavior.

## If you want the full thing instead

Vendoring is the conservative path. The full install is one command in Claude
Code:

```text
/plugin marketplace add https://github.com/affaan-m/ECC
/plugin install ecc@ecc
```

That gets all 284 skills, all 68 agents, and the hook runtime. It is a
reasonable choice for a dedicated software project. It is the wrong default for
this repo.

## Licensing

Upstream ECC is MIT (Copyright © 2026 Affaan Mustafa). Seven of the vendored
skills are individually marked Apache-2.0. Both licenses and their attribution
requirements are recorded in [`THIRD_PARTY_LICENSES.md`](../THIRD_PARTY_LICENSES.md).
Original frontmatter — including `license`, `author`, and `metadata.origin`
fields — was left intact in every vendored file.
