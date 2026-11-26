"""One OpenAI-compatible chat client.

Everything goes through a single function so that swapping providers is a config change:
the Prune gateway is just LLM_BASE_URL + LLM_API_KEY, no code edits.

Errors are typed on purpose. The API layer turns ProviderTimeout / ProviderRateLimited into a
`can't verify` verdict instead of losing the whole run — that is failure #2 in the evidence pack.
"""

from __future__ import annotations

import asyncio
import json
import os
import re

import httpx

_FENCE = re.compile(r"^\s*```(?:json|text)?\s*|\s*```\s*$", re.IGNORECASE | re.MULTILINE)


class ProviderError(Exception):
    """The provider did something we can't use. Not our bug, but our problem."""


class ProviderTimeout(ProviderError):
    """Connection refused, DNS failure, or read timeout."""


class ProviderRateLimited(ProviderError):
    """HTTP 429, including a Prune spend cap."""


class ModelOutputError(ProviderError):
    """The model answered, but not with JSON we can parse."""


def settings() -> dict[str, str | float]:
    return {
        "base_url": os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        "api_key": os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "",
        "model": os.getenv("MODEL", "gpt-5-mini"),
        "timeout": float(os.getenv("REQUEST_TIMEOUT_S", "45")),
    }


def strip_fences(text: str) -> str:
    """Models sometimes wrap JSON in ```json fences, or in a sentence. Recover the object."""
    cleaned = _FENCE.sub("", text.strip())
    start, end = cleaned.find("{"), cleaned.rfind("}")
    return cleaned[start : end + 1] if 0 <= start < end else cleaned


async def chat_json(
    system: str,
    user: str,
    *,
    timeout: float | None = None,
    retries: int = 1,
) -> dict:
    cfg = settings()
    if not cfg["api_key"]:
        raise ProviderError("LLM_API_KEY is not set (copy .env.example to .env)")

    payload: dict = {
        "model": cfg["model"],
        "temperature": 0,  # needed for the R2 repeat check to be stable
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }

    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return await _post(payload, cfg, timeout)
        except (ProviderTimeout, ProviderRateLimited, ProviderError) as exc:
            last = exc
            if isinstance(exc, ModelOutputError):
                raise  # retrying a bad answer rarely helps and costs money
            if attempt < retries:
                await asyncio.sleep(1.5)
    raise last or ProviderError("unknown provider failure")


async def _post(payload: dict, cfg: dict, timeout: float | None) -> dict:
    async with httpx.AsyncClient(timeout=timeout or cfg["timeout"]) as client:
        try:
            resp = await client.post(
                f"{cfg['base_url']}/chat/completions",
                headers={"Authorization": f"Bearer {cfg['api_key']}"},
                json=payload,
            )
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
            raise ProviderTimeout(str(exc) or type(exc).__name__) from exc

    if resp.status_code == 429:
        raise ProviderRateLimited(resp.text[:300])
    if resp.status_code == 400 and ("response_format" in payload or "temperature" in payload):
        # Some OpenAI-compatible gateways (and some reasoning models) reject these knobs.
        payload.pop("response_format", None)
        payload.pop("temperature", None)
        return await _post(payload, cfg, timeout)
    if resp.status_code >= 400:
        raise ProviderError(f"HTTP {resp.status_code}: {resp.text[:300]}")

    content = resp.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(strip_fences(content))
    except json.JSONDecodeError as exc:
        raise ModelOutputError(content[:300]) from exc
