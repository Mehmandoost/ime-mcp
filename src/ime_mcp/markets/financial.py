"""Financial market: salaf, certificates, funds."""

from __future__ import annotations

from typing import Any

from ime_mcp.client import get_json, post_json
from ime_mcp.dates import ParsedDate, chunk_jalali_range

BAZAR_MALI_URL = "https://www.ime.co.ir/subsystems/ime/bazaremali/bazaremalidata.ashx"
SALAF_REFERER = "https://www.ime.co.ir/standard-transactions.html"
CD_TRADES_URL = "https://dataapi.ime.co.ir/api/CDC/CDCTrades"

CD_CONTRACTS = {
    "gold_bar": "CD1GOB0001",
    "gold_coin": "CD1GOC0001",
    "silver_bar": "CD1SIB0001",
}


def normalize_financial_row(raw: dict[str, Any], market: str) -> dict[str, Any]:
    return {
        "id": raw.get("id") or raw.get("Namad"),
        "symbol": raw.get("LVal18AFC") or raw.get("Namad"),
        "code": raw.get("Namad"),
        "description": raw.get("NamadDescription"),
        "trade_date": raw.get("DT"),
        "last_price": raw.get("PDrCotVal"),
        "close_price": raw.get("PClosing"),
        "volume": raw.get("QTotTran5J"),
        "value": raw.get("QTotCap"),
        "min_price": raw.get("PriceMin"),
        "max_price": raw.get("PriceMax"),
        "market": market,
        "_raw": raw,
    }


async def _fetch_bazaremali(
    start: ParsedDate,
    end: ParsedDate,
    *,
    category: int,
    referer: str,
    market: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for from_date, to_date in chunk_jalali_range(start, end, chunk_days=100):
        params = {
            "f": from_date,
            "t": to_date,
            "c": category,
            "ot": 0,
            "lang": 8,
            "order": "asc",
        }
        data = await get_json(BAZAR_MALI_URL, params=params, referer=referer)
        rows.extend(data.get("rows", []))
    return [normalize_financial_row(r, market) for r in rows]


async def fetch_salaf_trades(start: ParsedDate, end: ParsedDate) -> list[dict[str, Any]]:
    return await _fetch_bazaremali(start, end, category=0, referer=SALAF_REFERER, market="salaf")


async def fetch_certificate_trades(start: ParsedDate, end: ParsedDate) -> list[dict[str, Any]]:
    return await _fetch_bazaremali(
        start, end, category=1, referer=SALAF_REFERER, market="certificate"
    )


async def fetch_fund_trades(start: ParsedDate, end: ParsedDate) -> list[dict[str, Any]]:
    return await _fetch_bazaremali(
        start, end, category=2, referer=SALAF_REFERER, market="commodity_fund"
    )


async def fetch_gold_silver_cd_trades(
    start: ParsedDate,
    end: ParsedDate,
    *,
    contract_type: str = "gold_bar",
    page_size: int = 100,
) -> list[dict[str, Any]]:
    code = CD_CONTRACTS.get(contract_type)
    if not code:
        raise ValueError(f"Unknown contract_type {contract_type!r}; use gold_bar, gold_coin, silver_bar")

    origin = "https://gold.ime.co.ir" if "gold" in contract_type else "https://silver.ime.co.ir"
    headers_referer = origin + "/"

    all_rows: list[dict[str, Any]] = []
    page = 1
    while True:
        payload = {
            "fromDate": start.gregorian,
            "toDate": end.gregorian,
            "pageNumber": page,
            "pageSize": page_size,
            "marketId": 22,
            "customFilter": code,
        }
        raw = await post_json(
            CD_TRADES_URL, payload, referer=headers_referer, origin=origin
        )
        data = raw.get("Data", [])
        for item in data:
            all_rows.append(
                {
                    "id": item.get("ContractCode") or item.get("ROW"),
                    "symbol": item.get("ContractCode"),
                    "trade_date": item.get("PersianDate"),
                    "volume": item.get("TradesVolume"),
                    "value": item.get("TradesValue"),
                    "last_price": item.get("LastPrice"),
                    "open_interest": item.get("OpenInterest"),
                    "contract_type": contract_type,
                    "market": "continuous_cd",
                    "_raw": item,
                }
            )
        if not raw.get("HasNextPage"):
            break
        page += 1
    return all_rows
