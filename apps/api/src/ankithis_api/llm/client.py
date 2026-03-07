"""Anthropic SDK wrapper with structured output via tool_use and retry logic."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import anthropic

from ankithis_api.config import settings

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def structured_call(
    system: str,
    user: str,
    tool_name: str,
    tool_schema: dict[str, Any],
    max_retries: int = 2,
    model: str | None = None,
) -> dict[str, Any]:
    """Call Claude with a tool definition and return the structured JSON output.

    Uses Anthropic's tool_use to force structured output matching the schema.
    Retries on transient errors with exponential backoff.
    """
    client = get_client()
    model = model or settings.anthropic_model

    tool = {
        "name": tool_name,
        "description": f"Output structured data for {tool_name}",
        "input_schema": tool_schema,
    }

    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": user}],
                tools=[tool],
                tool_choice={"type": "tool", "name": tool_name},
            )

            # Extract tool use block
            for block in response.content:
                if block.type == "tool_use" and block.name == tool_name:
                    return block.input

            raise ValueError(f"No tool_use block found in response for {tool_name}")

        except anthropic.RateLimitError:
            if attempt < max_retries:
                wait = 2 ** (attempt + 1)
                logger.warning(f"Rate limited, retrying in {wait}s (attempt {attempt + 1})")
                time.sleep(wait)
            else:
                raise
        except anthropic.APIStatusError as e:
            if e.status_code >= 500 and attempt < max_retries:
                wait = 2 ** (attempt + 1)
                logger.warning(f"API error {e.status_code}, retrying in {wait}s")
                time.sleep(wait)
            else:
                raise
