#!/usr/bin/env bash
#
# Hardened Flick installer.
#
# Flick's own scripts/bootstrap.mjs installs Whisper and yt-dlp with
# `pip install --user`. That fails on any Python marked externally-managed
# (PEP 668: Homebrew Python, Ubuntu 23.04+, Debian 12+, Fedora 38+) and it
# also fails inside a virtualenv, so there is no shell you can run it from
# that works everywhere. This wrapper performs the same setup, but puts the
# Python side in a project-local virtualenv instead.
#
# It also pre-downloads Remotion's chrome-headless-shell, because the first
# render otherwise stops with a browser-launch error, and it can relocate
# Flick's saved-animations library out of the plugin directory so a plugin
# update cannot take it with it.
#
# Usage:
#   ./install-flick.sh [--project DIR] [--skill DIR] [--library DIR]
#                      [--skip-python] [--skip-browser]

set -euo pipefail

PROJECT="flick-output"
SKILL=""
LIBRARY=""
SKIP_PYTHON=0
SKIP_BROWSER=0

while [ $# -gt 0 ]; do
  case "$1" in
    --project)       PROJECT="${2:?--project needs a directory}"; shift 2 ;;
    --skill)         SKILL="${2:?--skill needs a directory}"; shift 2 ;;
    --library)       LIBRARY="${2:?--library needs a directory}"; shift 2 ;;
    --skip-python)   SKIP_PYTHON=1; shift ;;
    --skip-browser)  SKIP_BROWSER=1; shift ;;
    -h|--help)       sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)               echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

say()  { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------- preflight
say "Checking prerequisites"

command -v node >/dev/null 2>&1 || die "Node.js not found. Flick needs Node.js 20 or newer."
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
[ "$NODE_MAJOR" -ge 20 ] || die "Node.js $(node -v) is too old. Flick needs 20 or newer."
echo "  node    $(node -v)"

PY=""
for candidate in python3 python; do
  command -v "$candidate" >/dev/null 2>&1 || continue
  if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    PY="$candidate"; break
  fi
done
if [ -z "$PY" ]; then
  [ "$SKIP_PYTHON" -eq 1 ] || die "Python 3.9+ not found. Install it, or pass --skip-python to set up rendering only."
  warn "Python 3.9+ not found; continuing without transcription (--skip-python)."
else
  echo "  python  $("$PY" --version 2>&1)"
fi

# ------------------------------------------------------------- locate skill
if [ -z "$SKILL" ]; then
  say "Locating the Flick skill"
  while IFS= read -r found; do
    [ -f "$found/scripts/setup-workspace.mjs" ] || continue
    SKILL="$found"; break
  done < <(
    find "$HOME/.claude/plugins" "$HOME/.claude/skills" "$HOME/.agents/skills" \
         "$HOME/.codex/skills" ./skills ./.claude/skills \
         -maxdepth 6 -type d -name flick 2>/dev/null | sort
  )
  [ -n "$SKILL" ] || die "Could not find an installed Flick skill. Install it, then re-run with --skill /path/to/skills/flick"
fi
SKILL="$(cd "$SKILL" && pwd)"
[ -f "$SKILL/scripts/setup-workspace.mjs" ] || die "Not a Flick skill directory: $SKILL"
echo "  skill   $SKILL"

# ---------------------------------------------------------------- workspace
say "Creating the Flick workspace"
node "$SKILL/scripts/setup-workspace.mjs" --project "$PROJECT"
PROJECT="$(cd "$PROJECT" && pwd)"

say "Installing Remotion"
( cd "$PROJECT/remotion" && npm install --no-audit --no-fund )

if [ "$SKIP_BROWSER" -eq 0 ]; then
  say "Pre-downloading Remotion's headless browser"
  # Without this the first render fails: Remotion needs chrome-headless-shell,
  # and a system Chrome/Chromium will not substitute for it.
  ( cd "$PROJECT/remotion" && npx --yes remotion browser ensure )
fi

# ------------------------------------------------------- python virtualenv
if [ -n "$PY" ] && [ "$SKIP_PYTHON" -eq 0 ]; then
  say "Creating the transcription virtualenv (Whisper pulls PyTorch: ~5 GB on Linux, less on macOS)"
  "$PY" -m venv "$PROJECT/.venv"
  "$PROJECT/.venv/bin/python" -m pip install --upgrade pip
  "$PROJECT/.venv/bin/python" -m pip install openai-whisper yt-dlp

  cat > "$PROJECT/flick-env.sh" <<ENV
# Source this before running Flick's transcribe step:
#   source "$PROJECT/flick-env.sh"
# Flick resolves Python by probing 'python3' on PATH, so putting the
# virtualenv first is what makes it pick up Whisper and yt-dlp.
export PATH="$PROJECT/.venv/bin:\$PATH"
ENV
  echo "  virtualenv  $PROJECT/.venv"
  echo "  activate    source $PROJECT/flick-env.sh"
fi

# ------------------------------------------------- protect saved animations
if [ -n "$LIBRARY" ]; then
  say "Relocating the saved-animations library"
  mkdir -p "$LIBRARY"
  LIBRARY="$(cd "$LIBRARY" && pwd)"
  SAVED="$SKILL/saved-animations"

  if [ -L "$SAVED" ]; then
    echo "  already a link -> $(readlink "$SAVED")"
  elif [ -d "$SAVED" ]; then
    # Seed the user-owned copy, then replace the in-plugin directory with a
    # link to it. A plugin update removes the link, not the library; re-run
    # this script to restore it.
    cp -Rn "$SAVED/." "$LIBRARY/" 2>/dev/null || true
    rm -rf "$SAVED"
    ln -s "$LIBRARY" "$SAVED"
    echo "  library     $LIBRARY"
    echo "  linked from $SAVED"
  else
    ln -s "$LIBRARY" "$SAVED"
    echo "  library     $LIBRARY (new)"
  fi
fi

say "Flick is ready"
echo "  workspace  $PROJECT"
echo
echo "Next: run /flick in Claude Code, and give it this workspace."
echo "Verify the render path first with:  ./verify-flick.sh --skill \"$SKILL\""
