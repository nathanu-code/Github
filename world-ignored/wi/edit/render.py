"""Render World Ignored edits: one decode, one full-frame encode per preset, original audio kept.

    render(src, out_dir, texts, presets=["v9x16", "f4x5"], trim=(start, end))

Output per preset: an MP4, a JSON sidecar with layout/crop metadata, and a QC result
(see qc.py). Blurred-background "fit" mode exists only as a reviewer-requested fallback.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from .. import config
from . import banners as bn
from .analyze import analyze, probe
from .layout import best_placement, safe_rect
from .reframe import onscreen_maps, plan_crop


def _timing(duration: float, ed: dict) -> tuple[tuple[float, float], tuple[float, float], list[str]]:
    flags = []
    o_len = min(ed["opening_seconds"], 0.38 * duration)
    c_len = min(ed["closing_seconds"], 0.32 * duration)
    opening = (0.0, o_len)
    closing = (max(o_len + 0.5, duration - c_len), duration)
    if duration < 8:
        flags.append(f"short_clip: {duration:.1f}s leaves little room for banners")
    return opening, closing, flags


def _envelope(t: float, span: tuple[float, float], fade: float, hold_end: bool = False) -> float:
    a, b = span
    if t < a or t > b + 1e-6:
        return 0.0
    up = min(1.0, (t - a) / fade) if fade > 0 and a > 0 else 1.0
    down = 1.0 if hold_end else min(1.0, (b - t) / fade) if fade > 0 else 1.0
    return max(0.0, min(up, down))


class _Overlay:
    """Pre-multiplied banner layer for fast per-frame compositing."""

    def __init__(self, banner: bn.Banner, x: int, y: int):
        rgba = np.array(banner.image.convert("RGBA")).astype(np.float32) / 255.0
        self.rgb = rgba[..., [2, 1, 0]]   # to BGR
        self.alpha = rgba[..., 3:4]
        self.x, self.y = x + 0, y
        self.h, self.w = rgba.shape[:2]

    def apply(self, frame: np.ndarray, strength: float) -> None:
        if strength <= 0:
            return
        roi = frame[self.y:self.y + self.h, self.x:self.x + self.w].astype(np.float32) / 255.0
        a = self.alpha * strength
        out = self.rgb * a + roi * (1 - a)
        frame[self.y:self.y + self.h, self.x:self.x + self.w] = np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)


def _encoder(path: Path, w: int, h: int, fps: float, crf: int) -> subprocess.Popen:
    return subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", f"{fps:.5f}",
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-g", str(int(round(fps * 2))), "-bf", "2", "-movflags", "+faststart", str(path)],
        stdin=subprocess.PIPE)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def render(src: str | Path, out_dir: str | Path, texts: dict, presets: list[str] | None = None,
           trim: tuple[float | None, float | None] = (None, None), basename: str = "edit",
           fit_mode: str = "fill") -> dict:
    """texts: headline, subhead, location_line, closing_headline, closing_subhead."""
    s = config.settings()
    ed = s["editing"]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    presets = presets or ["v9x16", "f4x5"]
    base_presets = [p for p in presets if not s["presets"][p].get("derive_from")]
    derived = [p for p in presets if s["presets"][p].get("derive_from")]
    for p in derived:
        parent = s["presets"][p]["derive_from"]
        if parent not in base_presets:
            base_presets.append(parent)

    pr = probe(src)
    start = float(trim[0] or 0.0)
    end = float(trim[1]) if trim[1] else pr.duration
    flags: list[str] = []
    if end - start > ed["max_duration_seconds"]:
        end = start + ed["max_duration_seconds"]
        flags.append(f"trimmed_to_max: source longer than {ed['max_duration_seconds']}s; set a trim to choose the segment")
    duration = end - start
    fps = min(60.0, pr.fps)
    opening, closing, tflags = _timing(duration, ed)
    flags += tflags

    an = analyze(src, start, end)
    dw, dh = an.src_size
    bt = an.burned_in_text()
    if bt["persistent"]:
        flags.append(f"WATERMARK/LOGO suspected at {bt['persistent']} (persistent on-screen text): confirm the "
                     f"rights holder and that no third-party branding remains")
    elif bt["share"] > 0.4:
        flags.append(f"burned-in text in {bt['share']:.0%} of frames: check it is not cut mid-word by the crop")

    jobs = {}
    for name in base_presets:
        W, H = s["presets"][name]["width"], s["presets"][name]["height"]
        plan = plan_crop(an, (W, H))
        grid = (54, int(round(54 * H / W)))
        onscreen = onscreen_maps(an, plan, grid)
        text_on = onscreen_maps(an, plan, grid, an.text_maps, normalise=False) if an.text_maps is not None else None
        zone = ed["safe_zones"][name]
        variants = []   # (opening banner, closing banner, lower?)
        for lower in (False, True):
            if lower and zone["lower_from"] >= 1.0:
                continue
            sr = safe_rect((W, H), zone, lower)
            bw = sr[2] - sr[0]
            try:
                variants.append((
                    bn.render_banner(bn.opening_blocks(texts["headline"], texts.get("subhead", ""), texts["location_line"]),
                                     W, bw, tuple(ed["banner_rgba"])),
                    bn.render_banner(bn.closing_blocks(texts["closing_headline"], texts.get("closing_subhead", "")),
                                     W, bw, tuple(ed["banner_rgba"])),
                    lower))
            except bn.BannerOverflow:
                if not lower:
                    raise   # text doesn't fit even the full-width banner: headline must be shortened
        oi, op = best_placement(onscreen, an.times, (W, H), [(v[0].height, v[2]) for v in variants], zone, opening,
                                text=text_on)
        ci, cp = best_placement(onscreen, an.times, (W, H), [(v[1].height, v[2]) for v in variants], zone, closing,
                                text=text_on)
        ob, cb = variants[oi][0], variants[ci][1]
        jobs[name] = dict(W=W, H=H, plan=plan, ob=ob, cb=cb, op=op, cp=cp,
                          o_over=_Overlay(ob, op.x, op.y), c_over=_Overlay(cb, cp.x, cp.y),
                          tmp=out_dir / f".{basename}_{name}_video.mp4")

    # Decode once at a size no larger than any preset needs (saves CPU on 4K sources).
    need = max(j["W"] / j["plan"].crop_w for j in jobs.values())
    scale = min(1.0, need)
    rw = int(round(dw * scale / 2) * 2)
    rh = int(round(dh * scale / 2) * 2)
    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(src),
         "-vf", f"fps={fps:.5f},scale={rw}:{rh}:flags=lanczos,setsar=1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
        stdout=subprocess.PIPE)
    encs = {n: _encoder(j["tmp"], j["W"], j["H"], fps, ed["video_crf"]) for n, j in jobs.items()}
    fb = rw * rh * 3
    k = 0
    sx, sy = rw / dw, rh / dh
    while True:
        buf = dec.stdout.read(fb)
        if len(buf) < fb:
            break
        frame = np.frombuffer(buf, np.uint8).reshape(rh, rw, 3)
        t = k / fps
        for n, j in jobs.items():
            x0, y0, w, h = j["plan"].window_at(t)
            x0, y0, w, h = x0 * sx, y0 * sy, w * sx, h * sy
            if fit_mode == "blur":
                out = _fit_blur(frame, j["W"], j["H"])
            else:
                z = j["W"] / w
                M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
                out = cv2.warpAffine(frame, M, (j["W"], j["H"]), flags=cv2.INTER_CUBIC if z > 1 else cv2.INTER_AREA,
                                     borderMode=cv2.BORDER_REPLICATE)
            j["o_over"].apply(out, _envelope(t, opening, ed["fade_seconds"]))
            j["c_over"].apply(out, _envelope(t, closing, ed["fade_seconds"], hold_end=True))
            encs[n].stdin.write(out.tobytes())
        k += 1
    dec.wait()
    for e in encs.values():
        e.stdin.close()
        e.wait()
    if k == 0:
        raise RuntimeError("no frames decoded")
    real_duration = k / fps

    results = {}
    for n, j in jobs.items():
        final = out_dir / f"{basename}_{n}.mp4"
        _mux_audio(j["tmp"], src, start, real_duration, pr.has_audio, final)
        j["tmp"].unlink(missing_ok=True)
        results[n] = _meta(n, final, j, opening, closing, real_duration, pr, flags, an.detector, fit_mode)

    for p in derived:
        parent = s["presets"][p]["derive_from"]
        W, H = s["presets"][p]["width"], s["presets"][p]["height"]
        final = out_dir / f"{basename}_{p}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", results[parent]["path"], "-vf", f"scale={W}:{H}:flags=lanczos",
                        "-c:v", "libx264", "-preset", "medium", "-crf", str(ed["video_crf"] + 2), "-pix_fmt", "yuv420p",
                        "-c:a", "copy", "-movflags", "+faststart", str(final)], check=True)
        m = dict(results[parent])
        sf = W / s["presets"][parent]["width"]
        m.update(preset=p, path=str(final), size=[W, H], sha256=sha256_file(final), derived_from=parent)
        m["opening"] = {**m["opening"], "rect": [int(v * sf) for v in m["opening"]["rect"]]}
        m["closing"] = {**m["closing"], "rect": [int(v * sf) for v in m["closing"]["rect"]]}
        results[p] = m

    for n, m in results.items():
        Path(m["path"]).with_suffix(".json").write_text(json.dumps(m, indent=1))
    return {n: results[n] for n in presets}


def _fit_blur(frame: np.ndarray, W: int, H: int) -> np.ndarray:
    """Reviewer-approved fallback only: whole frame visible over a blurred fill."""
    h, w = frame.shape[:2]
    cover = max(W / w, H / h)
    bg = cv2.resize(frame, (int(w * cover) + 2, int(h * cover) + 2))
    by, bx = (bg.shape[0] - H) // 2, (bg.shape[1] - W) // 2
    bg = cv2.GaussianBlur(bg[by:by + H, bx:bx + W], (0, 0), 30)
    bg = (bg * 0.55).astype(np.uint8)
    fit = min(W / w, H / h)
    fg = cv2.resize(frame, (int(w * fit), int(h * fit)), interpolation=cv2.INTER_AREA)
    y, x = (H - fg.shape[0]) // 2, (W - fg.shape[1]) // 2
    bg[y:y + fg.shape[0], x:x + fg.shape[1]] = fg
    return bg


def _mux_audio(video: Path, src: Path, start: float, duration: float, has_audio: bool, final: Path) -> None:
    fade_out = max(0.0, duration - 0.25)
    if has_audio:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-ss", f"{start:.3f}", "-t", f"{duration:.3f}",
               "-i", str(src), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
               "-ar", "48000", "-af", f"afade=t=in:d=0.05,afade=t=out:st={fade_out:.3f}:d=0.25",
               "-t", f"{duration:.3f}", "-movflags", "+faststart", str(final)]
    else:
        # Platforms expect an audio track; add silence (never invented sound effects).
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
               "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
               "-t", f"{duration:.3f}", "-movflags", "+faststart", str(final)]
    subprocess.run(cmd, check=True)


def _meta(name, final, j, opening, closing, duration, pr, flags, detector, fit_mode) -> dict:
    plan, op, cp = j["plan"], j["op"], j["cp"]
    return {
        "preset": name, "path": str(final), "size": [j["W"], j["H"]], "duration": round(duration, 3),
        "sha256": sha256_file(final), "fit_mode": fit_mode, "detector": detector,
        "source": {"size": list(pr.display_size), "fps": pr.fps, "has_audio": pr.has_audio},
        "crop": {"axis": plan.axis, "w": round(plan.crop_w, 1), "h": round(plan.crop_h, 1),
                 "aspect": round(plan.crop_w / plan.crop_h, 4), **plan.coverage_stats(), "flags": plan.flags},
        "opening": {"rect": list(op.rect()), "overlap": op.overlap, "overlap_peak": op.overlap_peak, "zone": op.zone,
                    "interval": [round(opening[0], 2), round(opening[1], 2)], "lines": j["ob"].lines,
                    "banner_problems": bn.check_banner(j["ob"])},
        "closing": {"rect": list(cp.rect()), "overlap": cp.overlap, "overlap_peak": cp.overlap_peak, "zone": cp.zone,
                    "interval": [round(closing[0], 2), round(closing[1], 2)], "lines": j["cb"].lines,
                    "banner_problems": bn.check_banner(j["cb"])},
        "flags": list(flags),
    }

