"""Publisher interface and error classes shared by all platform adapters."""
from __future__ import annotations

import time
from dataclasses import dataclass

import requests

from .. import config


class PublishError(RuntimeError):
    """before_commit=True means the post definitely was not created, so a retry is safe."""

    def __init__(self, msg: str, *, before_commit: bool, retry_after: float | None = None):
        super().__init__(msg)
        self.before_commit = before_commit
        self.retry_after = retry_after


@dataclass
class PostResult:
    post_id: str
    url: str
    status: str = "published"     # published | processing (accepted, URL not yet available)


class Publisher:
    name = "base"
    env_vars: tuple[str, ...] = ()
    posting_method = "official API"

    def available(self) -> tuple[bool, str]:
        missing = [v for v in self.env_vars if not config.env(v)]
        if missing:
            return False, f"missing credentials: {', '.join(missing)}"
        return True, "ok"

    # Each adapter implements these.
    def publish(self, video_path: str, caption: str, item: dict, *, public_url: str | None = None) -> PostResult:
        raise NotImplementedError

    def find_existing(self, caption: str, since_iso: str) -> PostResult | None:
        """Look for a post we may have created before an interruption. None = not found / not supported."""
        return None

    def post_metrics(self, post_id: str) -> dict:
        return {}

    def account_metrics(self) -> dict:
        return {}

    def needs_public_url(self) -> bool:
        return False

    # Helpers -----------------------------------------------------------------------------------
    @staticmethod
    def http(method: str, url: str, *, commit: bool = False, tries: int = 3, **kw) -> requests.Response:
        """HTTP with rate-limit handling. `commit=True` marks the request that creates the post:
        a network error there is ambiguous (the post may exist), so it is never retried blindly."""
        kw.setdefault("timeout", 120)
        for attempt in range(tries):
            try:
                r = requests.request(method, url, **kw)
            except requests.RequestException as exc:
                if commit:
                    raise PublishError(f"network error on publish call: {exc}", before_commit=False) from exc
                if attempt == tries - 1:
                    raise PublishError(f"network error: {exc}", before_commit=True) from exc
                time.sleep(2 ** attempt * 2)
                continue
            if r.status_code == 429 or r.status_code >= 500:
                wait = float(r.headers.get("Retry-After", 2 ** attempt * 5))
                if commit and r.status_code >= 500:
                    raise PublishError(f"HTTP {r.status_code} on publish call: {r.text[:200]}", before_commit=False)
                if attempt == tries - 1:
                    raise PublishError(f"HTTP {r.status_code}: {r.text[:200]}", before_commit=True, retry_after=wait)
                time.sleep(min(wait, 60))
                continue
            if r.status_code >= 400:
                raise PublishError(f"HTTP {r.status_code}: {r.text[:300]}", before_commit=True)
            return r
        raise PublishError("unreachable", before_commit=True)
