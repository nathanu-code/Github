"""Automated visual/technical QC for rendered exports, plus preview frames for Slack review.

An export passes only when every hard check passes. Soft checks add review flags that are shown
in the Slack review package but don't block it on their own.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .. import config
from .analyze import probe


def _frame_at(path: str, t: float) -> np.ndarray:
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, t):.3f}", "-i", path, "-frames:v", "1",
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    return cv2.imdecode(np.frombuffer(out, np.uint8), cv2.IMREAD_COLOR)


def _has_bars(frame: np.ndarray) -> list[str]:
    """Detect letterbox/pillarbox bars: flat, dark strips along an edge."""
    h, w = frame.shape[:2]
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    k = max(4, int(0.03 * min(h, w)))
    edges = {"top": g[:k], "bottom": g[-k:], "left": g[:, :k], "right": g[:, -k:]}
    return [name for name, strip in edges.items() if strip.mean() < 14 and strip.std() < 4]


def check(meta: dict) -> dict:
    s = config.settings()
    ed = s["editing"]
    path = meta["path"]
    W, H = meta["size"]
    hard, soft = [], []

    pr = probe(path)
    if (pr.width, pr.height) != (W, H):
        hard.append(f"resolution {pr.width}x{pr.height} != {W}x{H}")
    if pr.sar not in ("1:1", "0:1", None):
        hard.append(f"non-square pixels (SAR {pr.sar})")
    if abs(pr.duration - meta["duration"]) > 0.35:
        hard.append(f"duration {pr.duration:.2f}s differs from expected {meta['duration']:.2f}s")
    if not pr.has_audio:
        hard.append("no audio track")
    if not meta["source"]["has_audio"]:
        soft.append("source had no audio; silent track added")
    dec = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "null", "-"], capture_output=True, text=True)
    if dec.returncode != 0 or dec.stderr.strip():
        hard.append(f"decode errors: {dec.stderr.strip()[:200]}")

    crop = meta["crop"]
    if meta["fit_mode"] == "fill" and abs(crop["aspect"] - W / H) > 0.005 * (W / H):
        hard.append("crop aspect differs from frame aspect (distortion)")
    if meta["fit_mode"] == "fill":
        if crop["mean"] < ed["min_crop_coverage_mean"] or crop["floor_1s"] < ed["min_crop_coverage_floor"]:
            soft.append(f"MANUAL REVIEW: full-frame crop keeps {crop['mean']:.0%} of the action on average "
                        f"(worst second {crop['floor_1s']:.0%}); essential footage may be cut")
    else:
        soft.append("blurred-background fallback used (requires reviewer approval)")
    soft += crop.get("flags", [])

    zone = ed["safe_zones"][meta.get("derived_from") or meta["preset"]]
    for key in ("opening", "closing"):
        b = meta[key]
        x, y, w, h = b["rect"]
        lower = y + h > zone["lower_from"] * H + 2
        side = (zone["side_lower"] if lower else zone["side"]) * W
        if x < side - 2 or x + w > W - side + 2 or y < zone["top"] * H - 2 or y + h > H - zone["bottom"] * H + 2:
            hard.append(f"{key} banner outside platform safe zone")
        if b["banner_problems"]:
            hard.append(f"{key} banner text: " + "; ".join(b["banner_problems"]))
        if b["overlap"] > ed["max_banner_overlap"]:
            soft.append(f"{key} banner covers {b['overlap']:.0%} of on-screen action (zone: {b['zone']})")
    o, c = meta["opening"]["interval"], meta["closing"]["interval"]
    if o[1] > c[0]:
        hard.append("opening and closing banners overlap in time")

    frames = {}
    for label, t in (("opening", min(1.5, o[1] * 0.6)), ("middle", meta["duration"] / 2),
                     ("closing", max(c[0] + 0.6, meta["duration"] - 0.8))):
        f = _frame_at(path, t)
        frames[label] = f
        if meta["fit_mode"] == "fill":
            bars = _has_bars(f)
            if bars:
                soft.append(f"{label} frame: dark flat edge at {', '.join(bars)} (check for borders)")
    result = {"passed": not hard, "hard_failures": hard, "review_flags": soft + meta.get("flags", [])}
    preview = Path(path).with_suffix(".preview.jpg")
    _contact_sheet(frames, meta, preview)
    result["preview"] = str(preview)
    return result


def _contact_sheet(frames: dict, meta: dict, out: Path, height: int = 720) -> None:
    tiles = []
    for label, f in frames.items():
        h, w = f.shape[:2]
        tile = cv2.resize(f, (int(w * height / h), height), interpolation=cv2.INTER_AREA)
        img = Image.fromarray(cv2.cvtColor(tile, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, img.width, 34], fill=(0, 0, 0))
        d.text((10, 8), f"{meta['preset']}  {label.upper()}", fill=(255, 220, 0))
        tiles.append(img)
    gap = 12
    sheet = Image.new("RGB", (sum(t.width for t in tiles) + gap * (len(tiles) + 1), height + 2 * gap), (40, 40, 40))
    x = gap
    for t in tiles:
        sheet.paste(t, (x, gap))
        x += t.width + gap
    sheet.save(out, quality=85)


def check_all(results: dict) -> dict:
    out = {}
    for name, meta in results.items():
        qc = check(meta)
        meta["qc"] = qc
        Path(meta["path"]).with_suffix(".json").write_text(json.dumps(meta, indent=1))
        out[name] = qc
    return out
