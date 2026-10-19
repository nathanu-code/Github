"""Banner placement: put each banner where it covers the least on-screen action.

Banners span the safe-zone width, so only their vertical position is chosen. Candidates are every
position inside the platform safe zone; the cost is the share of on-screen importance the banner
would cover during the time it is visible, plus a slight preference for the upper third (the
house style) that never outweighs covering the subject.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Placement:
    x: int
    y: int
    w: int
    h: int
    overlap: float          # share of action covered while visible (mean over samples)
    overlap_peak: float     # worst sample
    zone: str               # human-readable: top / upper / middle / lower / bottom
    cost: float = 0.0

    def rect(self):
        return self.x, self.y, self.w, self.h


def safe_rect(frame: tuple[int, int], zone: dict, lower: bool = False) -> tuple[int, int, int, int]:
    """Centred safe rectangle. lower=True gives the narrower region used below `lower_from`."""
    W, H = frame
    side = zone["side_lower"] if lower else zone["side"]
    x0 = int(round(side * W))
    x1 = W - x0
    y0 = int(round(zone["top"] * H))
    y1 = int(round(H - zone["bottom"] * H))
    if not lower and zone["lower_from"] < 1.0:
        y1 = min(y1, int(round(zone["lower_from"] * H)))
    return x0, y0, x1, y1


def best_placement(onscreen, times, frame, variants, zone, interval, prefer="upper", text=None):
    """variants: [(banner_height, lower: bool)] -> (index, Placement) with the lowest cost."""
    best = None
    for idx, (bh, lower) in enumerate(variants):
        safe = safe_rect(frame, zone, lower)
        if safe[3] - safe[1] < bh:
            continue
        p = choose_position(onscreen, times, frame, bh, safe, interval, prefer, text=text)
        if best is None or p.cost < best[1].cost:
            best = (idx, p)
    if best is None:
        raise ValueError("no banner variant fits the safe zone")
    return best


def choose_position(onscreen: np.ndarray, times: np.ndarray, frame: tuple[int, int], banner_h: int,
                    safe: tuple[int, int, int, int], interval: tuple[float, float],
                    prefer: str = "upper", avoid: tuple[int, int] | None = None,
                    text: np.ndarray | None = None) -> Placement:
    """onscreen: (n, gh, gw) importance in output-frame coordinates (fractions per sample).
    text: optional (n, gh, gw) burned-in text coverage (0..1); banners avoid sitting on top of it."""
    W, H = frame
    x0, y0, x1, y1 = safe
    n, gh, gw = onscreen.shape
    sel = (times >= interval[0] - 1e-6) & (times <= interval[1] + 1e-6)
    if not sel.any():
        sel = np.zeros_like(times, bool)
        sel[int(np.argmin(np.abs(times - interval[0])))] = True
    maps = onscreen[sel]
    col0, col1 = int(x0 / W * gw), int(np.ceil(x1 / W * gw))
    rows = maps[:, :, col0:col1].sum(axis=2)          # (k, gh) importance per row within banner width
    csum = np.concatenate([np.zeros((rows.shape[0], 1)), np.cumsum(rows, 1)], 1)
    if text is not None:
        trows = text[sel][:, :, col0:col1].mean(axis=2)  # share of banner-width row covered by text
        tsum = np.concatenate([np.zeros((trows.shape[0], 1)), np.cumsum(trows, 1)], 1)

    best = None
    max_y = y1 - banner_h
    if max_y < y0:
        raise ValueError("banner taller than the safe zone")
    step = max(4, H // 200)
    for y in range(y0, max_y + 1, step):
        r0 = y / H * gh
        r1 = (y + banner_h) / H * gh
        a, b = int(np.floor(r0)), int(np.ceil(r1))
        cov = csum[:, b] - csum[:, a]
        mean, peak = float(cov.mean()), float(cov.max())
        centre = (y + banner_h / 2) / H
        style = {"upper": abs(centre - 0.26), "lower": abs(centre - 0.70), "any": 0.0}[prefer]
        cost = mean + 0.35 * peak + 0.04 * style
        if text is not None:
            # share of the banner area that would sit on burned-in text, averaged over time
            cost += 1.2 * float(((tsum[:, b] - tsum[:, a]) / max(1, b - a)).mean())
        if avoid is not None and not (y + banner_h <= avoid[0] or y >= avoid[1]):
            cost += 0.02
        if best is None or cost < best[0]:
            best = (cost, y, mean, peak)
    cost, y, mean, peak = best
    c = (y + banner_h / 2) / H
    zone = "top" if c < 0.2 else "upper" if c < 0.4 else "middle" if c < 0.6 else "lower" if c < 0.8 else "bottom"
    return Placement(x0, int(y), x1 - x0, banner_h, round(mean, 3), round(peak, 3), zone, cost)
