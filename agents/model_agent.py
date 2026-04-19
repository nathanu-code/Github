"""Human model creation agent — generates photorealistic AI models via Higgsfield Soul 2.0."""
from __future__ import annotations

import asyncio
from pathlib import Path

from models.schemas import GenerationJob, HumanModelSpec
from services.claude_client import ClaudeClient
from services.higgsfield import HiggsFieldClient

SYSTEM_PROMPT = """You are a world-class AI photography director who creates the most
photorealistic, believable human model images using AI generation prompts.

Your prompts produce images that look like they were shot by top fashion/commercial photographers.
They include: specific lighting setups, lens choices, film characteristics, skin texture details,
micro-expression guidance, environmental context, and color grading direction.

Always push for maximum realism. The goal is indistinguishable from a real photograph."""


class ModelCreationAgent:
    """Creates ultra-realistic human model images using Higgsfield Soul 2.0 + Claude."""

    def __init__(self, claude: ClaudeClient, higgsfield: HiggsFieldClient):
        self.claude = claude
        self.higgsfield = higgsfield

    async def create_model(
        self,
        spec: HumanModelSpec,
        output_dir: Path,
        num_variations: int = 3,
        poll_interval: float = 5.0,
        soul_id: str | None = None,
        style_id: str | None = None,
    ) -> list[GenerationJob]:
        """Generate `num_variations` model images from a spec via Soul 2.0."""
        enhanced_prompt = self._enhance_prompt(spec.to_prompt(), spec)

        orientation = {
            "portrait": "portrait",
            "fashion": "portrait",
            "lifestyle": "portrait",
            "cinematic": "landscape",
            "action": "landscape",
            "editorial": "portrait",
        }.get(spec.style.value, "portrait")

        jobs = await asyncio.gather(*[
            self.higgsfield.generate_image(
                prompt=enhanced_prompt,
                quality="1080p",
                orientation=orientation,
                custom_reference_id=soul_id,
                style_id=style_id,
                seed=i * 1000,
            )
            for i in range(num_variations)
        ])

        completed = await asyncio.gather(*[
            self.higgsfield.poll_job(job, poll_interval=poll_interval)
            for job in jobs
        ])

        await asyncio.gather(*[
            self.higgsfield.download_result(job, output_dir / "models")
            for job in completed
        ])

        return list(completed)

    async def create_soul_id(
        self,
        name: str,
        spec: HumanModelSpec,
        seed_image_jobs: list[GenerationJob] | None = None,
    ) -> dict:
        """Register a Soul ID (persistent character) in Higgsfield.

        Costs ~40 credits. Provide up to 5 reference image URLs for best results.
        """
        reference_urls = [
            j.result_url for j in (seed_image_jobs or []) if j.result_url
        ]
        return await self.higgsfield.create_character(
            name=name,
            appearance_prompt=spec.to_prompt(),
            reference_images=reference_urls[:5],
        )

    async def list_available_styles(self) -> list[dict]:
        """Fetch available Soul 2.0 style presets from Higgsfield."""
        return await self.higgsfield.list_soul_styles()

    # ------------------------------------------------------------------ #
    #  Prompt enhancement                                                  #
    # ------------------------------------------------------------------ #

    def _enhance_prompt(self, base_prompt: str, spec: HumanModelSpec) -> str:
        """Use Claude to add professional photography detail to the Soul 2.0 prompt."""
        style_guidance = {
            "portrait": "intimate close-up, 85mm portrait lens, shallow depth of field f/1.4",
            "fashion": "full-body editorial, 50mm, high-end Vogue magazine shoot, bold pose",
            "lifestyle": "candid natural light, 35mm wide, documentary authentic feel",
            "cinematic": "dramatic anamorphic, lens flare, Hollywood movie still, 2.39:1",
            "action": "dynamic frozen motion, 1/1000s shutter, athletic energy",
            "editorial": "graphic shadows, high contrast, bold composition, art-directed",
        }.get(spec.style.value, "professional studio lighting, commercial photography")

        return self.claude.complete(
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    f"Enhance this Soul 2.0 AI image prompt for maximum photorealism:\n"
                    f"Base: {base_prompt}\n"
                    f"Style: {style_guidance}\n\n"
                    f"Return ONLY the enhanced prompt text, nothing else. "
                    f"Under 200 words. Hyper-specific, cinematic, believable."
                ),
            }],
            max_tokens=300,
        )
