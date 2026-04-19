from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class VideoStyle(str, Enum):
    CINEMATIC = "cinematic"
    PORTRAIT = "portrait"
    FASHION = "fashion"
    LIFESTYLE = "lifestyle"
    ACTION = "action"
    EDITORIAL = "editorial"


class AspectRatio(str, Enum):
    PORTRAIT_9_16 = "9:16"   # Reels / TikTok
    SQUARE_1_1 = "1:1"       # Instagram feed
    LANDSCAPE_16_9 = "16:9"  # YouTube / desktop


class HumanModelSpec(BaseModel):
    """Specification for generating a photorealistic human model."""
    gender: str = Field(..., description="Gender of the model")
    age_range: str = Field(..., description="Age range e.g. '25-30'")
    ethnicity: str | None = None
    hair: str | None = None
    style: VideoStyle = VideoStyle.PORTRAIT
    outfit_description: str | None = None
    setting: str | None = None
    lighting: str = "natural cinematic lighting"
    extra_details: str | None = None

    def to_prompt(self) -> str:
        parts = [
            f"Ultra-photorealistic portrait of a {self.age_range} year old {self.gender}",
        ]
        if self.ethnicity:
            parts.append(self.ethnicity)
        if self.hair:
            parts.append(f"with {self.hair} hair")
        if self.outfit_description:
            parts.append(f"wearing {self.outfit_description}")
        if self.setting:
            parts.append(f"in {self.setting}")
        parts.append(self.lighting)
        parts.append("8K resolution, hyperrealistic skin texture, professional photography")
        if self.extra_details:
            parts.append(self.extra_details)
        return ", ".join(parts)


class VideoSpec(BaseModel):
    """Specification for a video/reel generation job."""
    prompt: str
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT_9_16
    duration_seconds: int = Field(default=15, ge=5, le=60)
    style: VideoStyle = VideoStyle.CINEMATIC
    model_reference_url: str | None = None
    motion_description: str | None = None
    audio_description: str | None = None


class TrendItem(BaseModel):
    """A discovered viral content trend."""
    title: str
    platform: str
    engagement_score: float
    tags: list[str] = Field(default_factory=list)
    url: str | None = None
    description: str | None = None
    content_format: str = "reel"


class GenerationJob(BaseModel):
    """Tracks a Higgsfield generation job."""
    job_id: str
    job_type: str  # "image" | "video"
    status: str = "pending"
    result_url: str | None = None
    local_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContentPlan(BaseModel):
    """Full production plan for a batch of content."""
    trend: TrendItem
    model_spec: HumanModelSpec
    video_specs: list[VideoSpec]
    hook_text: str
    caption: str
    hashtags: list[str] = Field(default_factory=list)
    posting_time: str | None = None
