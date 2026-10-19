"""Settings loader. Paths resolve relative to the project root (the world-ignored/ folder)."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.environ.get("WI_STATE_DIR", ROOT / "state"))
WORK_DIR = Path(os.environ.get("WI_WORK_DIR", ROOT / "work"))


@lru_cache(maxsize=1)
def settings() -> dict:
    with open(ROOT / "config" / "settings.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def tz() -> ZoneInfo:
    return ZoneInfo(settings()["timezone"])


def asset(path: str) -> Path:
    return ROOT / path


def env(name: str) -> str | None:
    """Read a credential from the environment. Values are never logged."""
    value = os.environ.get(name)
    return value or None
