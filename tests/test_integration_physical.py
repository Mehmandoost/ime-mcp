import pytest

from ime_mcp.markets.physical import fetch_physical_trades
from ime_mcp.dates import parse_date


@pytest.mark.live
async def test_fetch_physical_trades_live():
    start = end = parse_date("1404-07-01")
    rows = await fetch_physical_trades(start, end)
    assert len(rows) >= 1
