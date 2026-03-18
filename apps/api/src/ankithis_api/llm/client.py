"""Bedrock Converse API wrapper with structured JSON output via prompt injection."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

import boto3

from ankithis_api.config import settings

logger = logging.getLogger(__name__)

_boto3_client = None


def get_client():
    """Lazy-init boto3 bedrock-runtime client from AWS credentials."""
    global _boto3_client
    if _boto3_client is None:
        _boto3_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    return _boto3_client


def _extract_json(text: str) -> dict[str, Any]:
    """Extract JSON object from LLM response text.

    Handles responses wrapped in ```json fences or bare JSON.
    """
    # Try to find JSON in code fences first
    m = re.search(r"```(?:json)?\s*\n?(\{.*?\})\s*\n?```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))

    # Try to find a bare JSON object
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return json.loads(m.group(0))

    raise ValueError(f"No JSON object found in response: {text[:200]}...")


def _schema_to_prompt(tool_name: str, tool_schema: dict[str, Any]) -> str:
    """Convert a JSON schema into a prompt instruction for structured output."""
    schema_str = json.dumps(tool_schema, indent=2)
    return (
        f"\n\nYou MUST respond with a single JSON object matching this exact schema. "
        f"Do NOT include any text before or after the JSON. "
        f"Do NOT wrap in markdown code fences.\n\n"
        f"Required JSON schema for '{tool_name}':\n{schema_str}"
    )


def structured_call(
    system: str,
    user: str,
    tool_name: str,
    tool_schema: dict[str, Any],
    max_retries: int = 2,
    model: str | None = None,
    images: list[bytes] | None = None,
) -> dict[str, Any]:
    """Call Kimi K2.5 via Bedrock Converse API and return structured JSON output.

    Injects the JSON schema into the prompt and parses the response.
    Retries on transient errors with exponential backoff.

    Parameters
    ----------
    images:
        Optional list of JPEG image bytes for multimodal requests.
        Each entry becomes an image content block in the Converse message.
    """
    client = get_client()
    model = model or settings.bedrock_model

    # Append schema instructions to user prompt
    schema_instruction = _schema_to_prompt(tool_name, tool_schema)
    augmented_user = user + schema_instruction

    # Build content blocks: images first, then text
    content_blocks: list[dict[str, Any]] = []
    if images:
        for frame_bytes in images:
            content_blocks.append({
                "image": {
                    "format": "jpeg",
                    "source": {"bytes": frame_bytes},
                }
            })
    content_blocks.append({"text": augmented_user})

    messages = [{"role": "user", "content": content_blocks}]

    for attempt in range(max_retries + 1):
        try:
            converse_kwargs: dict[str, Any] = {
                "modelId": model,
                "messages": messages,
                "inferenceConfig": {
                    "maxTokens": 4096,
                    "temperature": 0.3,
                },
            }
            if system:
                converse_kwargs["system"] = [{"text": system}]

            response = client.converse(**converse_kwargs)

            # Extract text from response
            text = ""
            content_blocks = (
                response.get("output", {}).get("message", {}).get("content", [])
            )
            for block in content_blocks:
                if "text" in block:
                    text += block["text"]

            if not text.strip():
                raise ValueError("Empty response from Bedrock Converse API")

            # Parse JSON from response
            result = _extract_json(text)

            logger.debug(
                "Bedrock %s/%s OK (%d chars)",
                model,
                tool_name,
                len(text),
            )
            return result

        except client.exceptions.ThrottlingException:
            if attempt < max_retries:
                wait = 2 ** (attempt + 1)
                logger.warning(
                    "Bedrock throttled, retrying in %ds (attempt %d)", wait, attempt + 1
                )
                time.sleep(wait)
            else:
                raise
        except client.exceptions.ModelTimeoutException:
            if attempt < max_retries:
                wait = 2 ** (attempt + 1)
                logger.warning(
                    "Bedrock timeout, retrying in %ds (attempt %d)", wait, attempt + 1
                )
                time.sleep(wait)
            else:
                raise
        except (json.JSONDecodeError, ValueError) as e:
            if attempt < max_retries:
                logger.warning(
                    "JSON parse failed (%s), retrying (attempt %d)", e, attempt + 1
                )
                time.sleep(1)
            else:
                raise
