# ime-mcp

Read-only [MCP](https://modelcontextprotocol.io/) server for **Iran Mercantile Exchange** ([ime.co.ir](https://www.ime.co.ir/)). It exposes official public statistics and live board snapshots from IME endpoints (no third-party API keys).

## Requirements

- Python 3.11+
- Internet access to `www.ime.co.ir` and `cdn.ime.co.ir`

## Install

```bash
cd /home/ali/Workspace/ime-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

With [uv](https://docs.astral.sh/uv/):

```bash
uv sync --extra test
```

## Cursor configuration

Add to your MCP settings (`.cursor/mcp.json` or Cursor MCP UI):

```json
{
  "mcpServers": {
    "ime": {
      "command": "uv",
      "args": ["--directory", "/home/ali/Workspace/ime-mcp", "run", "ime-mcp"]
    }
  }
}
```

If `uv` is not installed, use the venv interpreter:

```json
{
  "mcpServers": {
    "ime": {
      "command": "/home/ali/Workspace/ime-mcp/.venv/bin/ime-mcp",
      "args": []
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `list_markets` | Markets covered and statistics page URLs |
| `search_physical_trades` | Physical market trades by date range |
| `get_physical_trade` | One physical row by id or symbol |
| `search_offer_notices` | Supply rows with no executed volume |
| `get_physical_board` | Live CDN board snapshot (TTS may need broker network) |
| `search_futures_trades` | Futures statistics |
| `get_futures_contract` | One futures contract |
| `search_option_trades` | Options statistics |
| `get_option_contract` | One option contract |
| `get_derivatives_board` | Live derivatives snapshot |
| `search_certificate_trades` | Commodity deposit certificates |
| `search_salaf_trades` | Standard parallel salaf |
| `search_fund_trades` | Commodity funds |
| `get_financial_board` | Live financial symbols on CDN board |

Dates accept Jalali (`1404-07-01`) or Gregorian (`2025-09-23`).

## Tests

```bash
pytest -m "not live"
pytest -m live
```

## Data sources

- Physical: `GetAmareMoamelatList` on [offer-stat.html](https://www.ime.co.ir/offer-stat.html)
- Futures: [fut-report.html](https://www.ime.co.ir/fut-report.html) handler
- Options: [option-report.html](https://www.ime.co.ir/option-report.html) handler
- Financial: [bazaremali](https://www.ime.co.ir/standard-transactions.html) handler
- Live board: SignalR `marketshub` on [cdn.ime.co.ir](https://cdn.ime.co.ir)

## License

MIT
