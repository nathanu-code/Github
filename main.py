#!/usr/bin/env python3
"""
AI Human Models & Viral Content Agent
──────────────────────────────────────
Powered by Claude (Anthropic) + Higgsfield AI (Soul 2.0 + DoP)

Usage examples:
  python main.py run --niche "fitness lifestyle" --trends 3 --videos 3
  python main.py model --gender female --age "22-28" --style fashion
  python main.py video --prompt "cinematic walk on rooftop at sunset" --dop-model dop-standard
  python main.py trends --niche "streetwear" --limit 10
  python main.py styles
  python main.py motions
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()

from agents.orchestrator import ContentOrchestrator
from models.schemas import HumanModelSpec, VideoStyle

app = typer.Typer(
    name="ai-content-agent",
    help="Create ultra-realistic AI human models and viral video content",
    add_completion=False,
)
console = Console()


def _get_orchestrator(output_dir: str, poll_interval: float) -> ContentOrchestrator:
    return ContentOrchestrator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        higgsfield_api_key=os.getenv("HIGGSFIELD_API_KEY"),
        higgsfield_api_secret=os.getenv("HIGGSFIELD_API_SECRET"),
        output_dir=Path(output_dir),
        poll_interval=poll_interval,
    )


# ------------------------------------------------------------------ #
#  Commands                                                            #
# ------------------------------------------------------------------ #

@app.command()
def run(
    niche: str = typer.Option(..., "--niche", "-n", help="Content niche, e.g. 'fitness lifestyle'"),
    trends: int = typer.Option(3, "--trends", "-t", help="Number of viral trends to target"),
    videos: int = typer.Option(3, "--videos", "-v", help="Videos to produce per trend"),
    model_variations: int = typer.Option(2, "--model-variations", "-m"),
    dop_model: str = typer.Option("dop-turbo", "--dop-model", help="dop-turbo or dop-standard"),
    output_dir: str = typer.Option("./output", "--output", "-o"),
    poll_interval: float = typer.Option(5.0, "--poll-interval"),
    no_soul_id: bool = typer.Option(False, "--no-soul-id", help="Skip Soul ID creation"),
):
    """Run the full automated pipeline: trends → model → Soul ID → reels."""
    orch = _get_orchestrator(output_dir, poll_interval)
    results = asyncio.run(orch.run_full_pipeline(
        niche=niche,
        num_trends=trends,
        videos_per_trend=videos,
        model_variations=model_variations,
        create_soul_id=not no_soul_id,
        dop_model=dop_model,
    ))
    console.print(f"\n[bold green]Pipeline complete![/] {len(results)} content batches produced.")
    for r in results:
        s = r.summary()
        console.print(f"\n[cyan]• {s['trend']}[/]")
        console.print(f"  Hook:    {s['hook']}")
        console.print(f"  Models:  {len(s['model_images'])}")
        console.print(f"  Videos:  {len(s['videos'])}")
        console.print(f"  Soul ID: {s.get('soul_id', 'N/A')}")
        console.print(f"  Caption: {(s['caption'] or '')[:80]}...")


@app.command()
def model(
    gender: str = typer.Option("female", "--gender", "-g"),
    age: str = typer.Option("22-28", "--age", "-a"),
    style: str = typer.Option("portrait", "--style", "-s",
                               help="portrait, fashion, lifestyle, cinematic, action, editorial"),
    ethnicity: str | None = typer.Option(None, "--ethnicity", "-e"),
    hair: str | None = typer.Option(None, "--hair"),
    outfit: str | None = typer.Option(None, "--outfit"),
    setting: str | None = typer.Option(None, "--setting"),
    lighting: str = typer.Option("natural cinematic lighting", "--lighting"),
    variations: int = typer.Option(3, "--variations", "-n"),
    soul_id: str | None = typer.Option(None, "--soul-id", help="Existing Soul ID to anchor identity"),
    output_dir: str = typer.Option("./output", "--output", "-o"),
    poll_interval: float = typer.Option(5.0, "--poll-interval"),
):
    """Generate ultra-realistic human model images via Higgsfield Soul 2.0."""
    spec = HumanModelSpec(
        gender=gender,
        age_range=age,
        style=VideoStyle(style),
        ethnicity=ethnicity,
        hair=hair,
        outfit_description=outfit,
        setting=setting,
        lighting=lighting,
    )
    orch = _get_orchestrator(output_dir, poll_interval)
    jobs = asyncio.run(orch.run_custom_model(spec=spec, num_variations=variations, soul_id=soul_id))
    console.print(f"\n[bold green]Generated {len(jobs)} model images.[/]")


@app.command()
def video(
    prompt: str = typer.Option(..., "--prompt", "-p", help="Video description prompt"),
    aspect_ratio: str = typer.Option("9:16", "--aspect-ratio", "-ar",
                                      help="9:16 (reel), 1:1 (square), 16:9 (landscape)"),
    duration: int = typer.Option(15, "--duration", "-d", help="Duration in seconds"),
    style: str = typer.Option("cinematic", "--style", "-s"),
    dop_model: str = typer.Option("dop-turbo", "--dop-model", help="dop-turbo or dop-standard"),
    reference_url: str | None = typer.Option(None, "--reference-url", "-r",
                                               help="Reference model image URL"),
    output_dir: str = typer.Option("./output", "--output", "-o"),
    poll_interval: float = typer.Option(5.0, "--poll-interval"),
):
    """Generate a single video/reel from a custom prompt via Higgsfield DoP."""
    orch = _get_orchestrator(output_dir, poll_interval)
    job = asyncio.run(orch.run_custom_video(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        duration=duration,
        style=style,
        reference_image_url=reference_url,
        dop_model=dop_model,
    ))
    console.print(f"\n[bold green]Video ready →[/] {job.local_path or job.result_url}")


@app.command()
def trends(
    niche: str = typer.Option(..., "--niche", "-n"),
    limit: int = typer.Option(10, "--limit", "-l"),
):
    """Preview viral trends for a niche without generating content."""
    from services.trend_scraper import TrendScraper

    async def _run() -> None:
        async with TrendScraper() as scraper:
            items = await scraper.get_trends(limit=limit)
        console.print(f"\n[bold]Top {len(items)} trends (niche: {niche})[/]\n")
        for i, item in enumerate(items, 1):
            console.print(
                f"{i:2}. [cyan]{item.title[:60]}[/]\n"
                f"    Platform: {item.platform}  |  Score: {item.engagement_score:.0f}\n"
                f"    Tags: {', '.join(item.tags[:5])}\n"
            )

    asyncio.run(_run())


@app.command()
def styles(
    output_dir: str = typer.Option("./output", "--output"),
    poll_interval: float = typer.Option(5.0, "--poll-interval"),
):
    """List available Soul 2.0 image style presets from Higgsfield."""
    orch = _get_orchestrator(output_dir, poll_interval)
    result = asyncio.run(orch.list_styles())
    table = Table(title="Soul 2.0 Style Presets")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description")
    for s in result:
        table.add_row(str(s.get("id", "")), s.get("name", ""), s.get("description", "")[:60])
    console.print(table)


@app.command()
def motions(
    output_dir: str = typer.Option("./output", "--output"),
    poll_interval: float = typer.Option(5.0, "--poll-interval"),
):
    """List available DoP motion presets from Higgsfield."""
    orch = _get_orchestrator(output_dir, poll_interval)
    result = asyncio.run(orch.list_motions())
    table = Table(title="DoP Motion Presets")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description")
    for m in result:
        table.add_row(str(m.get("id", "")), m.get("name", ""), m.get("description", "")[:60])
    console.print(table)


if __name__ == "__main__":
    app()
