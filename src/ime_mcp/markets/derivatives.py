"""Futures and options statistics."""

from __future__ import annotations

from typing import Any

from ime_mcp.client import get_json
from ime_mcp.dates import ParsedDate, chunk_jalali_range

FUTURES_URL = (
    "https://www.ime.co.ir/subsystems/ime/futurereports/FutureAmareMoamelatHnadler.ashx"
)
OPTIONS_URL = "https://www.ime.co.ir/subsystems/ime/option/optionboarddata.ashx"
FUTURES_REFERER = "https://www.ime.co.ir/fut-report.html"
OPTIONS_REFERER = "https://www.ime.co.ir/option-report.html"


def normalize_futures_record(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": raw.get("ContractCode"),
        "symbol": raw.get("ContractCode"),
        "description": raw.get("ContractDescription"),
        "trade_date": raw.get("DT"),
        "delivery_date": raw.get("DeliveryDate"),
        "volume": raw.get("TradesVolume"),
        "value": raw.get("TradesValue"),
        "first_price": raw.get("FirstPrice"),
        "last_price": raw.get("LastPrice"),
        "min_price": raw.get("MinPrice"),
        "max_price": raw.get("MaxPrice"),
        "settlement_price": raw.get("TodaySettlementPrice"),
        "last_settlement_price": raw.get("LastSettlementPrice"),
        "open_interest": raw.get("OpenInterest"),
        "open_interest_change": raw.get("ChangeOpenInterest"),
        "buyers": raw.get("C_Buy"),
        "sellers": raw.get("C_Sell"),
        "_raw": raw,
    }


def normalize_option_record(raw: dict[str, Any]) -> dict[str, Any]:
    option_type = raw.get("OptionType") or raw.get("Type")
    return {
        "id": raw.get("ContractCode") or raw.get("id"),
        "symbol": raw.get("ContractCode"),
        "underlying": raw.get("UnderlyingAsset") or raw.get("BaseContractCode"),
        "option_type": option_type,
        "description": raw.get("ContractDescription"),
        "trade_date": raw.get("DT"),
        "delivery_date": raw.get("DeliveryDate"),
        "volume": raw.get("TradesVolume") or raw.get("QTotTran5J"),
        "value": raw.get("TradesValue") or raw.get("QTotCap"),
        "last_price": raw.get("LastPrice") or raw.get("PDrCotVal"),
        "strike_price": raw.get("StrikePrice"),
        "open_interest": raw.get("OpenInterest"),
        "_raw": raw,
    }


async def fetch_futures_trades(
    start: ParsedDate,
    end: ParsedDate,
    *,
    only_active: bool = False,
) -> list[dict[str, Any]]:
    contract_filter = -1 if only_active else 0
    rows: list[dict[str, Any]] = []
    for from_date, to_date in chunk_jalali_range(start, end, chunk_days=100):
        params = {
            "f": from_date,
            "t": to_date,
            "c": contract_filter,
            "lang": 8,
            "order": "asc",
        }
        data = await get_json(FUTURES_URL, params=params, referer=FUTURES_REFERER)
        rows.extend(data.get("rows", []))
    return [normalize_futures_record(r) for r in rows]


async def fetch_option_trades(
    start: ParsedDate,
    end: ParsedDate,
    *,
    option_type: str = "all",
    only_active: bool = False,
) -> list[dict[str, Any]]:
    contract_filter = -1 if only_active else 0
    if option_type.lower() == "call":
        ot = 1
    elif option_type.lower() == "put":
        ot = 2
    else:
        ot = 0

    rows: list[dict[str, Any]] = []
    for from_date, to_date in chunk_jalali_range(start, end, chunk_days=100):
        params = {
            "f": from_date,
            "t": to_date,
            "c": contract_filter,
            "ot": ot,
            "lang": 8,
            "order": "asc",
        }
        data = await get_json(OPTIONS_URL, params=params, referer=OPTIONS_REFERER)
        rows.extend(data.get("rows", []))
    return [normalize_option_record(r) for r in rows]
