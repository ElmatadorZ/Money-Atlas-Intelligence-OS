"""Money Atlas MCP server — JSON-RPC 2.0 over stdio, stdlib only.

    python3 money_atlas_mcp/server.py            # what Claude Code starts
    MONEY_ATLAS_FIXTURES=fixtures.json python3 money_atlas_mcp/server.py   # offline

Tools: list_sources, get_quote, get_candles, get_macro_series, market_snapshot,
position_size, paper_propose_order, paper_orders. There is no tool that approves or sends
an order: approval is `python -m money_atlas_mcp.approve`, run by a person.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

if __package__ in (None, ""):  # run as a script from the plugin folder
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from money_atlas_mcp import __version__  # noqa: E402
from money_atlas_mcp.analytics import position_size, snapshot  # noqa: E402
from money_atlas_mcp.paper import PaperLedger, RiskError  # noqa: E402
from money_atlas_mcp.providers import (ProviderError, Router, age_seconds,  # noqa: E402
                                       stale_after_seconds)

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")

INSTRUCTIONS = (
    "Market data for the Money Atlas skill. Every result carries `source` and `as_of`: "
    "quote them, and treat the numbers as given data. If `stale` is true or the note says "
    "FIXTURE or end-of-day, say so. Never present a figure from memory as current when a "
    "tool can fetch it. Orders are paper only and need a human to approve them outside the "
    "chat with `python -m money_atlas_mcp.approve`; never claim an order was placed or filled.")

S = {"type": "string"}
N = {"type": "number"}
INTERVAL = {"type": "string", "enum": ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"],
            "default": "1d"}
SOURCE = {"type": "string", "enum": ["binance", "mt5", "stooq"],
          "description": "Optional. Inferred from the symbol: BTCUSDT→binance, XAUUSD/EURUSD→mt5, "
                         "spy.us/^spx→stooq."}

TOOLS = [
    {"name": "list_sources", "description": "Which data sources this server has and what each covers.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_quote", "description": "Latest price for a symbol, with source and as_of time.",
     "inputSchema": {"type": "object", "properties": {"symbol": S, "source": SOURCE},
                     "required": ["symbol"]}},
    {"name": "get_candles", "description": "OHLCV bars for a symbol.",
     "inputSchema": {"type": "object", "properties": {
         "symbol": S, "interval": INTERVAL, "limit": {"type": "integer", "default": 100, "maximum": 1000},
         "source": SOURCE}, "required": ["symbol"]}},
    {"name": "get_macro_series", "description": "A FRED macro series (e.g. DGS10, CPIAUCSL, FEDFUNDS, "
     "DTWEXBGS, UNRATE): latest observations with dates.",
     "inputSchema": {"type": "object", "properties": {
         "series_id": S, "limit": {"type": "integer", "default": 24}}, "required": ["series_id"]}},
    {"name": "market_snapshot", "description": "Everything a market read needs from real bars: last "
     "price, range and position in it, ATR, recent swing highs/lows, structure, measured-move "
     "projections, and whether the data is stale.",
     "inputSchema": {"type": "object", "properties": {
         "symbol": S, "interval": INTERVAL, "limit": {"type": "integer", "default": 120},
         "source": SOURCE}, "required": ["symbol"]}},
    {"name": "position_size", "description": "Units so that a stop-out loses risk_pct of the account.",
     "inputSchema": {"type": "object", "properties": {
         "account": N, "risk_pct": N, "entry": N, "stop": N, "contract_size": {"type": "number", "default": 1}},
         "required": ["account", "risk_pct", "entry", "stop"]}},
    {"name": "paper_propose_order", "description": "Propose a PAPER order. It is checked against hard "
     "risk limits and then waits for a human to approve it outside the chat. Nothing is sent to "
     "any exchange or broker.",
     "inputSchema": {"type": "object", "properties": {
         "symbol": S, "side": {"type": "string", "enum": ["buy", "sell"]}, "qty": N, "entry": N,
         "stop": N, "take_profit": N, "rationale": S},
         "required": ["symbol", "side", "qty", "entry", "stop", "rationale"]}},
    {"name": "paper_orders", "description": "Paper orders, limits, kill-switch state and realised P&L.",
     "inputSchema": {"type": "object", "properties": {"status": {
         "type": "string", "enum": ["awaiting_approval", "open", "closed", "rejected"]}}}},
]

SOURCES = {
    "binance": "Crypto spot, public market data (no key): BTCUSDT, ETHUSDT, …",
    "mt5": "Gold, FX, CFDs from your MetaTrader 5 terminal (Windows, MetaTrader5 package): XAUUSD, EURUSD, …",
    "stooq": "Stocks, ETFs, indices, end-of-day: spy.us, aapl.us, ^spx, …",
    "fred": "US macro series from FRED: DGS10, CPIAUCSL, FEDFUNDS, UNRATE, …",
}


class Server:
    def __init__(self, router=None, ledger=None):
        self.router = router or Router()
        self.ledger = ledger or PaperLedger()

    # ------------------------------------------------------------ tools
    def _with_staleness(self, data, interval="1d"):
        age = age_seconds(str(data.get("as_of", "")))
        data["stale"] = None if age is None else age > stale_after_seconds(interval)
        data["data_label"] = "given — fetched by tool; quote source and as_of"
        return data

    def call(self, name, a):
        if name == "list_sources":
            return {"sources": SOURCES}
        if name == "get_quote":
            return self._with_staleness(self.router.quote(a["symbol"], a.get("source")), "1h")
        if name == "get_candles":
            iv = a.get("interval", "1d")
            return self._with_staleness(
                self.router.candles(a["symbol"], iv, a.get("limit", 100), a.get("source")), iv)
        if name == "get_macro_series":
            return self.router.series(a["series_id"], a.get("limit", 24))
        if name == "market_snapshot":
            iv = a.get("interval", "1d")
            c = self.router.candles(a["symbol"], iv, a.get("limit", 120), a.get("source"))
            return self._with_staleness(snapshot(c), iv)
        if name == "position_size":
            return position_size(a["account"], a["risk_pct"], a["entry"], a["stop"], a.get("contract_size", 1.0))
        if name == "paper_propose_order":
            o = self.ledger.propose(a["symbol"], a["side"], a["qty"], a["entry"], a["stop"],
                                    a.get("take_profit"), a.get("rationale", ""))
            o["next_step"] = (f"Awaiting human approval. The user runs: python -m money_atlas_mcp.approve {o['id']}")
            return o
        if name == "paper_orders":
            return self.ledger.orders(a.get("status"))
        raise KeyError(name)

    # ------------------------------------------------------------ JSON-RPC
    def handle(self, msg):
        mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
        if mid is None:          # notification (e.g. notifications/initialized): no reply
            return None
        try:
            if method == "initialize":
                asked = params.get("protocolVersion")
                version = asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
                result = {"protocolVersion": version, "capabilities": {"tools": {"listChanged": False}},
                          "serverInfo": {"name": "money-atlas-data", "version": __version__},
                          "instructions": INSTRUCTIONS}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                name = params.get("name")
                if name not in {t["name"] for t in TOOLS}:
                    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {name}"}}
                try:
                    data = self.call(name, params.get("arguments") or {})
                    result = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}],
                              "structuredContent": data if isinstance(data, dict) else {"result": data},
                              "isError": False}
                except (ProviderError, RiskError, ValueError, KeyError) as e:
                    result = {"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}], "isError": True}
            else:
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
            return {"jsonrpc": "2.0", "id": mid, "result": result}
        except Exception as e:  # noqa: BLE001 - never crash the stdio loop
            traceback.print_exc(file=sys.stderr)
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": str(e)}}


def main() -> None:
    server = Server()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            reply = server.handle(msg)
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
