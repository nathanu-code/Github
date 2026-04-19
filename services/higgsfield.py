"""Higgsfield AI API client — photorealistic human models and video generation.

Auth: two headers hf-api-key + hf-secret (not Bearer).
Base: https://platform.higgsfield.ai
Docs: https://cloud.higgsfield.ai
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from models.schemas import GenerationJob, VideoSpec, AspectRatio

HIGGSFIELD_BASE_URL = os.getenv("HIGGSFIELD_BASE_URL", "https://platform.higgsfield.ai")

# Resolution presets for Soul 2.0 image generation
RESOLUTION_PRESETS = {
    "portrait": "PORTRAIT_1072x1920",
    "square": "SQUARE_1536x1536",
    "landscape": "LANDSCAPE_1920x1072",
}


class HiggsFieldError(Exception):
    pass


class HiggsFieldClient:
    """Async client for the Higgsfield AI platform API."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
    ):
        # Support combined "key:secret" env var (HF_KEY) or separate keys
        combined = os.getenv("HF_KEY", "")
        if combined and ":" in combined:
            parts = combined.split(":", 1)
            self.api_key = api_key or parts[0]
            self.api_secret = api_secret or parts[1]
        else:
            self.api_key = api_key or os.environ["HIGGSFIELD_API_KEY"]
            self.api_secret = api_secret or os.environ["HIGGSFIELD_API_SECRET"]

        self.base_url = HIGGSFIELD_BASE_URL.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> HiggsFieldClient:
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "hf-api-key": self.api_key,
                "hf-secret": self.api_secret,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=60.0,
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("Use async context manager: async with HiggsFieldClient() as c:")
        return self._client

    # ------------------------------------------------------------------ #
    #  Image — Soul 2.0 (text-to-image with character consistency)        #
    # ------------------------------------------------------------------ #

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(
        self,
        prompt: str,
        quality: str = "1080p",
        orientation: str = "portrait",
        custom_reference_id: str | None = None,
        custom_reference_strength: float = 1.0,
        style_id: str | None = None,
        seed: int | None = None,
        enhance_prompt: bool = True,
    ) -> GenerationJob:
        """Generate a photorealistic human model image via Soul 2.0."""
        params: dict[str, Any] = {
            "prompt": prompt,
            "width_and_height": RESOLUTION_PRESETS.get(orientation, RESOLUTION_PRESETS["portrait"]),
            "quality": quality,
            "batch_size": "SINGLE",
            "enhance_prompt": enhance_prompt,
        }
        if custom_reference_id:
            params["custom_reference_id"] = custom_reference_id
            params["custom_reference_strength"] = custom_reference_strength
        if style_id:
            params["style_id"] = style_id
        if seed is not None:
            params["seed"] = seed

        resp = await self.client.post("/v1/text2image/soul", json={"params": params})
        self._raise_for_status(resp)
        data = resp.json()

        job_set_id = data.get("job_set_id") or data.get("id", "")
        return GenerationJob(
            job_id=job_set_id,
            job_type="image",
            status=data.get("status", "queued"),
            metadata={"prompt": prompt, "quality": quality},
        )

    # ------------------------------------------------------------------ #
    #  Video — DoP (Director of Photography) image-to-video              #
    # ------------------------------------------------------------------ #

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_video(
        self,
        spec: VideoSpec,
        reference_image_url: str | None = None,
        dop_model: str = "dop-turbo",
        motions: list[str] | None = None,
    ) -> GenerationJob:
        """Generate a cinematic video clip via DoP model."""
        input_images: list[dict[str, str]] = []
        ref_url = reference_image_url or spec.model_reference_url
        if ref_url:
            input_images.append({"type": "image_url", "image_url": ref_url})

        params: dict[str, Any] = {
            "model": dop_model,
            "prompt": spec.prompt,
        }
        if input_images:
            params["input_images"] = input_images
        if motions:
            params["motions"] = motions
        if spec.motion_description:
            # motion_description goes into the prompt if motions preset not used
            params["prompt"] = f"{spec.prompt}. {spec.motion_description}"

        resp = await self.client.post("/v1/image2video/dop", json={"params": params})
        self._raise_for_status(resp)
        data = resp.json()

        job_set_id = data.get("job_set_id") or data.get("id", "")
        return GenerationJob(
            job_id=job_set_id,
            job_type="video",
            status=data.get("status", "queued"),
            metadata={
                "prompt": spec.prompt,
                "dop_model": dop_model,
                "aspect_ratio": spec.aspect_ratio.value,
            },
        )

    # ------------------------------------------------------------------ #
    #  Talking head (speech-to-video)                                     #
    # ------------------------------------------------------------------ #

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_talking_head(
        self,
        input_image_url: str,
        input_audio_url: str,
        prompt: str = "",
        quality: str = "720p",
        duration: int = 15,
    ) -> GenerationJob:
        """Animate a model image with audio to create a talking-head video."""
        params: dict[str, Any] = {
            "input_image": input_image_url,
            "input_audio": input_audio_url,  # Must be WAV format
            "quality": quality,
            "duration": duration,
            "enhance_prompt": True,
        }
        if prompt:
            params["prompt"] = prompt

        resp = await self.client.post("/v1/speak/higgsfield", json={"params": params})
        self._raise_for_status(resp)
        data = resp.json()

        job_set_id = data.get("job_set_id") or data.get("id", "")
        return GenerationJob(
            job_id=job_set_id,
            job_type="video",
            status=data.get("status", "queued"),
            metadata={"type": "talking_head", "quality": quality},
        )

    # ------------------------------------------------------------------ #
    #  Soul ID — persistent character creation                            #
    # ------------------------------------------------------------------ #

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def create_character(
        self,
        name: str,
        appearance_prompt: str,
        reference_images: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a Soul ID — a persistent character for consistent appearances.

        reference_images: 1-5 face photo URLs for max identity consistency.
        Costs ~40 credits. Returns character dict with 'id' field.
        """
        payload: dict[str, Any] = {"name": name}
        if reference_images:
            payload["image_urls"] = reference_images[:5]  # API max = 5

        resp = await self.client.post("/v1/custom-references", json=payload)
        self._raise_for_status(resp)
        return resp.json()

    async def list_characters(self) -> list[dict[str, Any]]:
        """List all saved Soul ID characters."""
        resp = await self.client.get("/v1/custom-references/list")
        self._raise_for_status(resp)
        data = resp.json()
        return data if isinstance(data, list) else data.get("items", [])

    async def animate_character(
        self,
        character_id: str,
        action_prompt: str,
        duration_seconds: int = 15,
        aspect_ratio: AspectRatio = AspectRatio.PORTRAIT_9_16,
        style: str = "cinematic",
        dop_model: str = "dop-standard",
    ) -> GenerationJob:
        """Generate a video of a Soul ID character with a given action."""
        # First generate a reference image using the Soul ID, then animate it
        image_job = await self.generate_image(
            prompt=action_prompt,
            custom_reference_id=character_id,
            custom_reference_strength=1.0,
        )
        image_job = await self.poll_job(image_job)

        # Now animate the image
        video_spec = VideoSpec(
            prompt=action_prompt,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            style=__import__("models.schemas", fromlist=["VideoStyle"]).VideoStyle(style)
            if style in ("cinematic", "portrait", "fashion", "lifestyle", "action", "editorial")
            else __import__("models.schemas", fromlist=["VideoStyle"]).VideoStyle.CINEMATIC,
            model_reference_url=image_job.result_url,
        )
        return await self.generate_video(
            spec=video_spec,
            reference_image_url=image_job.result_url,
            dop_model=dop_model,
        )

    # ------------------------------------------------------------------ #
    #  Discovery endpoints                                                 #
    # ------------------------------------------------------------------ #

    async def list_soul_styles(self) -> list[dict[str, Any]]:
        """Return available style presets for Soul 2.0 image generation."""
        resp = await self.client.get("/v1/text2image/soul-styles")
        self._raise_for_status(resp)
        data = resp.json()
        return data if isinstance(data, list) else data.get("styles", [])

    async def list_motions(self) -> list[dict[str, Any]]:
        """Return available motion presets for DoP video generation."""
        resp = await self.client.get("/v1/motions")
        self._raise_for_status(resp)
        data = resp.json()
        return data if isinstance(data, list) else data.get("motions", [])

    # ------------------------------------------------------------------ #
    #  Job polling                                                         #
    # ------------------------------------------------------------------ #

    async def poll_job(
        self,
        job: GenerationJob,
        poll_interval: float = 5.0,
        max_wait_seconds: float = 600.0,
    ) -> GenerationJob:
        """Poll /v1/job-sets/{id} until completed or timed out."""
        elapsed = 0.0
        while elapsed < max_wait_seconds:
            resp = await self.client.get(f"/v1/job-sets/{job.job_id}")
            self._raise_for_status(resp)
            data = resp.json()

            job.status = data.get("status", job.status)

            # Extract result URL from nested jobs array
            jobs_list = data.get("jobs") or data.get("results") or []
            for j in jobs_list:
                url = j.get("url") or j.get("output_url") or j.get("media_url")
                if url:
                    job.result_url = url
                    break

            if job.status in ("completed", "succeeded", "done"):
                return job
            if job.status in ("failed", "error", "nsfw", "cancelled"):
                raise HiggsFieldError(
                    f"Job {job.job_id} ended with status '{job.status}': "
                    f"{data.get('error') or data.get('message', '')}"
                )

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise HiggsFieldError(f"Job {job.job_id} timed out after {max_wait_seconds}s")

    # ------------------------------------------------------------------ #
    #  Download                                                            #
    # ------------------------------------------------------------------ #

    async def download_result(self, job: GenerationJob, output_dir: Path) -> Path:
        """Stream the generated asset to a local file."""
        if not job.result_url:
            raise HiggsFieldError(f"Job {job.job_id} has no result URL yet")

        output_dir.mkdir(parents=True, exist_ok=True)
        ext = "mp4" if job.job_type == "video" else "png"
        dest = output_dir / f"{job.job_id}.{ext}"

        async with httpx.AsyncClient() as dl:
            async with dl.stream("GET", job.result_url) as r:
                r.raise_for_status()
                with dest.open("wb") as f:
                    async for chunk in r.aiter_bytes(chunk_size=8192):
                        f.write(chunk)

        job.local_path = str(dest)
        return dest

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        if resp.is_error:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise HiggsFieldError(f"HTTP {resp.status_code}: {detail}")
