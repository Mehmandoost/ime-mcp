"""IME MCP server entrypoint."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from ime_mcp.catalog import MARKETS
from ime_mcp.dates import parse_date
from ime_mcp.markets import derivatives, financial, physical
from ime_mcp import live as live_board
from ime_mcp.paging import filter_rows, match_trade_id, paginate
from ime_mcp.response import ImeUnavailableError, tool_payload

mcp = MCPServer("ime")


def _strip_raw(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: v for k, v in row.items() if k != "_raw"} for row in rows]


def _detail(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    raw = out.pop("_raw", None)
    if raw is not None:
        out["raw_fields"] = raw
    return out


@mcp.tool()
async def list_markets() -> str:
    """List IME markets covered by this server and their statistics pages."""
    return tool_payload(
        source="https://www.ime.co.ir/",
        data=MARKETS,
        row_count=len(MARKETS),
    )


@mcp.tool()
async def search_physical_trades(
    start_date: str,
    end_date: str | None = None,
    symbol: str | None = None,
    producer: str | None = None,
    commodity: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Search physical market trade statistics (بازار فیزیکی) for a Jalali or Gregorian date range."""
    end_date = end_date or start_date
    start, end = parse_date(start_date), parse_date(end_date)
    rows = await physical.fetch_physical_trades(start, end)
    rows = filter_rows(rows, symbol=symbol, producer=producer, commodity=commodity)
    page, truncated = paginate(rows, limit=limit, offset=offset)
    return tool_payload(
        source=physical.PHYSICAL_TRADES_URL,
        data=_strip_raw(page),
        row_count=len(rows),
        truncated=truncated,
        extra={"date_range_jalali": [start.jalali, end.jalali]},
    )


@mcp.tool()
async def get_physical_trade(
    trade_id: str,
    start_date: str,
    end_date: str | None = None,
) -> str:
    """Get one physical trade row by arzehPk id or symbol within a date range."""
    end_date = end_date or start_date
    start, end = parse_date(start_date), parse_date(end_date)
    rows = await physical.fetch_physical_trades(start, end)
    row = match_trade_id(rows, trade_id)
    if row is None:
        return tool_payload(
            source=physical.PHYSICAL_TRADES_URL,
            data=None,
            extra={"error": f"No physical trade found for id {trade_id!r} in range"},
        )
    return tool_payload(source=physical.PHYSICAL_TRADES_URL, data=_detail(row), row_count=1)


