"""Claude API client with prompt caching for the content generation agents."""
from __future__ import annotations

import os
from typing import Any

import anthropic

MODEL = "claude-sonnet-4-6"


class ClaudeClient:
    """Thin wrapper around the Anthropic SDK with prompt caching enabled."""

    def __init__(self, api_key: str | None = None):
        self._client = anthropic.Anthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"],
        )

    def complete(
        self,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 2048,
        use_cache: bool = True,
    ) -> str:
        """Send a message and return the text response."""
        system_block: list[dict[str, Any]] = [{"type": "text", "text": system}]
        if use_cache:
            system_block[0]["cache_control"] = {"type": "ephemeral"}

        response = self._client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_block,
            messages=messages,
        )
        return response.content[0].text

    def complete_json(
        self,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 2048,
    ) -> Any:
        """Return a parsed JSON object from Claude's response."""
        import json
        import re

        raw = self.complete(system, messages, max_tokens)
        # Extract JSON block if wrapped in markdown
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        text = match.group(1).strip() if match else raw.strip()
        return json.loads(text)
