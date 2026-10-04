"""Live trading board snapshot via IME SignalR (cdn.ime.co.ir)."""

from __future__ import annotations

import asyncio
import json
import time
import urllib.parse
from urllib.parse import quote_plus
from typing import Any

import httpx
import websockets

from ime_mcp.response import ImeUnavailableError

NEGOTIATE_URL = "https://cdn.ime.co.ir/realTimeServer/negotiate"
START_URL = "https://cdn.ime.co.ir/realTimeServer/start"
WS_URL = "wss://cdn.ime.co.ir/realTimeServer/connect"
CONNECTION_DATA = json.dumps([{"name": "marketshub"}])

_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
CACHE_TTL_SECONDS = 20.0


def _normalize_live_row(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": raw.get("ContractCode") or raw.get("contractCode"),
        "description": raw.get("ContractDescription") or raw.get("contractDescription"),
        "last_price": raw.get("LastTradedPrice") or raw.get("LastPrice") or raw.get("pl"),
        "settlement_price": raw.get("SettlementPrice") or raw.get("TodaySettlementPrice") or raw.get("pls"),
        "open_price": raw.get("FirstPrice") or raw.get("pf"),
        "high_price": raw.get("MaxPrice") or raw.get("pmax"),
        "low_price": raw.get("MinPrice") or raw.get("pmin"),
        "volume": raw.get("TotalTradedVolume") or raw.get("TradesVolume") or raw.get("tvol"),
        "value": raw.get("TotalTradedValue") or raw.get("TradesValue") or raw.get("tval"),
        "open_interest": raw.get("OpenInterest") or raw.get("openInterest"),
        "best_bid_price": raw.get("BestBuyPrice") or raw.get("BestBuyLimitPrice"),
        "best_bid_qty": raw.get("BestBuyQuantity"),
        "best_ask_price": raw.get("BestSellPrice") or raw.get("BestSellLimitPrice"),
        "best_ask_qty": raw.get("BestSellQuantity"),
        "_raw": raw,
    }


def _filter_board(
    rows: list[dict[str, Any]],
    *,
    symbol: str | None = None,
    board: str | None = None,
) -> list[dict[str, Any]]:
    out = rows
    if symbol:
        sym = symbol.strip().upper()
        out = [r for r in out if sym in str(r.get("symbol", "")).upper()]
    if board == "financial":
        out = [
            r
            for r in out
            if str(r.get("symbol", "")).startswith(("CD", "GB", "ETF", "JZ", "ET"))
        ]
    elif board == "derivatives":
        out = [
            r
            for r in out
            if str(r.get("symbol", ""))
            and not str(r.get("symbol", "")).startswith("CD")
        ]
    return out


async def fetch_marketshub_snapshot(*, timeout_seconds: float = 8.0) -> list[dict[str, Any]]:
    cache_key = "marketshub"
    now = time.time()
    cached = _cache.get(cache_key)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    params = {
        "clientProtocol": "2.1",
        "connectionData": CONNECTION_DATA,
        "_": str(int(now * 1000)),
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        negotiate = await client.get(NEGOTIATE_URL, params=params)
        if negotiate.status_code >= 500:
            raise ImeUnavailableError("IME live board unavailable (negotiate failed)")
        negotiate.raise_for_status()
        token = negotiate.json()["ConnectionToken"]

        ws_params = {
            "transport": "webSockets",
            "clientProtocol": "2.1",
            "connectionToken": token,
            "connectionData": CONNECTION_DATA,
            "tid": "1",
        }
        uri = WS_URL + "?" + urllib.parse.urlencode(ws_params, quote_via=quote_plus)
        rows: list[dict[str, Any]] = []
        ws_headers = {"User-Agent": "Mozilla/5.0 (compatible; ime-mcp/0.1)"}
        try:
            async with websockets.connect(uri, open_timeout=10, additional_headers=ws_headers) as ws:
                start = await client.get(START_URL, params=ws_params)
                start.raise_for_status()
                deadline = time.time() + timeout_seconds
                while time.time() < deadline:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    except TimeoutError:
                        continue
                    if not msg or msg[0] != "{":
                        continue
                    data = json.loads(msg)
                    messages = data.get("M") or []
                    for envelope in messages:
                        args = envelope.get("A") or []
                        if not args:
                            continue
                        payload = args[0]
                        if isinstance(payload, list) and payload:
                            rows = [_normalize_live_row(item) for item in payload if isinstance(item, dict)]
                            if rows:
                                _cache[cache_key] = (time.time(), rows)
                                return rows
        except websockets.WebSocketException as exc:
            raise ImeUnavailableError(f"IME live board websocket failed: {exc}") from exc

    if not rows:
        raise ImeUnavailableError(
            "IME live board returned no data within timeout; market may be closed"
        )
    return rows


async def get_board_snapshot(
    *,
    symbol: str | None = None,
    board: str | None = None,
) -> list[dict[str, Any]]:
    rows = await fetch_marketshub_snapshot()
    return _filter_board(rows, symbol=symbol, board=board)
