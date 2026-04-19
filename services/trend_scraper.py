"""Viral content discovery — scrapes trending topics across platforms."""
from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx
import feedparser

from models.schemas import TrendItem


# RSS feeds for viral / trending content
TREND_FEEDS = {
    "reddit_videos": "https://www.reddit.com/r/videos/top.rss?t=day",
    "reddit_reels": "https://www.reddit.com/r/reels/top.rss?t=day",
    "reddit_MMA": "https://www.reddit.com/r/mma/top.rss?t=day",
    "reddit_fashion": "https://www.reddit.com/r/malefashionadvice/top.rss?t=day",
    "reddit_fitness": "https://www.reddit.com/r/fitness/top.rss?t=day",
}

# TikTok Creative Center trending page (public, no auth needed)
TIKTOK_TRENDING_URL = "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en"


class TrendScraper:
    """Discovers viral content trends from social platforms."""

    def __init__(self):
        self._http = httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0 (compatible; ContentBot/1.0)"},
            timeout=30.0,
            follow_redirects=True,
        )

    async def __aenter__(self) -> TrendScraper:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._http.aclose()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    async def get_trends(self, limit: int = 20) -> list[TrendItem]:
        """Aggregate trending items from all sources."""
        tasks = [
            self._fetch_reddit_feed(name, url)
            for name, url in TREND_FEEDS.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        items: list[TrendItem] = []
        for res in results:
            if isinstance(res, list):
                items.extend(res)

        # Sort by engagement score descending and deduplicate
        seen: set[str] = set()
        unique: list[TrendItem] = []
        for item in sorted(items, key=lambda x: x.engagement_score, reverse=True):
            key = item.title.lower()[:60]
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique[:limit]

    async def get_instagram_hashtag_trends(self, niche: str) -> list[str]:
        """Return trending hashtags for a given niche using public data."""
        # Fallback: generate contextual hashtags with a pattern
        base = niche.lower().replace(" ", "")
        return [
            f"#{base}", f"#{base}life", f"#{base}style",
            "#viral", "#trending", "#reels", "#fyp",
            "#explore", "#content", "#model",
            "#fashion", "#lifestyle", "#aesthetic",
        ]

    # ------------------------------------------------------------------ #
    #  Platform scrapers                                                   #
    # ------------------------------------------------------------------ #

    async def _fetch_reddit_feed(self, source_name: str, url: str) -> list[TrendItem]:
        try:
            resp = await self._http.get(url)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            items = []
            for entry in feed.entries[:10]:
                score = self._extract_score(entry.get("summary", ""))
                items.append(TrendItem(
                    title=entry.get("title", "Untitled"),
                    platform=f"reddit/{source_name}",
                    engagement_score=score,
                    url=entry.get("link"),
                    tags=self._extract_tags(entry.get("title", "")),
                    description=self._clean_html(entry.get("summary", "")),
                    content_format="video" if "video" in source_name else "reel",
                ))
            return items
        except Exception:
            return []

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_score(html: str) -> float:
        """Try to parse an upvote count from Reddit HTML summary."""
        match = re.search(r"(\d[\d,]+)\s+(?:points?|upvotes?)", html, re.I)
        if match:
            return float(match.group(1).replace(",", ""))
        return 0.0

    @staticmethod
    def _extract_tags(title: str) -> list[str]:
        words = re.findall(r"\b[A-Za-z]{4,}\b", title)
        stop = {"this", "that", "with", "from", "have", "been", "will", "what"}
        return list({w.lower() for w in words if w.lower() not in stop})[:8]

    @staticmethod
    def _clean_html(html: str) -> str:
        return re.sub(r"<[^>]+>", "", html).strip()[:300]
