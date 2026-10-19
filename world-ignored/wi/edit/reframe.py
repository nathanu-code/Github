"""Full-frame reframing: choose a crop window per moment so footage fills the target frame.

The crop always has exactly the target aspect ratio (no stretching) and the largest possible size
(no zoom beyond what the ratio change requires). Its position follows the action:

1. For each sampled frame, score every crop position by how much of the importance map it keeps.
2. Dynamic programming picks a path that keeps the most action while penalising camera movement.
3. The path is smoothed (second-order) so pans look like a steady operator, not a jittery tracker.
4. If a single fixed crop is nearly as good, it is used instead (no movement at all).

Coverage (share of action kept on screen) is reported per sample so QC can flag crops that would
cut essential footage.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .analyze import Analysis


@dataclass
class CropPlan:
    target: tuple[int, int]           # output width, height
    src_size: tuple[int, int]         # display width, height of source
    crop_w: float
    crop_h: float
    axis: str                         # "x" (pan horizontally), "y" (pan vertically) or "none"
    times: np.ndarray
    centers: np.ndarray               # crop centre along `axis`, source pixels, per sample
    coverage: np.ndarray              # share of importance kept, per sample
    mode: str = "static"              # "static" or "tracking"
    flags: list[str] = field(default_factory=list)

    def window_at(self, t: float) -> tuple[float, float, float, float]:
        """Crop (x0, y0, w, h) in source pixels at time t (linear interpolation between samples)."""
        sw, sh = self.src_size
        if self.axis == "none":
            return (sw - self.crop_w) / 2, (sh - self.crop_h) / 2, self.crop_w, self.crop_h
        c = float(np.interp(t, self.times, self.centers))
        if self.axis == "x":
            x0 = float(np.clip(c - self.crop_w / 2, 0, sw - self.crop_w))
            return x0, (sh - self.crop_h) / 2, self.crop_w, self.crop_h
        y0 = float(np.clip(c - self.crop_h / 2, 0, sh - self.crop_h))
        return (sw - self.crop_w) / 2, y0, self.crop_w, self.crop_h

    @property
    def upscale(self) -> float:
        return self.target[0] / self.crop_w

    def coverage_stats(self, fps: float = 3.0) -> dict:
        cov = self.coverage
        win = max(1, int(round(fps)))
        rolling = np.convolve(cov, np.ones(win) / win, mode="valid") if len(cov) >= win else cov
        return {"mean": round(float(cov.mean()), 3), "floor_1s": round(float(rolling.min()), 3),
                "mode": self.mode, "upscale": round(self.upscale, 2)}


def _smooth(path: np.ndarray, weights: np.ndarray, lam1: float, lam2: float) -> np.ndarray:
    n = len(path)
    if n < 3:
        return path.copy()
    W = np.diag(weights)
    D1 = np.diff(np.eye(n), 1, axis=0)
    D2 = np.diff(np.eye(n), 2, axis=0)
    A = W + lam1 * D1.T @ D1 + lam2 * D2.T @ D2
    return np.linalg.solve(A, W @ path)


def plan_crop(an: Analysis, target: tuple[int, int], sample_fps: float = 3.0,
              move_penalty: float = 0.9, static_tolerance: float = 0.025) -> CropPlan:
    tw, th = target
    sw, sh = an.src_size
    ta, sa = tw / th, sw / sh
    n, mh, mw = an.maps.shape

    if abs(sa - ta) / ta < 0.01:
        return CropPlan(target, (sw, sh), sw, sh, "none", an.times, np.zeros(n), np.ones(n), "static")

    if sa > ta:   # source wider than target: full height, pan horizontally
        axis, crop_w, crop_h = "x", sh * ta, float(sh)
        profiles = an.maps.sum(axis=1)                    # (n, mw)
        cells, src_len, crop_len = mw, sw, crop_w
    else:         # source taller than target: full width, pan vertically
        axis, crop_w, crop_h = "y", float(sw), sw / ta
        profiles = an.maps.sum(axis=2)                    # (n, mh)
        cells, src_len, crop_len = mh, sh, crop_h

    win = crop_len / src_len * cells                      # window length in map cells (fractional)
    wi = int(np.floor(win))
    frac = win - wi
    # coverage[i, p] for window starting at cell p (fractional edge handled linearly)
    csum = np.concatenate([np.zeros((n, 1)), np.cumsum(profiles, axis=1)], axis=1)
    positions = np.arange(0, cells - wi + (1 if frac == 0 else 0))
    positions = positions[positions + win <= cells + 1e-6]
    cov = np.empty((n, len(positions)))
    for j, p in enumerate(positions):
        full = csum[:, p + wi] - csum[:, p]
        part = profiles[:, p + wi] * frac if (frac > 0 and p + wi < cells) else 0
        cov[:, j] = full + part
    cost = 1.0 - cov

    # Viterbi over positions with an |Δp| movement penalty (per cell, scaled to the map size)
    P = len(positions)
    pen = move_penalty / cells
    dist = np.abs(positions[:, None] - positions[None, :]) * pen
    max_step = max(1, int(round(cells * 0.06)))           # ~6% of frame per sample at most
    dist[np.abs(positions[:, None] - positions[None, :]) > max_step] = 1e6
    acc = cost[0].copy()
    back = np.zeros((n, P), dtype=int)
    for i in range(1, n):
        tot = acc[:, None] + dist                         # from q (rows) to p (cols)
        back[i] = tot.argmin(0)
        acc = tot.min(0) + cost[i]
    path = np.empty(n, dtype=int)
    path[-1] = int(acc.argmin())
    for i in range(n - 1, 0, -1):
        path[i - 1] = back[i, path[i]]

    def to_center(pos_cells: np.ndarray) -> np.ndarray:
        return (pos_cells + win / 2) / cells * src_len

    def coverage_for(centers: np.ndarray) -> np.ndarray:
        start_cells = centers / src_len * cells - win / 2
        out = np.empty(n)
        for i, s in enumerate(start_cells):
            s = float(np.clip(s, 0, cells - win))
            out[i] = np.interp(s, positions, cov[i]) if P > 1 else cov[i, 0]
        return out

    # confidence: samples with a clear peak pull the path harder
    peak = cov.max(1) - np.median(cov, 1)
    weights = 0.2 + peak / (peak.max() + 1e-9)
    dyn = _smooth(positions[path].astype(float), weights, lam1=4.0 * sample_fps, lam2=40.0 * sample_fps)
    dyn = np.clip(dyn, 0, cells - win)
    dyn_centers = to_center(dyn)
    dyn_cov = coverage_for(dyn_centers)

    best_static = int(cov.mean(0).argmax())
    st_centers = np.full(n, to_center(np.array([positions[best_static]], float))[0])
    st_cov = cov[:, best_static]

    if st_cov.mean() >= dyn_cov.mean() - static_tolerance and np.percentile(st_cov, 10) >= np.percentile(dyn_cov, 10) - 0.05:
        plan = CropPlan(target, (sw, sh), crop_w, crop_h, axis, an.times, st_centers, st_cov, "static")
    else:
        plan = CropPlan(target, (sw, sh), crop_w, crop_h, axis, an.times, dyn_centers, dyn_cov, "tracking")
    if plan.upscale > 2.0:
        plan.flags.append(f"low_resolution: crop is upscaled {plan.upscale:.1f}x")
    return plan


def onscreen_maps(an: Analysis, plan: CropPlan, grid: tuple[int, int], maps: np.ndarray | None = None,
                  normalise: bool = True) -> np.ndarray:
    """Importance (or another per-sample map, e.g. burned-in text) as it appears in the output frame,
    per sample, on a gw x gh grid. With normalise=True values are fractions of the on-screen total.
    """
    import cv2
    gw, gh = grid
    maps = an.maps if maps is None else maps
    n, mh, mw = maps.shape
    sw, sh = plan.src_size
    out = np.empty((n, gh, gw), np.float32)
    for i, t in enumerate(an.times):
        x0, y0, w, h = plan.window_at(float(t))
        c0, c1 = x0 / sw * mw, (x0 + w) / sw * mw
        r0, r1 = y0 / sh * mh, (y0 + h) / sh * mh
        M = np.float32([[(c1 - c0) / gw, 0, c0], [0, (r1 - r0) / gh, r0]])
        sub = cv2.warpAffine(maps[i], M, (gw, gh), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT)
        if normalise:
            s = sub.sum()
            out[i] = sub / s if s > 0 else 1.0 / sub.size
        else:
            out[i] = sub
    return out
