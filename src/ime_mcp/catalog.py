"""Market catalog for list_markets tool."""

MARKETS = [
    {
        "id": "physical",
        "name_fa": "بازار فیزیکی",
        "statistics_url": "https://www.ime.co.ir/offer-stat.html",
        "tools": ["search_physical_trades", "get_physical_trade", "search_offer_notices", "get_physical_board"],
    },
    {
        "id": "derivatives_futures",
        "name_fa": "بازار آتی",
        "statistics_url": "https://www.ime.co.ir/fut-report.html",
        "tools": ["search_futures_trades", "get_futures_contract", "get_derivatives_board"],
    },
    {
        "id": "derivatives_options",
        "name_fa": "بازار اختیار معامله",
        "statistics_url": "https://www.ime.co.ir/option-report.html",
        "tools": ["search_option_trades", "get_option_contract", "get_derivatives_board"],
    },
    {
        "id": "financial_salaf",
        "name_fa": "اوراق سلف استاندارد",
        "statistics_url": "https://www.ime.co.ir/standard-transactions.html",
        "tools": ["search_salaf_trades"],
    },
    {
        "id": "financial_certificate",
        "name_fa": "گواهی سپرده کالایی",
        "statistics_url": "https://www.ime.co.ir/deals_statistics.html",
        "tools": ["search_certificate_trades", "get_financial_board"],
    },
    {
        "id": "financial_fund",
        "name_fa": "صندوق‌های سرمایه‌گذاری کالایی",
        "statistics_url": "https://www.ime.co.ir/deals_statistics.html",
        "tools": ["search_fund_trades", "get_financial_board"],
    },
    {
        "id": "export",
        "name_fa": "بازار صادراتی",
        "statistics_url": "https://www.ime.co.ir/export-stat.html",
        "tools": ["search_physical_trades"],
    },
]
