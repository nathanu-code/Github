# Flick — evaluation and score

**Verdict: 73 / 100 — adopt behind a wrapper, for GrowSales AI content. Not for client deadlines.**

Evaluated 2026-08-23 against [`Creatorberry/flick`](https://github.com/Creatorberry/flick)
@ `7b43a68` (28 commits, first commit 2026-08-15, single author, MIT).

This is not a desk review. Flick's toolchain was installed and a template was
rendered end to end on a clean machine; every claim below marked *verified* was
executed. See [Evidence](#evidence).

---

## 1. What Flick actually is

The marketing copy reads like an application. It isn't one.

Flick is a **Claude Code skill** — a ~600-line markdown workflow (`SKILL.md` plus
four step references) that instructs the *agent* to scaffold a Remotion project,
write scene components, and render them. The only executable code is **332 lines
of Node and Python** across nine small scripts that wrap `npm`, `ffmpeg`,
`whisper`, and `yt-dlp`.

The real payload is elsewhere: **7,872 lines of hand-authored Remotion TSX** in
`saved-animations/` — 13 production-grade scene templates.

This matters for how you evaluate it. Flick's quality is not the quality of its
332 lines of glue. It is the quality of its templates and its prompt discipline,
and *those are good*.

## 2. Score

| Dimension | Weight | Score | Basis |
|---|---:|---:|---|
| Does what it claims | 25% | 9/10 | Verified: real frame-driven Remotion motion, plan-gate before render |
| Output quality | 20% | 9/10 | Verified: layered depth, animated connectors, typed terminals — not a slideshow |
| Code quality & safety | 15% | 8/10 | 332 lines, no shell interpolation, input validation, no telemetry |
| Install reliability | 15% | 4/10 | Breaks out of the box on the most common modern Python setups |
| Project maturity | 10% | 3/10 | 8 days old, no tests, no CI, no releases, core closed to PRs |
| Fit for this account | 10% | 7/10 | Strong for GrowSales AI; template aesthetic misfits the cabinet brands |
| Exit cost | 5% | 10/10 | MIT, plain Remotion TSX you own, fully local, no account |

**Weighted total: 7.35/10 → 73/100.**

### Why not higher
Install reliability and maturity are both genuinely weak, and they compound: the
thing most likely to break is also the thing you cannot get fixed upstream
(§4.1, §5).

### Why not lower
The core claim is true, and independently verified. Most "AI video" tools lose
points because the output is a Ken Burns slideshow. Flick's output is real
motion graphics, and the artifacts it produces are standard Remotion components
that remain useful even if the project is abandoned tomorrow.

## 3. What holds up

- **The plan gate is real.** `SKILL.md` states an explicit gate: `flick-plan.md`
  must exist and be approved before any component is written. You are not
  burning a render to find out you hate it.
- **The output is genuinely animated.** Verified by rendering
  `connected-workflow-terminals`: 106 frames at 1080×1920, animated dotted
  connector paths, per-terminal typing, layered card depth. See
  `poster-sample.jpg` in this directory.
- **The scripts are careful.** Every subprocess uses `spawnSync(cmd, [args])` —
  arrays, never an interpolated shell string, so no command injection through a
  filename or URL. Scene names are validated against `^[a-z0-9]+(-[a-z0-9]+)*$`
  before touching the filesystem. `setup-workspace.mjs` refuses to write into a
  non-empty directory.
- **No lock-in.** MIT, no account, no upload. Workspaces are local and
  gitignored by default. Saved scenes are ordinary `.tsx`.
- **The no-background-music stance is enforced in the prompt**, and the bundled
  effects are wired to on-screen actions rather than sprinkled over everything.

## 4. Defects found

### 4.1 The installer fails on the most common modern Python setups — HIGH
`scripts/bootstrap.mjs` runs:

```js
run(python.command, [...python.prefix, '-m', 'pip', 'install', '--user', '--upgrade', 'pip']);
run(python.command, [...python.prefix, '-m', 'pip', 'install', '--user', 'openai-whisper', 'yt-dlp']);
```

There is no virtualenv. `pip install --user` fails outright on any
externally-managed Python (PEP 668) — **Homebrew Python on macOS, Ubuntu 23.04+,
Debian 12+, Fedora 38+**. That covers a large share of the target audience, and
it is the *first* thing a new user hits.

Verified both failure modes:

- On a PEP 668 Python → `error: externally-managed-environment`.
  (A marker file is present at `/usr/lib/python3.12/EXTERNALLY-MANAGED` on the
  test machine.)
- Inside a virtualenv → `ERROR: Can not perform a '--user' install. User
  site-packages are not visible in this virtualenv.`

So there is **no shell you can run `bootstrap.mjs` from that works everywhere**.
Activating a venv first — the obvious workaround — breaks it a second way.

Separately, `pip install --user --upgrade pip` mutates the user's global pip as
a side effect of installing a video tool. It should not.

**Fixed by** `install-flick.sh`, which puts Whisper and yt-dlp in a
project-local venv and puts that venv on `PATH` — Flick's `findPython()` probes
`python3` from `PATH`, so it picks the venv up with no changes to Flick itself.

### 4.2 Two templates reference sound files that are not bundled — MEDIUM
`saved-animations/page-scroll-and-title-focus` calls
`staticFile("sounds/Deepwoosh.mp3")` and `staticFile("sounds/woosh.mp3")`.
Neither exists in `assets/starter-remotion/public/sounds/` (13 files, verified by
set difference). Adapting that template without swapping those references fails
at render.

**Detected by** `verify-flick.sh`, which audits every `staticFile("sounds/…")`
reference in the library against the bundled set.

### 4.3 The reusable library lives inside the plugin directory — MEDIUM
`SKILL.md` saves approved animations to `<flick-skill>/saved-animations/` — i.e.
*inside the installed plugin*, which the plugin manager owns and replaces. The
compounding asset library is the single strongest reason to use Flick, and it is
stored in the one directory an update is entitled to overwrite. README even
recommends enabling auto-update.

**Mitigated by** `install-flick.sh --library <dir>`, which relocates the library
to a path you own and symlinks it back. An update then removes the *link*, not
the library; re-run the script to restore it.

### 4.4 The first render fails without a pre-fetched browser — LOW
Remotion needs `chrome-headless-shell`; a system Chrome or Chromium does not
substitute. On this machine the first render died with `Failed to launch the
browser process` until `remotion browser ensure` fetched its own 92 MB build.
Users who read "the first run downloads a fair amount" will read this as a
Flick bug. `install-flick.sh` pre-fetches it.

### 4.5 Library and sync hygiene — LOW
- `two-tools-to-video-frames/` and `video-to-frames/` are **byte-identical**
  (same MD5, 1,182 lines each) but occupy two catalog entries, so the agent
  weighs one template twice when matching.
- `skills/`, `.claude/skills/`, and `.agents/skills/` are meant to be identical
  copies, but `.gitignore` un-ignores `src/data/scene-spec.json` only under the
  canonical `skills/` path, so the other two committed copies lack it. **Not
  build-breaking** — `sync-scene-spec.mjs` uses `fs.cp`, which creates the
  missing parent directory (verified empirically, not assumed).
- Most templates reference private images that are not shipped (`China.png`,
  `bragcard.jpg`, `$17-claude.png`, a `graphify-github-frames/` sequence). The
  catalog README does disclose this, but only 2 of 13 templates render
  standalone.

## 5. Project risk

No tests. No CI (`.github/` holds only CODEOWNERS and a PR template). No tags or
releases — you install from `main`, whatever `main` is that day. One author,
eight days of history.

The sharpest risk is governance, not youth. **`CONTRIBUTING.md` states that
Creatorberry does not accept pull requests to the core skills, scripts, starter
project, or workflow** — only showcase examples. Every defect in §4.1–§4.4 sits
in exactly those closed areas. You cannot upstream a fix; you can file an issue
or fork.

That is a legitimate choice for a young project. It just means **the wrapper in
this directory is not a stopgap until upstream fixes it — it is the maintenance
model.** Budget for carrying it.

Flick is also a funnel: MIT and genuinely local, but the README routes idea
generation to Creatorberry's paid product. Nothing improper, and it doesn't
touch your data — worth knowing rather than worrying about.

## 6. Fit for this account

**Good fit — GrowSales AI.** The existing LinkedIn pipeline produces static
1080×1350 cards. Flick is its motion counterpart, and the template library is
built for precisely this subject matter: terminals, tool constellations,
agent-role showcases, install moments. Native 9:16 output drops into LinkedIn
video, Reels, and Shorts. The workflow is script-first, so a post that already
exists can be pasted straight in as the transcript — no video, no Whisper, and
§4.1 stops mattering.

**Poor fit — Island Home Cabinets / Grandeur Design Supply / Ke'a Cabinetry.**
Every template is dev-tool/SaaS in aesthetic — dark terminals, code, orange grid
motifs. For cabinetry and building materials the catalog is close to useless and
Flick would be building original scenes each time, which is where it is slowest
and least predictable. Those brands are better served by photography.

**The cheapest way in:** paste an existing GrowSales AI LinkedIn post as the
transcript, `--skip-python`, and render one hook scene. That path avoids the
Whisper install entirely and is the fastest honest test of whether the style
suits you.

## 7. Corrections to the source write-up

The write-up this evaluation was commissioned from is slightly stale:

| Claim | Actual |
|---|---|
| "19 commits" | 28 commits as of 2026-08-23; it moves fast |
| Codex: `npx skills add … --skill flick --skill transcript-extractor …` | `transcript-extractor` was **deleted** in `d1cd41e`. That command names a skill that no longer exists; the current README correctly lists only `--skill flick` |
| "Python 3" | `SKILL.md` requires **3.9+** |
| "The first run downloads a fair amount" | Remotion is the light half (345 MB, ~20 s). Whisper pulls PyTorch: the measured virtualenv is **5.0 GB** on Linux, where pip resolves the CUDA build (`nvidia-cublas`, `cudnn`, `nccl`, `cusolver`…) even with no GPU present. Materially smaller on macOS, which has no CUDA wheels. Budget accordingly — or skip it and paste a script |

## Evidence

Executed on Linux, Node v22.22.2, Python 3.11.15, clean workspace:

| Step | Result |
|---|---|
| `setup-workspace.mjs` | workspace + starter Remotion project created |
| `npm install` | 266 packages, 345 MB, 20 s |
| `remotion browser ensure` | 92 MB `chrome-headless-shell` (required — see §4.4) |
| `remotion render` (106 frames) | **1.2 MB MP4 in 24 s** |
| `ffprobe` | 1080×1920, 9:16, 3.58 s, h264 + aac |
| `create-poster.mjs` | `poster.jpg` extracted |
| Sound-reference audit | **2 missing** (§4.2) |
| `fs.cp` parent-dir behavior | auto-creates — §4.5 is cosmetic, not breaking |
| `install-flick.sh` (full) | exit 0; `whisper` and `yt_dlp` import from the venv |
| `findPython()` after `flick-env.sh` | resolves to `.venv/bin/python3` — the venv fix works unmodified |
| Disk cost | **5.0 GB** virtualenv + 564 MB `node_modules` (packages plus headless shell) |
| `--library` relocation | 15 templates survived a simulated plugin wipe (`rm -rf` of the skill dir) |

Reproduce with `./verify-flick.sh`.

## Recommendation

Adopt for GrowSales AI, through `install-flick.sh`. Run `verify-flick.sh` after
every `/plugin update` — the core is closed to outside fixes, so upstream
changes are the main thing that will break you, and the library you care about
lives where updates land.

Do not put it on a client deadline yet.
