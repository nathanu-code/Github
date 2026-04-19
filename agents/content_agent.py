"""Content discovery agent — finds viral trends and builds production plans."""
from __future__ import annotations

import json

from models.schemas import ContentPlan, HumanModelSpec, TrendItem, VideoSpec, VideoStyle, AspectRatio
from services.claude_client import ClaudeClient
from services.trend_scraper import TrendScraper

SYSTEM_PROMPT = """You are a viral content strategist and creative director who specializes
in creating ultra-realistic AI-model content for Instagram Reels and TikTok.

Your job:
1. Analyze trending topics and identify which ones are best suited for photorealistic human model content.
2. Design ultra-cinematic, attention-grabbing content plans that feel authentic and native to the platform.
3. Write hooks that stop the scroll in the first 2 seconds.
4. Choose model aesthetics that match the trend's audience and vibe.

Always think: What makes someone stop scrolling? What creates an emotional reaction?
Great content = right emotion + right face + right context + irresistible hook.

Respond ONLY with valid JSON — no markdown, no explanation."""


class ContentDiscoveryAgent:
    """Finds viral trends and uses Claude to turn them into full content plans."""

    def __init__(self, claude: ClaudeClient):
        self.claude = claude

    async def discover_and_plan(
        self,
        niche: str,
        num_trends: int = 5,
        videos_per_trend: int = 3,
    ) -> list[ContentPlan]:
        """Fetch trends and produce a content plan for each one."""
        async with TrendScraper() as scraper:
            trends = await scraper.get_trends(limit=30)

        # Filter to niche-relevant trends with Claude
        relevant = self._filter_to_niche(trends, niche, top_n=num_trends)

        plans: list[ContentPlan] = []
        for trend in relevant:
            plan = self._build_plan(trend, niche, videos_per_trend)
            plans.append(plan)
        return plans

    # ------------------------------------------------------------------ #
    #  Internal                                                            #
    # ------------------------------------------------------------------ #

    def _filter_to_niche(
        self,
        trends: list[TrendItem],
        niche: str,
        top_n: int,
    ) -> list[TrendItem]:
        """Ask Claude to pick the most relevant trends for the niche."""
        trends_json = [
            {"title": t.title, "platform": t.platform, "score": t.engagement_score, "tags": t.tags}
            for t in trends
        ]
        result = self.claude.complete_json(
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    f"Niche: {niche}\n\n"
                    f"Trending items:\n{json.dumps(trends_json, indent=2)}\n\n"
                    f"Return a JSON array of the top {top_n} item TITLES (strings only) "
                    f"that are most relevant to '{niche}' and can work with photorealistic "
                    f"AI model content. Example: [\"Title A\", \"Title B\"]"
                ),
            }],
        )
        selected_titles: set[str] = {t.lower() for t in result}
        filtered = [t for t in trends if t.title.lower() in selected_titles]
        # If Claude picked nothing recognizable, fall back to top scored
        return filtered[:top_n] if filtered else trends[:top_n]

    def _build_plan(
        self,
        trend: TrendItem,
        niche: str,
        videos_per_trend: int,
    ) -> ContentPlan:
        """Ask Claude to design a full content plan for a single trend."""
        raw = self.claude.complete_json(
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"""
Trend title: {trend.title}
Platform: {trend.platform}
Tags: {', '.join(trend.tags)}
Niche: {niche}
Videos to produce: {videos_per_trend}

Design a full content plan. Return JSON matching EXACTLY this structure:
{{
  "model_spec": {{
    "gender": "female",
    "age_range": "22-27",
    "ethnicity": "Brazilian",
    "hair": "long dark wavy",
    "style": "fashion",
    "outfit_description": "...",
    "setting": "...",
    "lighting": "golden hour cinematic",
    "extra_details": "..."
  }},
  "video_specs": [
    {{
      "prompt": "...",
      "aspect_ratio": "9:16",
      "duration_seconds": 15,
      "style": "cinematic",
      "motion_description": "..."
    }}
  ],
  "hook_text": "first 2-second scroll-stopping text overlay",
  "caption": "full Instagram/TikTok caption",
  "hashtags": ["#tag1", "#tag2"],
  "posting_time": "7PM EST"
}}

Valid style values: cinematic, portrait, fashion, lifestyle, action, editorial
Valid aspect_ratio values: 9:16, 1:1, 16:9
""",
            }],
        )

        # Parse model spec
        ms = raw.get("model_spec", {})
        model_spec = HumanModelSpec(
            gender=ms.get("gender", "female"),
            age_range=ms.get("age_range", "22-27"),
            ethnicity=ms.get("ethnicity"),
            hair=ms.get("hair"),
            style=VideoStyle(ms.get("style", "portrait")),
            outfit_description=ms.get("outfit_description"),
            setting=ms.get("setting"),
            lighting=ms.get("lighting", "natural cinematic lighting"),
            extra_details=ms.get("extra_details"),
        )

        # Parse video specs
        video_specs = []
        for vs in raw.get("video_specs", []):
            try:
                ar_str = vs.get("aspect_ratio", "9:16")
                ar = AspectRatio(ar_str)
            except ValueError:
                ar = AspectRatio.PORTRAIT_9_16
            try:
                style = VideoStyle(vs.get("style", "cinematic"))
            except ValueError:
                style = VideoStyle.CINEMATIC

            video_specs.append(VideoSpec(
                prompt=vs.get("prompt", f"Ultra-cinematic video about {trend.title}"),
                aspect_ratio=ar,
                duration_seconds=min(int(vs.get("duration_seconds", 15)), 60),
                style=style,
                motion_description=vs.get("motion_description"),
            ))

        return ContentPlan(
            trend=trend,
            model_spec=model_spec,
            video_specs=video_specs[:videos_per_trend],
            hook_text=raw.get("hook_text", ""),
            caption=raw.get("caption", ""),
            hashtags=raw.get("hashtags", []),
            posting_time=raw.get("posting_time"),
        )
