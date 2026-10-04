import json
from pathlib import Path

from ime_mcp.markets.derivatives import normalize_futures_record

FIXTURE = Path(__file__).parent / "fixtures" / "futures_trades_response.json"


def test_parse_futures_fixture():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rows = data.get("rows", [])
    assert rows
    row = normalize_futures_record(rows[0])
    assert row["symbol"] == rows[0]["ContractCode"]
    assert row["volume"] is not None
