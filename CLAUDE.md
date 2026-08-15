# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this repo is

An operations and agent-configuration workspace. It carries a curated subset of
[ECC](https://github.com/affaan-m/ECC) skills selected for a cabinetry supply and
design business that imports into Hawaii, plus this repo's own documentation.

There is no application code here. The deliverables are Markdown that steers
agent behavior, and the tooling that keeps it in sync with upstream.

## Layout

```
.claude/
  skills/    26 vendored ECC skills, loaded on demand
  agents/     7 vendored subagent definitions
  rules/      2 shared standards files
docs/
  ECC-EVALUATION.md      what ECC is, what was taken, what was skipped
scripts/
  sync-ecc.sh            refresh the vendored subset from a pinned upstream ref
THIRD_PARTY_LICENSES.md  MIT + Apache-2.0 attribution for vendored files
```

## Working with the vendored files

Everything under `.claude/skills/`, `.claude/agents/`, and `.claude/rules/` is
**vendored from upstream**. Treat it as third-party code.

- Prefer not to edit vendored files in place. Local edits are silently
  overwritten the next time `scripts/sync-ecc.sh` runs.
- If a skill needs local behavior, add a sibling skill under a distinct name
  rather than patching the vendored one.
- The seven Apache-2.0 skills listed in `THIRD_PARTY_LICENSES.md` require a
  change notice if you do modify them. Record it in that file's modification
  log.
- Preserve YAML frontmatter exactly — `license`, `author`, and
  `metadata.origin` carry attribution.

## Syncing upstream

```bash
scripts/sync-ecc.sh                # sync at the pinned commit
ECC_REF=main scripts/sync-ecc.sh   # preview upstream tip
```

Always review `git diff .claude` before committing a sync. These files change
how agents behave, so a blind sync is a behavior change you did not read.

To add or drop a skill, edit the `SKILLS` / `AGENTS` / `RULES` arrays in
`scripts/sync-ecc.sh` and re-run it — that script is the source of truth for
what is vendored, not the directory contents.

## Deliberate exclusions

ECC's 23 enforcement hooks are **not** installed here, and adding them should be
a considered decision rather than a convenience. They fire on every tool call,
spawn a Node process each time, and run roughly 64k lines of upstream
JavaScript with filesystem access. `docs/ECC-EVALUATION.md` has the reasoning.

## Domain content caveat

The trade, logistics, quality, and manufacturing skills cite specific
regulations (19 CFR, 19 USC, FDA, IATF 16949, AS9100, Incoterms 2020). They are
decision support, not legal advice, and they can drift as rules change. When a
task turns on a current tariff rate, an AD/CVD order, a filing deadline, or a
penalty amount, verify against the primary source before acting — do not rely on
the skill text alone.
