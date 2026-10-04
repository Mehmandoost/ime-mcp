"""Shared HTTP client for IME endpoints."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from ime_mcp.response import ImeUnavailableError

DEFAULT_TIMEOUT = httpx.Timeout(20.0, read=120.0)
_semaphore = asyncio.Semaphore(4)
_client: httpx.AsyncClient | None = None


def _browser_headers(referer: str) -> dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (compatible; ime-mcp/0.1)",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": referer,
        "Connection": "keep-alive",
    }


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


async def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    referer: str,
    origin: str | None = None,
    retries: int = 2,
) -> Any:
    headers = _browser_headers(referer)
    headers["Content-Type"] = "application/json; charset=utf-8"
    headers["Origin"] = origin or "https://www.ime.co.ir"

    last_error: Exception | None = None
    async with _semaphore:
        client = await get_client()
        for attempt in range(retries + 1):
            try:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code >= 500:
                    raise ImeUnavailableError(
                        f"IME unavailable (HTTP {response.status_code}) for {url}"
                    )
                response.raise_for_status()
                text = response.text.strip()
                if not text.startswith("{"):
                    raise ImeUnavailableError(f"Non-JSON response from {url}")
                return response.json()
            except (httpx.HTTPError, ImeUnavailableError) as exc:
                last_error = exc
                if attempt < retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                break

    raise ImeUnavailableError(f"Request failed for {url}: {last_error}") from last_error


async def get_json(
    url: str,
    *,
    params: dict[str, Any],
    referer: str,
    retries: int = 2,
) -> Any:
    headers = _browser_headers(referer)

    last_error: Exception | None = None
    async with _semaphore:
        client = await get_client()
        for attempt in range(retries + 1):
            try:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code >= 500:
                    raise ImeUnavailableError(
                        f"IME unavailable (HTTP {response.status_code}) for {url}"
                    )
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ImeUnavailableError) as exc:
                last_error = exc
                if attempt < retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                break

    raise ImeUnavailableError(f"Request failed for {url}: {last_error}") from last_error


def parse_aspnet_d_field(raw: Any) -> list[dict[str, Any]]:
    """Parse ASP.NET ASMX `d` wrapper (JSON string or list)."""
    inner = raw.get("d", "[]") if isinstance(raw, dict) else raw
    if isinstance(inner, str):
        records = json.loads(inner)
    else:
        records = inner
    if not isinstance(records, list):
        raise ImeUnavailableError("Unexpected IME physical trades payload shape")
    return records
