#!/usr/bin/env bash
#
# Flick smoke test.
#
# Renders one self-contained template from Flick's saved-animations library
# end to end (scaffold -> npm install -> render -> poster) and audits the
# library for templates whose staticFile() references are not bundled.
#
# Usage: ./verify-flick.sh [--skill DIR] [--workdir DIR] [--keep]

set -euo pipefail

SKILL=""
WORKDIR=""
KEEP=0

while [ $# -gt 0 ]; do
  case "$1" in
    --skill)   SKILL="${2:?--skill needs a directory}"; shift 2 ;;
    --workdir) WORKDIR="${2:?--workdir needs a directory}"; shift 2 ;;
    --keep)    KEEP=1; shift ;;
    -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)         echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

say()  { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
pass() { printf '\033[32m  PASS\033[0m %s\n' "$*"; }
fail() { printf '\033[31m  FAIL\033[0m %s\n' "$*"; FAILURES=$((FAILURES + 1)); }
die()  { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

FAILURES=0

# This template is verified to make no staticFile() calls, so it renders with
# no brand assets and no sound files present.
SCENE_DIR="connected-workflow-terminals"
SCENE_FILE="WorkflowStartToFinishScene.tsx"
SCENE_EXPORT="WorkflowStartToFinishScene"
SCENE_DURATION="WORKFLOW_START_TO_FINISH_DURATION"
COMPOSITION="flick-verify"

if [ -z "$SKILL" ]; then
  while IFS= read -r found; do
    [ -f "$found/scripts/setup-workspace.mjs" ] || continue
    SKILL="$found"; break
  done < <(
    find "$HOME/.claude/plugins" "$HOME/.claude/skills" "$HOME/.agents/skills" \
         "$HOME/.codex/skills" ./skills ./.claude/skills \
         -maxdepth 6 -type d -name flick 2>/dev/null | sort
  )
  [ -n "$SKILL" ] || die "Could not find an installed Flick skill. Pass --skill /path/to/skills/flick"
fi
SKILL="$(cd "$SKILL" && pwd)"
[ -f "$SKILL/scripts/setup-workspace.mjs" ] || die "Not a Flick skill directory: $SKILL"

if [ -z "$WORKDIR" ]; then
  WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/flick-verify.XXXXXX")"
  trap '[ "$KEEP" -eq 1 ] || rm -rf "$WORKDIR"' EXIT
fi
PROJECT="$WORKDIR/project"

say "Flick smoke test"
echo "  skill    $SKILL"
echo "  workdir  $WORKDIR"

# ------------------------------------------------- 1. library asset audit
say "Auditing saved-animations for unbundled references"
SOUNDS="$SKILL/assets/starter-remotion/public/sounds"
LIB="$SKILL/saved-animations"
if [ -d "$LIB" ] && [ -d "$SOUNDS" ]; then
  MISSING="$(
    comm -23 \
      <(grep -rho 'staticFile("sounds/[^"]*")' "$LIB" 2>/dev/null \
          | sed 's/staticFile("sounds\///; s/")//' | sort -u) \
      <(ls "$SOUNDS" | sort -u)
  )"
  if [ -n "$MISSING" ]; then
    fail "templates reference sound files that Flick does not bundle:"
    printf '         %s\n' $MISSING
    echo "         Swap these for a bundled sound before rendering such a template."
  else
    pass "every referenced sound effect is bundled"
  fi
else
  fail "saved-animations or bundled sounds directory missing"
fi

# ------------------------------------------------- 2. scaffold + install
say "Scaffolding workspace"
node "$SKILL/scripts/setup-workspace.mjs" --project "$PROJECT" >/dev/null
[ -f "$PROJECT/remotion/package.json" ] && pass "workspace scaffolded" || fail "workspace not scaffolded"

TEMPLATE="$LIB/$SCENE_DIR/$SCENE_FILE"
[ -f "$TEMPLATE" ] || die "Template not found: $TEMPLATE"
mkdir -p "$PROJECT/remotion/src/scenes"
cp "$TEMPLATE" "$PROJECT/remotion/src/scenes/"

cat > "$PROJECT/remotion/src/Root.tsx" <<EOF
import type {FC} from 'react';
import {Composition} from 'remotion';
import {$SCENE_EXPORT, $SCENE_DURATION} from './scenes/${SCENE_FILE%.tsx}';

export const RemotionRoot: FC = () => (
  <Composition
    id="$COMPOSITION"
    component={$SCENE_EXPORT}
    durationInFrames={$SCENE_DURATION}
    fps={30}
    width={1080}
    height={1920}
  />
);
EOF

say "Installing Remotion"
( cd "$PROJECT/remotion" && npm install --no-audit --no-fund >/dev/null 2>&1 ) \
  && pass "npm install" || fail "npm install"

say "Ensuring headless browser"
( cd "$PROJECT/remotion" && npx --yes remotion browser ensure >/dev/null 2>&1 ) \
  && pass "chrome-headless-shell present" || fail "could not fetch chrome-headless-shell"

# ------------------------------------------------- 3. render + poster
say "Rendering"
OUT="$PROJECT/scenes/$COMPOSITION/$COMPOSITION.mp4"
mkdir -p "$(dirname "$OUT")"
if ( cd "$PROJECT/remotion" && npx --yes remotion render src/index.tsx "$COMPOSITION" "$OUT" >/dev/null 2>&1 ); then
  if [ -s "$OUT" ]; then
    pass "rendered $(du -h "$OUT" | cut -f1) -> $(basename "$OUT")"
  else
    fail "render reported success but produced no file"
  fi
else
  fail "remotion render failed"
fi

say "Extracting poster"
if [ -s "$OUT" ] && node "$SKILL/scripts/create-poster.mjs" \
     --project "$PROJECT" --name "$COMPOSITION" --timestamp 2 >/dev/null 2>&1; then
  [ -s "$PROJECT/scenes/$COMPOSITION/poster.jpg" ] \
    && pass "poster.jpg extracted" || fail "poster.jpg missing"
else
  fail "create-poster.mjs failed"
fi

# ------------------------------------------------- summary
say "Result"
if [ "$FAILURES" -eq 0 ]; then
  printf '\033[32mAll checks passed.\033[0m Flick can render on this machine.\n'
else
  printf '\033[31m%s check(s) failed.\033[0m\n' "$FAILURES"
fi
[ "$KEEP" -eq 1 ] && echo "Output kept at: $PROJECT"
exit "$FAILURES"
