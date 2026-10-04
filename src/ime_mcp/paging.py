"""Pagination and filtering helpers for tool responses."""

from __future__ import annotations

from typing import Any


def paginate(
    rows: list[dict[str, Any]],
    *,
    limit: int = 25,
    offset: int = 0,
    max_limit: int = 100,
) -> tuple[list[dict[str, Any]], bool]:
    limit = min(max(1, limit), max_limit)
    offset = max(0, offset)
    page = rows[offset : offset + limit]
    truncated = offset + limit < len(rows)
    return page, truncated


def filter_rows(
    rows: list[dict[str, Any]],
    *,
    symbol: str | None = None,
    producer: str | None = None,
    commodity: str | None = None,
    query: str | None = None,
) -> list[dict[str, Any]]:
    out = rows
    if symbol:
        sym = symbol.strip().lower()
        out = [r for r in out if sym in str(r.get("symbol", "")).lower()]
    if producer:
        prod = producer.strip()
        out = [r for r in out if prod in str(r.get("producer", ""))]
    if commodity:
        com = commodity.strip()
        out = [r for r in out if com in str(r.get("commodity", ""))]
    if query:
        q = query.strip().lower()
        out = [
            r
            for r in out
            if q in json_lower(r)
        ]
    return out


def json_lower(row: dict[str, Any]) -> str:
    return " ".join(str(v).lower() for v in row.values())


def match_trade_id(rows: list[dict[str, Any]], trade_id: str) -> dict[str, Any] | None:
    for row in rows:
        if str(row.get("id")) == trade_id or str(row.get("symbol")) == trade_id:
            return row
    return None
