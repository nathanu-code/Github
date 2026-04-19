"""Master orchestrator — coordinates all agents into a full automated pipeline."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from agents.content_agent import ContentDiscoveryAgent
from agents.model_agent import ModelCreationAgent
from agents.video_agent import VideoProductionAgent
from models.schemas import ContentPlan, GenerationJob, HumanModelSpec, VideoSpec, AspectRatio, VideoStyle
from services.claude_client import ClaudeClient
from services.higgsfield import HiggsFieldClient

console = Console()


@dataclass
class PipelineResult:
    plan: ContentPlan
    model_jobs: list[GenerationJob]
    video_jobs: list[GenerationJob]
    soul_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "trend": self.plan.trend.title,
            "hook": self.plan.hook_text,
            "caption": self.plan.caption,
            "hashtags": self.plan.hashtags,
            "posting_time": self.plan.posting_time,
            "model_images": [j.local_path for j in self.model_jobs if j.local_path],
            "videos": [j.local_path for j in self.video_jobs if j.local_path],
            "soul_id": self.soul_id,
        }


class ContentOrchestrator:
    """
    Full pipeline:
      1. Discover viral trends
      2. Design content plan (Claude)
      3. Generate photorealistic model via Soul 2.0 (Higgsfield)
      4. Register Soul ID for character consistency
      5. Generate video reels via DoP (Higgsfield)
      6. Save manifest
    """

    def __init__(
        self,
        anthropic_api_key: str | None = None,
        higgsfield_api_key: str | None = None,
        higgsfield_api_secret: str | None = None,
        output_dir: Path = Path("./output"),
        poll_interval: float = 5.0,
        max_concurrent_plans: int = 2,
    ):
        self.output_dir = output_dir
        self.poll_interval = poll_interval
        self.max_concurrent_plans = max_concurrent_plans
        self._claude = ClaudeClient(api_key=anthropic_api_key)
        self._hf_key = higgsfield_api_key
        self._hf_secret = higgsfield_api_secret

    def _make_hf_client(self) -> HiggsFieldClient:
        return HiggsFieldClient(api_key=self._hf_key, api_secret=self._hf_secret)

    # ------------------------------------------------------------------ #
    #  Main entry points                                                   #
    # ------------------------------------------------------------------ #

    async def run_full_pipeline(
        self,
        niche: str,
        num_trends: int = 3,
        videos_per_trend: int = 3,
        model_variations: int = 2,
        create_soul_id: bool = True,
        dop_model: str = "dop-turbo",
    ) -> list[PipelineResult]:
        """Discover trends, create models, produce reels — fully automated."""
        console.rule("[bold cyan]AI Content Production Pipeline")

        # Step 1: Discover trends & build plans
        with console.status("[bold green]Discovering viral trends and designing plans..."):
            content_agent = ContentDiscoveryAgent(self._claude)
            plans = await content_agent.discover_and_plan(
                niche=niche,
                num_trends=num_trends,
                videos_per_trend=videos_per_trend,
            )
        console.print(f"[green]✓[/] {len(plans)} content plans designed for niche: [bold]{niche}[/]")
        self._print_plan_table(plans)

        # Step 2: Execute plans concurrently (with cap)
        sem = asyncio.Semaphore(self.max_concurrent_plans)
        async with self._make_hf_client() as hf:
            model_agent = ModelCreationAgent(self._claude, hf)
            video_agent = VideoProductionAgent(self._claude, hf)

            tasks = [
                self._execute_plan(plan, model_agent, video_agent, sem,
                                   model_variations, create_soul_id, dop_model)
                for plan in plans
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        successful: list[PipelineResult] = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                console.print(f"[red]✗[/] Plan {i+1} failed: {r}")
            else:
                successful.append(r)  # type: ignore[arg-type]

        self._save_manifest(successful, niche)
        console.rule(f"[bold green]Done — {len(successful)}/{len(plans)} plans completed")
        return successful

    async def run_custom_model(
        self,
        spec: HumanModelSpec,
        num_variations: int = 3,
        soul_id: str | None = None,
    ) -> list[GenerationJob]:
        """Generate custom model images without the trend pipeline."""
        async with self._make_hf_client() as hf:
            model_agent = ModelCreationAgent(self._claude, hf)
            with console.status("[bold green]Generating model images via Soul 2.0..."):
                jobs = await model_agent.create_model(
                    spec=spec,
                    output_dir=self.output_dir,
                    num_variations=num_variations,
                    poll_interval=self.poll_interval,
                    soul_id=soul_id,
                )
        console.print(f"[green]✓[/] Generated {len(jobs)} model images")
        for j in jobs:
            console.print(f"  → {j.local_path or j.result_url}")
        return jobs

    async def run_custom_video(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        duration: int = 15,
        style: str = "cinematic",
        reference_image_url: str | None = None,
        dop_model: str = "dop-turbo",
    ) -> GenerationJob:
        """Generate a single video from a custom prompt via DoP."""
        try:
            style_enum = VideoStyle(style)
        except ValueError:
            style_enum = VideoStyle.CINEMATIC

        spec = VideoSpec(
            prompt=prompt,
            aspect_ratio=AspectRatio(aspect_ratio),
            duration_seconds=duration,
            style=style_enum,
        )
        async with self._make_hf_client() as hf:
            video_agent = VideoProductionAgent(self._claude, hf)
            with console.status("[bold green]Generating video via DoP..."):
                job = await video_agent.produce_single_reel(
                    spec=spec,
                    reference_image_url=reference_image_url,
                    output_dir=self.output_dir,
                    poll_interval=self.poll_interval,
                    dop_model=dop_model,
                )
        console.print(f"[green]✓[/] Video saved → {job.local_path or job.result_url}")
        return job

    async def list_styles(self) -> list[dict]:
        """List available Soul 2.0 style presets."""
        async with self._make_hf_client() as hf:
            return await hf.list_soul_styles()

    async def list_motions(self) -> list[dict]:
        """List available DoP motion presets."""
        async with self._make_hf_client() as hf:
            return await hf.list_motions()

    # ------------------------------------------------------------------ #
    #  Internal plan execution                                            #
    # ------------------------------------------------------------------ #

    async def _execute_plan(
        self,
        plan: ContentPlan,
        model_agent: ModelCreationAgent,
        video_agent: VideoProductionAgent,
        sem: asyncio.Semaphore,
        model_variations: int,
        create_soul_id: bool,
        dop_model: str,
    ) -> PipelineResult:
        async with sem:
            plan_dir = self.output_dir / self._slugify(plan.trend.title)

            console.print(f"[cyan]→[/] Generating model for: [bold]{plan.trend.title}[/]")
            model_jobs = await model_agent.create_model(
                spec=plan.model_spec,
                output_dir=plan_dir,
                num_variations=model_variations,
                poll_interval=self.poll_interval,
            )

            soul_id: str | None = None
            model_image_url: str | None = model_jobs[0].result_url if model_jobs else None

            if create_soul_id and model_jobs:
                console.print(f"[cyan]→[/] Creating Soul ID for consistent character...")
                char = await model_agent.create_soul_id(
                    name=self._slugify(plan.trend.title),
                    spec=plan.model_spec,
                    seed_image_jobs=model_jobs,
                )
                soul_id = char.get("id") or char.get("character_id") or char.get("custom_reference_id")

            console.print(f"[cyan]→[/] Generating {len(plan.video_specs)} reels...")
            video_jobs = await video_agent.produce_reel_batch(
                plan=plan,
                soul_id=soul_id,
                model_image_url=model_image_url,
                output_dir=plan_dir,
                poll_interval=self.poll_interval,
                dop_model=dop_model,
            )

            console.print(f"[green]✓[/] Completed: [bold]{plan.trend.title}[/]")
            return PipelineResult(
                plan=plan,
                model_jobs=model_jobs,
                video_jobs=video_jobs,
                soul_id=soul_id,
            )

    # ------------------------------------------------------------------ #
    #  Output / reporting                                                  #
    # ------------------------------------------------------------------ #

    def _save_manifest(self, results: list[PipelineResult], niche: str) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "niche": niche,
            "total_plans": len(results),
            "content": [r.summary() for r in results],
        }
        path = self.output_dir / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2))
        console.print(f"\n[bold]Manifest →[/] {path}")

    @staticmethod
    def _print_plan_table(plans: list[ContentPlan]) -> None:
        table = Table(title="Content Plans", show_lines=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Trend", style="cyan", max_width=45)
        table.add_column("Model", style="green", max_width=30)
        table.add_column("Videos", justify="center", width=7)
        table.add_column("Hook", style="yellow", max_width=40)
        for i, p in enumerate(plans, 1):
            table.add_row(
                str(i),
                p.trend.title[:45],
                f"{p.model_spec.gender} {p.model_spec.age_range} {p.model_spec.style.value}",
                str(len(p.video_specs)),
                p.hook_text[:40],
            )
        console.print(table)

    @staticmethod
    def _slugify(text: str) -> str:
        import re
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]
