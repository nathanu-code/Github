"""World Ignored text banners: bold white uppercase text on a dark semi-transparent block.

Opening banner:  HEADLINE (largest) / optional SUBHEAD / LOCATION | DATE (small)
Closing banner:  SAFETY HEADLINE / safety instruction

Text is auto-sized and balanced across lines so every line fits inside the banner with the
configured padding. `render_banner` returns the image plus the measured boxes, which QC re-checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from .. import config


class BannerOverflow(ValueError):
    """Text cannot fit the banner even at minimum size; the headline must be shortened."""


@dataclass
class Banner:
    image: Image.Image                # RGBA, banner-sized
    width: int
    height: int
    text_boxes: list[tuple[int, int, int, int]]   # in banner coordinates
    padding: tuple[int, int]          # (x, y) minimum inner padding used
    lines: list[str]


@lru_cache(maxsize=64)
def _font(size: int, weight: str) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(config.asset(config.settings()["editing"]["font"])), size)
    try:
        f.set_variation_by_name(weight)
    except (OSError, ValueError):
        pass
    return f


def _text_w(text: str, font) -> int:
    l, _, r, _ = font.getbbox(text)
    return r - l


def _balanced_wrap(words: list[str], n_lines: int, font) -> list[str]:
    """Split words into n_lines minimising the widest line."""
    if n_lines <= 1 or len(words) <= 1:
        return [" ".join(words)]
    best, best_w = None, float("inf")

    def rec(start, k, acc):
        nonlocal best, best_w
        if k == 1:
            lines = acc + [" ".join(words[start:])]
            w = max(_text_w(x, font) for x in lines)
            if w < best_w:
                best, best_w = lines, w
            return
        for end in range(start + 1, len(words) - k + 2):
            rec(end, k - 1, acc + [" ".join(words[start:end])])

    rec(0, min(n_lines, len(words)), [])
    return best


def fit_lines(text: str, max_w: int, max_size: int, min_size: int, weight: str, max_lines: int = 3):
    """Font size and line split for `text` within max_w.

    Prefers fewer lines: an extra line is used only when it allows a noticeably larger size
    (more than ~18% bigger) than the best fewer-line option.
    """
    words = text.upper().split()
    best_per_n = []
    for n in range(1, min(max_lines, len(words)) + 1):
        for size in range(max_size, min_size - 1, -2):
            font = _font(size, weight)
            lines = _balanced_wrap(words, n, font)
            if max(_text_w(x, font) for x in lines) <= max_w:
                best_per_n.append((size, lines))
                break
    if not best_per_n:
        raise BannerOverflow(f"'{text[:60]}' does not fit in {max_lines} line(s) at {min_size}px; shorten it")
    largest = max(s for s, _ in best_per_n)
    for size, lines in best_per_n:            # ordered by line count
        if size >= largest / 1.18:
            return size, lines
    return best_per_n[-1]


def render_banner(blocks: list[dict], frame_w: int, banner_w: int, rgba=(12, 12, 12, 190),
                  pad_x: int | None = None, pad_y: int | None = None) -> Banner:
    """blocks: [{"text":..., "max":px, "min":px, "weight":..., "max_lines":n, "gap_before":em}]"""
    scale = frame_w / 1080
    pad_x = pad_x if pad_x is not None else int(46 * scale)
    pad_y = pad_y if pad_y is not None else int(30 * scale)
    inner_w = banner_w - 2 * pad_x

    laid = []   # (font, line, gap_before_px)
    for b in blocks:
        if not b.get("text"):
            continue
        size, lines = fit_lines(b["text"], inner_w, int(b["max"] * scale), int(b["min"] * scale),
                                b.get("weight", "ExtraBold"), b.get("max_lines", 3))
        font = _font(size, b.get("weight", "ExtraBold"))
        for k, line in enumerate(lines):
            gap = int(b.get("gap_before", 0.0) * size) if k == 0 and laid else int(size * 0.16)
            laid.append((font, line, gap if laid else 0))

    # measure using real glyph boxes; place by ascender line so caps align consistently
    heights = []
    for font, line, _ in laid:
        asc, desc = font.getmetrics()
        _, top, _, bottom = font.getbbox(line, anchor="ls")
        heights.append((top, bottom))
    content_h = 0
    for (font, _, gap), (top, bottom) in zip(laid, heights):
        content_h += gap + (bottom - top)
    banner_h = content_h + 2 * pad_y

    img = Image.new("RGBA", (banner_w, banner_h), tuple(rgba))
    draw = ImageDraw.Draw(img)
    y = pad_y
    boxes = []
    for (font, line, gap), (top, bottom) in zip(laid, heights):
        y += gap
        baseline = y - top
        w = _text_w(line, font)
        x = (banner_w - w) // 2
        l, t, r, bt = draw.textbbox((x, baseline), line, font=font, anchor="ls")
        draw.text((x, baseline), line, font=font, fill=(255, 255, 255, 255), anchor="ls")
        boxes.append((l, t, r, bt))
        y += bottom - top
    return Banner(img, banner_w, banner_h, boxes, (pad_x, pad_y), [ln for _, ln, _ in laid])


def opening_blocks(headline: str, subhead: str, location_line: str) -> list[dict]:
    return [
        {"text": headline, "max": 78, "min": 46, "weight": "ExtraBold", "max_lines": 2},
        {"text": subhead, "max": 54, "min": 38, "weight": "Bold", "max_lines": 2, "gap_before": 0.18},
        {"text": location_line, "max": 36, "min": 28, "weight": "Bold", "max_lines": 1, "gap_before": 0.9},
    ]


def closing_blocks(headline: str, subhead: str) -> list[dict]:
    return [
        {"text": headline, "max": 62, "min": 40, "weight": "ExtraBold", "max_lines": 2},
        {"text": subhead, "max": 40, "min": 30, "weight": "Bold", "max_lines": 2, "gap_before": 0.6},
    ]


def check_banner(b: Banner, min_pad_ratio: float = 0.75) -> list[str]:
    """Every text box inside the banner with at least ~75% of nominal padding; no overlaps."""
    problems = []
    px, py = b.padding
    for i, (l, t, r, bt) in enumerate(b.text_boxes):
        if l < px * min_pad_ratio or r > b.width - px * min_pad_ratio:
            problems.append(f"line {i+1} too close to banner side")
        if t < py * min_pad_ratio or bt > b.height - py * min_pad_ratio:
            problems.append(f"line {i+1} too close to banner top/bottom")
    for i in range(len(b.text_boxes) - 1):
        if b.text_boxes[i][3] > b.text_boxes[i + 1][1]:
            problems.append(f"lines {i+1} and {i+2} overlap")
    return problems
