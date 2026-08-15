#!/usr/bin/env bash
#
# sync-ecc.sh — refresh the vendored ECC subset from upstream.
#
# Vendors a curated slice of https://github.com/affaan-m/ECC into .claude/.
# Only the skills, agents, and rules listed below are copied. Hooks, the
# installer, and the other ~258 upstream skills are intentionally excluded —
# see docs/ECC-EVALUATION.md.
#
# Usage:
#   scripts/sync-ecc.sh            # sync at the pinned ref
#   ECC_REF=main scripts/sync-ecc.sh   # preview upstream tip
#
# To take updates: bump ECC_REF below, run this, then REVIEW THE DIFF before
# committing. These files steer agent behavior; never sync blind.

set -euo pipefail

ECC_REPO="${ECC_REPO:-https://github.com/affaan-m/ECC.git}"
ECC_REF="${ECC_REF:-c9de8f5b2b3a225bca9befa2b7700aa5e3a4d1b8}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$REPO_ROOT/.claude"

SKILLS=(
  # Trade and supply chain (Apache-2.0)
  customs-trade-compliance
  logistics-exception-management
  carrier-relationship-management
  inventory-demand-planning
  returns-reverse-logistics
  quality-nonconformance
  production-scheduling
  # Revenue and marketing
  lead-intelligence
  market-research
  marketing-campaign
  seo
  brand-voice
  competitive-platform-analysis
  customer-billing-ops
  # Research and knowledge
  deep-research
  research-ops
  documentation-lookup
  # Skill maintenance
  skill-scout
  skill-stocktake
  context-budget
  token-budget-advisor
  verification-loop
  # Light engineering
  coding-standards
  git-workflow
  github-ops
  security-review
)

AGENTS=(
  chief-of-staff
  marketing-agent
  seo-specialist
  planner
  code-reviewer
  security-reviewer
  docs-lookup
)

RULES=(
  common/coding-style.md
  common/security.md
)

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo "[ecc-sync] cloning $ECC_REPO @ $ECC_REF"
git clone --quiet --filter=blob:none --no-checkout "$ECC_REPO" "$TMP/ecc"
git -C "$TMP/ecc" fetch --quiet --depth 1 origin "$ECC_REF"
git -C "$TMP/ecc" checkout --quiet FETCH_HEAD

RESOLVED="$(git -C "$TMP/ecc" rev-parse HEAD)"
echo "[ecc-sync] upstream resolved to $RESOLVED"

missing=0

echo "[ecc-sync] syncing ${#SKILLS[@]} skills"
mkdir -p "$DEST/skills"
for s in "${SKILLS[@]}"; do
  if [ -d "$TMP/ecc/skills/$s" ]; then
    rm -rf "${DEST:?}/skills/$s"
    cp -R "$TMP/ecc/skills/$s" "$DEST/skills/$s"
  else
    echo "[ecc-sync] WARNING: skill '$s' not found upstream — left as-is" >&2
    missing=$((missing + 1))
  fi
done

echo "[ecc-sync] syncing ${#AGENTS[@]} agents"
mkdir -p "$DEST/agents"
for a in "${AGENTS[@]}"; do
  if [ -f "$TMP/ecc/agents/$a.md" ]; then
    cp "$TMP/ecc/agents/$a.md" "$DEST/agents/$a.md"
  else
    echo "[ecc-sync] WARNING: agent '$a' not found upstream — left as-is" >&2
    missing=$((missing + 1))
  fi
done

echo "[ecc-sync] syncing ${#RULES[@]} rules"
for r in "${RULES[@]}"; do
  if [ -f "$TMP/ecc/rules/$r" ]; then
    mkdir -p "$DEST/rules/$(dirname "$r")"
    cp "$TMP/ecc/rules/$r" "$DEST/rules/$r"
  else
    echo "[ecc-sync] WARNING: rule '$r' not found upstream — left as-is" >&2
    missing=$((missing + 1))
  fi
done

# Local (non-vendored) skills live alongside the vendored ones and are never
# touched by this script — it only removes paths it is about to rewrite. Report
# them so it stays obvious that they exist and are out of scope here.
local_skills=()
for d in "$DEST"/skills/*/; do
  name="$(basename "$d")"
  is_vendored=0
  for s in "${SKILLS[@]}"; do [ "$s" = "$name" ] && is_vendored=1 && break; done
  [ "$is_vendored" -eq 0 ] && local_skills+=("$name")
done
if [ "${#local_skills[@]}" -gt 0 ]; then
  echo "[ecc-sync] left ${#local_skills[@]} local skill(s) untouched: ${local_skills[*]}"
fi

echo
echo "[ecc-sync] done. upstream=$RESOLVED missing=$missing"
if [ "$RESOLVED" != "$ECC_REF" ]; then
  echo "[ecc-sync] NOTE: ECC_REF was not a full commit sha; pin it to $RESOLVED"
fi
echo "[ecc-sync] review the diff before committing:  git diff --stat .claude"
if [ "$missing" -gt 0 ]; then
  echo "[ecc-sync] $missing item(s) missing upstream — reconcile the lists in this script" >&2
  exit 1
fi
