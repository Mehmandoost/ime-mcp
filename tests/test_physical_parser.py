import json
from pathlib import Path

from ime_mcp.client import parse_aspnet_d_field
from ime_mcp.markets.physical import normalize_physical_record, normalize_offer_notice

FIXTURE = Path(__file__).parent / "fixtures" / "physical_trades_response.json"


def test_parse_physical_fixture():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    records = parse_aspnet_d_field(raw)
    assert len(records) >= 1
    row = normalize_physical_record(records[0])
    assert row["symbol"]
    assert row["commodity"]
    assert row["trade_date"]


def test_offer_notice_filter_logic():
    row = normalize_physical_record(
        {
            "Symbol": "TEST",
            "GoodsName": "کالا",
            "ProducerName": "تولید",
            "arze": 10,
            "Quantity": 0,
            "TotalPrice": 0,
            "date": "1404/07/01",
        }
    )
    notice = normalize_offer_notice(row)
    assert notice["notice_type"] == "supply_from_statistics"
