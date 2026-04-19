"""Video production agent — generates reels and short-form video content via Higgsfield DoP."""
from __future__ import annotations

import asyncio
from pathlib import Path

from models.schemas import ContentPlan, GenerationJob, VideoSpec
from services.claude_client import ClaudeClient
from services.higgsfield import HiggsFieldClient

SYSTEM_PROMPT = """You are a viral short-form video director who writes prompts for AI video
generators (specifically Higgsfield DoP — Director of Photography model) to produce cinematic,
scroll-stopping content.

Your prompts specify:
- Camera movement: slow push-in, orbit shot, tracking, static, whip pan, crane up
- Subject action: confident walk, hair flip, glance to camera, subtle smile, turn around
- Environmental motion: light rays, bokeh particles, wind in hair, crowd blur, leaves falling
- Color grade reference: desaturated moody, warm golden hour, cool blue cinematic, neon night
- Atmosphere: haze, anamorphic lens flare, depth-of-field rack focus, film grain

Your prompts produce videos that look like high-budget fashion/lifestyle commercials."""


class VideoProductionAgent:
    """Generates short-form video content with consistent human models via DoP."""

    def __init__(self, claude: ClaudeClient, higgsfield: HiggsFieldClient):
        self.claude = claude
        self.higgsfield = higgsfield

    async def produce_reel_batch(
        self,
        plan: ContentPlan,
        soul_id: str | None = None,
        model_image_url: str | None = None,
        output_dir: Path = Path("./output"),
        poll_interval: float = 5.0,
        dop_model: str = "dop-turbo",
    ) -> list[GenerationJob]:
        """Generate all videos in a content plan concurrently."""
        enhanced_specs = [
            self._enhance_video_spec(spec, plan)
            for spec in plan.video_specs
        ]

        if soul_id:
            # Animate the Soul ID character for each spec
            job_coros = [
                self.higgsfield.animate_character(
                    character_id=soul_id,
                    action_prompt=spec.prompt,
                    duration_seconds=spec.duration_seconds,
                    aspect_ratio=spec.aspect_ratio,
                    style=spec.style.value,
                    dop_model=dop_model,
                )
                for spec in enhanced_specs
            ]
        else:
            job_coros = [
                self.higgsfield.generate_video(
                    spec=spec,
                    reference_image_url=model_image_url,
                    dop_model=dop_model,
                )
                for spec in enhanced_specs
            ]

        jobs = await asyncio.gather(*job_coros)

        completed = await asyncio.gather(*[
            self.higgsfield.poll_job(job, poll_interval=poll_interval)
            for job in jobs
        ])

        await asyncio.gather(*[
            self.higgsfield.download_result(job, output_dir / "videos")
            for job in completed
        ])

        return list(completed)

    async def produce_single_reel(
        self,
        spec: VideoSpec,
        reference_image_url: str | None = None,
        output_dir: Path = Path("./output"),
        poll_interval: float = 5.0,
        dop_model: str = "dop-turbo",
    ) -> GenerationJob:
        """Generate a single reel from an explicit spec."""
        job = await self.higgsfield.generate_video(
            spec, reference_image_url=reference_image_url, dop_model=dop_model
        )
        completed = await self.higgsfield.poll_job(job, poll_interval=poll_interval)
        await self.higgsfield.download_result(completed, output_dir / "videos")
        return completed

    # ------------------------------------------------------------------ #
    #  Prompt enhancement                                                  #
    # ------------------------------------------------------------------ #

    def _enhance_video_spec(self, spec: VideoSpec, plan: ContentPlan) -> VideoSpec:
        """Ask Claude to upgrade the video prompt for maximum cinematic DoP impact."""
        enhanced_prompt = self.claude.complete(
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    f"Trend: {plan.trend.title}\n"
                    f"Hook text: {plan.hook_text}\n"
                    f"Model: {plan.model_spec.gender}, {plan.model_spec.age_range}, "
                    f"{plan.model_spec.style.value} style\n"
                    f"Base video prompt: {spec.prompt}\n\n"
                    f"Rewrite as a hyper-cinematic Higgsfield DoP prompt for a "
                    f"{spec.duration_seconds}s reel. Include camera movement, subject "
                    f"action, atmosphere, and color grade. "
                    f"Return ONLY the enhanced prompt, no explanation, under 120 words."
                ),
            }],
            max_tokens=200,
        )

        return VideoSpec(
            prompt=enhanced_prompt,
            aspect_ratio=spec.aspect_ratio,
            duration_seconds=spec.duration_seconds,
            style=spec.style,
            model_reference_url=spec.model_reference_url,
            motion_description=spec.motion_description,
            audio_description=spec.audio_description,
        )
