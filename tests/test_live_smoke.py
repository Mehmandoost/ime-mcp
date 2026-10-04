import pytest

from ime_mcp.live import _normalize_live_row, fetch_marketshub_snapshot
from ime_mcp.response import ImeUnavailableError


def test_normalize_live_row():
    row = _normalize_live_row({"ContractCode": "ETCME04", "LastPrice": 100, "TradesVolume": 5})
    assert row["symbol"] == "ETCME04"
    assert row["last_price"] == 100


@pytest.mark.live
async def test_live_derivatives_board():
    try:
        rows = await fetch_marketshub_snapshot(timeout_seconds=10.0)
    except ImeUnavailableError as exc:
        pytest.skip(f"IME live board unavailable: {exc}")
    assert isinstance(rows, list)
    assert len(rows) > 0
    assert rows[0].get("symbol")