@mcp.tool()
async def search_offer_notices(
    start_date: str,
    end_date: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Search offering notices derived from physical statistics rows with supply and no executed volume."""
    end_date = end_date or start_date
    start, end = parse_date(start_date), parse_date(end_date)
    rows = await physical.fetch_offer_notices(start, end)
    page, truncated = paginate(rows, limit=limit, offset=offset)
    return tool_payload(
        source=physical.PHYSICAL_TRADES_URL,
        data=_strip_raw(page),
        row_count=len(rows),
        truncated=truncated,
        extra={
            "note": "Notices are inferred from official statistics when supply_volume > 0 and trade_volume = 0",
        },
    )


@mcp.tool()
async def get_physical_board(
    symbol: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Snapshot of live contracts from IME CDN board (physical hall uses tts.ime.co.ir when accessible)."""
    try:
        rows = await live_board.get_board_snapshot(symbol=symbol, board=None)
    except ImeUnavailableError as exc:
        return tool_payload(
            source=live_board.NEGOTIATE_URL,
            data=[],
            extra={
                "error": str(exc),
                "note": "Physical TTS board at tts.ime.co.ir may require broker network access",
            },
        )
    page, truncated = paginate(rows, limit=limit, offset=offset)
    return tool_payload(
        source=live_board.NEGOTIATE_URL,
        data=_strip_raw(page),
        row_count=len(rows),
        truncated=truncated,
    )


@mcp.tool()
async def search_futures_trades(
    start_date: str,
    end_date: str | None = None,
    symbol: str | None = None,
    only_active: bool = False,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Search futures market statistics for a date range."""
    end_date = end_date or start_date
    start, end = parse_date(start_date), parse_date(end_date)
    rows = await derivatives.fetch_futures_trades(start, end, only_active=only_active)
    rows = filter_rows(rows, symbol=symbol)
    page, truncated = paginate(rows, limit=limit, offset=offset)
    return tool_payload(
        source=derivatives.FUTURES_URL,
        data=_strip_raw(page),
        row_count=len(rows),
        truncated=truncated,
    )


@mcp.tool()
async def get_futures_contract(
    contract_code: str,
    start_date: str,
    end_date: str | None = None,
) -> str:
    """Get futures contract statistics by contract code within a date range."""
    end_date = end_date or start_date
    start, end = parse_date(start_date), parse_date(end_date)
    rows = await derivatives.fetch_futures_trades(start, end)
    row = match_trade_id(rows, contract_code)
    if row is None:
        return tool_payload(
            source=derivatives.FUTURES_URL,
            data=None,
            extra={"error": f"No futures data for {contract_code!r}"},
        )
    return tool_payload(source=derivatives.FUTURES_URL, data=_detail(row), row_count=1)


@mcp.tool()
async def search_option_trades(
    start_date: str,
    end_date: str | None = None,
    option_type: str = "all",
    symbol: str | None = None,
    only_active: bool = False,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Search option market statistics (call, put, or all)."""
    end_date = end_date or start_date
    start, end = parse_date(start_date), parse_date(end_date)
    rows = await derivatives.fetch_option_trades(
        start, end, option_type=option_type, only_active=only_active
    )
    rows = filter_rows(rows, symbol=symbol)
    page, truncated = paginate(rows, limit=limit, offset=offset)
    return tool_payload(
        source=derivatives.OPTIONS_URL,
        data=_strip_raw(page),
        row_count=len(rows),
        truncated=truncated,
    )


@mcp.tool()
async def get_option_contract(
    contract_code: str,
    start_date: str,
    end_date: str | None = None,
) -> str:
    """Get one option contract row by code within a date range."""
    end_date = end_date or start_date
    start, end = parse_date(start_date), parse_date(end_date)
    rows = await derivatives.fetch_option_trades(start, end)
    row = match_trade_id(rows, contract_code)
    if row is None:
        return tool_payload(
            source=derivatives.OPTIONS_URL,
            data=None,
            extra={"error": f"No option data for {contract_code!r}"},
        )
    return tool_payload(source=derivatives.OPTIONS_URL, data=_detail(row), row_count=1)


@mcp.tool()
async def get_derivatives_board(
    symbol: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Live snapshot of derivatives contracts from cdn.ime.co.ir marketshub."""
    rows = await live_board.get_board_snapshot(symbol=symbol, board="derivatives")
    page, truncated = paginate(rows, limit=limit, offset=offset)
    return tool_payload(
        source=live_board.NEGOTIATE_URL,
        data=_strip_raw(page),
        row_count=len(rows),
        truncated=truncated,
    )


@mcp.tool()
async def search_certificate_trades(
    start_date: str,
    end_date: str | None = None,
    symbol: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Search commodity deposit certificate trades (گواهی سپرده) from bazaremali statistics."""
    end_date = end_date or start_date
    start, end = parse_date(start_date), parse_date(end_date)
    rows = await financial.fetch_certificate_trades(start, end)
    rows = filter_rows(rows, symbol=symbol)
    page, truncated = paginate(rows, limit=limit, offset=offset)
    return tool_payload(
        source=financial.BAZAR_MALI_URL,
        data=_strip_raw(page),
        row_count=len(rows),
        truncated=truncated,
        extra={"category": "certificate (c=1)"},
    )


@mcp.tool()
async def search_salaf_trades(
    start_date: str,
    end_date: str | None = None,
    symbol: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Search standard parallel salaf trades (سلف استاندارد)."""
    end_date = end_date or start_date
    start, end = parse_date(start_date), parse_date(end_date)
    rows = await financial.fetch_salaf_trades(start, end)
    rows = filter_rows(rows, symbol=symbol)
    page, truncated = paginate(rows, limit=limit, offset=offset)
    return tool_payload(
        source=financial.BAZAR_MALI_URL,
        data=_strip_raw(page),
        row_count=len(rows),
        truncated=truncated,
        extra={"category": "salaf (c=0)"},
    )


@mcp.tool()
async def search_fund_trades(
    start_date: str,
    end_date: str | None = None,
    symbol: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Search commodity fund trades from bazaremali statistics."""
    end_date = end_date or start_date
    start, end = parse_date(start_date), parse_date(end_date)
    rows = await financial.fetch_fund_trades(start, end)
    rows = filter_rows(rows, symbol=symbol)
    page, truncated = paginate(rows, limit=limit, offset=offset)
    return tool_payload(
        source=financial.BAZAR_MALI_URL,
        data=_strip_raw(page),
        row_count=len(rows),
        truncated=truncated,
        extra={"category": "commodity_fund (c=2)"},
    )


@mcp.tool()
async def get_financial_board(
    symbol: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """Live snapshot filtered to financial-market style symbols on the CDN board."""
    rows = await live_board.get_board_snapshot(symbol=symbol, board="financial")
    page, truncated = paginate(rows, limit=limit, offset=offset)
    return tool_payload(
        source=live_board.NEGOTIATE_URL,
        data=_strip_raw(page),
        row_count=len(rows),
        truncated=truncated,
    )


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
