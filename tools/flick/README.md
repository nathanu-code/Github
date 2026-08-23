# Flick — evaluation and hardened setup

Evaluation of [Creatorberry/flick](https://github.com/Creatorberry/flick), an
open-source Claude Code skill that turns a video, link, or transcript into
scene-by-scene Remotion animations.

**Score: 73/100 — adopt behind a wrapper, for GrowSales AI content. Not for
client deadlines.** Full reasoning in [EVALUATION.md](EVALUATION.md).

| File | What it is |
|---|---|
| [`EVALUATION.md`](EVALUATION.md) | Scored analysis, defects found, fit assessment |
| [`install-flick.sh`](install-flick.sh) | Installer that works around Flick's broken Python bootstrap |
| [`verify-flick.sh`](verify-flick.sh) | Smoke test: renders a template end to end, audits the library |
| `poster-sample.jpg` | A frame from a scene rendered during the evaluation |

## Why a wrapper

Flick's own `bootstrap.mjs` installs Whisper and yt-dlp with `pip install
--user` and no virtualenv. That fails on Homebrew Python, Ubuntu 23.04+, Debian
12+, and Fedora 38+ (PEP 668), and it fails a second, different way inside a
virtualenv — so there is no shell it reliably runs from. Its core is also closed
to outside pull requests, so this wrapper is the maintenance model, not a
stopgap. See EVALUATION.md §4.1 and §5.

`install-flick.sh` additionally pre-fetches Remotion's `chrome-headless-shell`
(without it the first render fails) and can move Flick's saved-animations
library somewhere a plugin update cannot overwrite it.

## Use

Install the skill first:

```text
/plugin marketplace add Creatorberry/flick
/plugin install flick@flick
```

Then set it up and confirm it renders on this machine:

```bash
./install-flick.sh --project ~/flick-output --library ~/flick-animations
./verify-flick.sh
```

`verify-flick.sh` exits non-zero if anything fails. Re-run it after every
`/plugin update`.

**Script-only path (recommended first run).** Pasting a script skips Whisper
entirely — no PyTorch, no transcription, and the whole class of install problems
above disappears:

```bash
./install-flick.sh --project ~/flick-output --skip-python
```

Then run `/flick` and paste the script as the transcript.

## Options

`install-flick.sh`

| Flag | Effect |
|---|---|
| `--project DIR` | Workspace to create (default `flick-output`) |
| `--skill DIR` | Path to `skills/flick`; auto-detected if omitted |
| `--library DIR` | Relocate saved-animations here and symlink it back |
| `--skip-python` | Rendering only — no Whisper, no transcription |
| `--skip-browser` | Skip the `chrome-headless-shell` download |

`verify-flick.sh` takes `--skill DIR`, `--workdir DIR`, and `--keep`.

Whisper is the expensive half: the virtualenv measures **5.0 GB** on Linux (pip
resolves the CUDA build of PyTorch even with no GPU). `--skip-python` avoids it
entirely.
