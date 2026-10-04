"""Physical market statistics."""

from __future__ import annotations

from typing import Any

from ime_mcp.client import get_json, parse_aspnet_d_field, post_json
from ime_mcp.dates import ParsedDate, chunk_jalali_range

PHYSICAL_TRADES_URL = (
    "https://www.ime.co.ir/subsystems/ime/services/home/imedata.asmx/GetAmareMoamelatList"
)
PHYSICAL_REFERER = "https://www.ime.co.ir/offer-stat.html"
EXPORT_URL = "https://www.ime.co.ir/subsystems/ime/fiziki/export.ashx"
EXPORT_REFERER = "https://www.ime.co.ir/export-stat.html"


def normalize_physical_record(raw: dict[str, Any]) -> dict[str, Any]:
    trade_value = raw.get("TotalPrice")
    return {
        "id": raw.get("arzehPk") or raw.get("Symbol"),
        "symbol": raw.get("Symbol"),
        "commodity": raw.get("GoodsName"),
        "producer": raw.get("ProducerName"),
        "supplier": raw.get("ArzehKonandeh"),
        "hall": raw.get("Talar"),
        "trade_date": raw.get("date"),
        "delivery_date": raw.get("DeliveryDate"),
        "contract_type": raw.get("ContractType"),
        "base_price": raw.get("ArzeBasePrice"),
        "min_price": raw.get("MinPrice"),
        "trade_price": raw.get("Price"),
        "max_price": raw.get("MaxPrice"),
        "supply_volume": raw.get("arze"),
        "demand": raw.get("taghaza"),
        "trade_volume": raw.get("Quantity"),
        "trade_value": trade_value,
        "trade_value_unit": "rial" if trade_value is not None else None,
        "broker": raw.get("cBrokerSpcName"),
        "warehouse": raw.get("Warehouse"),
        "currency": raw.get("Currency"),
        "unit": raw.get("Unit"),
        "settlement": raw.get("Tasvieh"),
        "supply_type": raw.get("ModeDescription"),
        "buy_type": raw.get("MethodDescription"),
        "_raw": raw,
    }


async def fetch_physical_trades(
    start: ParsedDate,
    end: ParsedDate,
    *,
    main_cat: int = 0,
    cat: int = 0,
    sub_cat: int = 0,
    producer: int = 0,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for from_date, to_date in chunk_jalali_range(start, end, chunk_days=30):
        payload = {
            "Language": 8,
            "fari": False,
            "GregorianFromDate": from_date,
            "GregorianToDate": to_date,
            "MainCat": main_cat,
            "Cat": cat,
            "SubCat": sub_cat,
            "Producer": producer,
        }
        raw = await post_json(PHYSICAL_TRADES_URL, payload, referer=PHYSICAL_REFERER)
        records.extend(parse_aspnet_d_field(raw))
    return [normalize_physical_record(r) for r in records]


def normalize_offer_notice(row: dict[str, Any]) -> dict[str, Any]:
    """Offer-oriented view derived from statistics rows with supply."""
    base = {k: v for k, v in row.items() if k != "_raw"}
    base["notice_type"] = "supply_from_statistics"
    return base


async def fetch_offer_notices(start: ParsedDate, end: ParsedDate) -> list[dict[str, Any]]:
    rows = await fetch_physical_trades(start, end)
    notices = []
    for row in rows:
        supply = row.get("supply_volume") or 0
        traded = row.get("trade_volume") or 0
        if supply and float(supply) > 0 and (not traded or float(traded) == 0):
            notices.append(normalize_offer_notice(row))
    return notices


async def fetch_export_trades(start: ParsedDate, end: ParsedDate) -> list[dict[str, Any]]:
    all_rows: list[dict[str, Any]] = []
    for from_date, to_date in chunk_jalali_range(start, end, chunk_days=100):
        params = {
            "f": from_date,
            "t": to_date,
            "m": 0,
            "c": 0,
            "s": 0,
            "p": 0,
            "lang": 8,
            "order": "asc",
        }
        data = await get_json(EXPORT_URL, params=params, referer=EXPORT_REFERER)
        for raw in data.get("rows", []):
            all_rows.append(
                {
                    "id": raw.get("arzehPk"),
                    "symbol": raw.get("Symbol"),
                    "commodity": str(raw.get("GoodsName", "")).replace(" - صادراتی", ""),
                    "producer": raw.get("ProducerName"),
                    "trade_date": raw.get("date"),
                    "delivery_date": raw.get("DeliveryDate"),
                    "trade_price": raw.get("Price"),
                    "trade_volume": raw.get("Quantity"),
                    "trade_value": raw.get("TotalPrice"),
                    "hall": raw.get("Talar"),
                    "broker": raw.get("cBrokerSpcName"),
                    "_raw": raw,
                }
            )
    return all_rows
