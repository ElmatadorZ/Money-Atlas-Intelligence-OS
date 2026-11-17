"""The Money Atlas MCP data server (money_atlas_mcp/): providers, analytics, the paper
ledger's hard limits, human-only approval, and the MCP protocol over stdio.

No network: providers are fed recorded responses.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from money_atlas_mcp import analytics, approve
from money_atlas_mcp.paper import PaperLedger, RiskError
from money_atlas_mcp.providers import (MT5, Binance, Fred, ProviderError, Router, Stooq,
                                       resolve_source)
from money_atlas_mcp.server import TOOLS, Server

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "money_atlas_mcp" / "fixtures" / "sample.json"


def fetch_from(responses):
    def fetch(url):
        for key, body in responses.items():
            if key in url:
                return body
        raise ProviderError(f"unexpected url {url}")
    return fetch


# ------------------------------------------------------------------ providers

def test_binance_quote_and_candles_parse_and_carry_source():
    b = Binance(fetch_from({
        "ticker/24hr": json.dumps({"lastPrice": "95123.4", "priceChangePercent": "-1.2",
                                   "highPrice": "96000", "lowPrice": "94000", "closeTime": 1781000000000}),
        "klines": json.dumps([[1780900000000, "1", "3", "0.5", "2", "10", 1780986399999]] * 3)}))
    q = b.quote("btc/usdt")
    assert q["symbol"] == "BTCUSDT" and q["price"] == 95123.4 and q["source"] == "binance"
    assert q["as_of"].startswith("2026-")
    c = b.candles("BTCUSDT", "1d", 3)
    assert len(c["bars"]) == 3 and c["bars"][0]["h"] == 3.0


def test_binance_error_payload_raises_instead_of_returning_none():
    b = Binance(fetch_from({"ticker/24hr": json.dumps({"code": -1121, "msg": "Invalid symbol."})}))
    with pytest.raises(ProviderError, match="no quote"):
        b.quote("NOPEUSDT")


def test_stooq_and_fred_parse_csv():
    s = Stooq(fetch_from({"stooq.com": "Date,Open,High,Low,Close,Volume\n"
                                       "2026-06-29,1,2,0.5,1.5,100\n2026-06-30,1.5,2.5,1,2,120\n"}))
    q = s.quote("SPY.US")
    assert q["price"] == 2.0 and q["change_pct_1d"] == pytest.approx(33.333, abs=1e-3)
    assert "not live" in q["note"]
    f = Fred(fetch_from({"fredgraph": "DATE,DGS10\n2026-06-26,4.31\n2026-06-29,.\n2026-06-30,4.35\n"}))
    out = f.series("dgs10")
    assert [o["value"] for o in out["observations"]] == [4.31, 4.35]  # "." (no data) skipped
    assert out["as_of"] == "2026-06-30"


def test_stooq_html_or_empty_response_is_an_error():
    s = Stooq(fetch_from({"stooq.com": "No data"}))
    with pytest.raises(ProviderError):
        s.candles("zzz.us")


def test_mt5_reads_through_the_optional_package():
    tick = SimpleNamespace(bid=4349.5, ask=4350.5, time=1781000000)
    fake = SimpleNamespace(initialize=lambda: True, last_error=lambda: (0, "ok"),
                           symbol_info_tick=lambda s: tick)
    q = MT5(fake).quote("XAUUSD")
    assert q["price"] == 4350.0 and q["source"] == "mt5"


def test_mt5_without_terminal_says_why():
    fake = SimpleNamespace(initialize=lambda: False, last_error=lambda: (-10003, "IPC failed"))
    with pytest.raises(ProviderError, match="cannot connect"):
        MT5(fake).quote("XAUUSD")


@pytest.mark.parametrize("symbol,source", [("BTCUSDT", "binance"), ("eth/usdt", "binance"),
                                           ("XAUUSD", "mt5"), ("EURUSD", "mt5"),
                                           ("spy.us", "stooq"), ("^spx", "stooq")])
def test_router_infers_source(symbol, source):
    assert resolve_source(symbol) == source


def test_router_refuses_to_guess_unknown_symbols():
    with pytest.raises(ProviderError, match="pass source="):
        resolve_source("WHATEVER")


# ------------------------------------------------------------------ analytics

def test_atr_matches_hand_computation():
    bars = [{"h": 11, "l": 9, "c": 10}] + [{"h": 12, "l": 10, "c": 11}] * 3
    # true ranges: 2, 2, 2 → ATR(3) = 2
    assert analytics.atr(bars, 3) == pytest.approx(2.0)
    assert analytics.atr(bars, 10) is None


def test_position_size():
    p = analytics.position_size(500000, 1, 4310, 4250)
    assert p["risk_cash"] == 5000 and p["units"] == pytest.approx(5000 / 60)


def test_snapshot_from_fixture_labels_its_method():
    c = json.loads(FIXTURES.read_text())["candles"]["XAUUSD"]
    s = analytics.snapshot(c)
    assert s["range"]["low"] <= s["last"] <= s["range"]["high"]
    assert s["atr"]["value"] > 0 and "heuristic" in s["measured_move"]["method"]


# ------------------------------------------------------------------ paper ledger

@pytest.fixture
def ledger(tmp_path):
    return PaperLedger(tmp_path)


def test_order_waits_for_approval_and_checks_risk(ledger):
    o = ledger.propose("XAUUSD", "buy", 1, 4300, 4260, 4400, "test")
    assert o["status"] == "awaiting_approval" and o["risk_at_stop"] == 40.0
    with pytest.raises(RiskError, match="exceeds 1.0%"):
        ledger.propose("XAUUSD", "buy", 5, 4300, 4260, None, "too big")   # 200 > 100


def test_stop_on_the_wrong_side_is_refused(ledger):
    with pytest.raises(RiskError, match="stop below entry"):
        ledger.propose("XAUUSD", "buy", 1, 4300, 4310, None, "")


def test_kill_switch_blocks_everything(ledger):
    o = ledger.propose("XAUUSD", "buy", 1, 4300, 4260, None, "")
    ledger.kill_switch.write_text("stop")
    with pytest.raises(RiskError, match="kill switch"):
        ledger.propose("XAUUSD", "buy", 1, 4300, 4260, None, "")
    with pytest.raises(RiskError, match="kill switch"):
        ledger.approve(o["id"], 4300)


def test_max_open_positions(ledger):
    for _ in range(3):
        ledger.propose("XAUUSD", "buy", 0.5, 4300, 4260, None, "")
    with pytest.raises(RiskError, match="limit 3"):
        ledger.propose("XAUUSD", "buy", 0.5, 4300, 4260, None, "")


def test_daily_loss_limit(ledger):
    state = ledger.load()
    state["limits"]["max_open_positions"] = 10
    ledger.save(state)
    for _ in range(4):
        o = ledger.propose("BTCUSDT", "buy", 0.001, 95000, 20000, None, "")   # risk 75 < 100
        ledger.approve(o["id"], 95000)
        ledger.close(o["id"], 20000)                                          # -75 each
    with pytest.raises(RiskError, match="daily loss limit"):
        ledger.propose("BTCUSDT", "buy", 0.001, 95000, 20000, None, "")


def test_approval_needs_the_typed_order_id(ledger, monkeypatch, capsys):
    o = ledger.propose("XAUUSD", "buy", 1, 4300, 4260, None, "test")
    monkeypatch.setattr(approve, "PaperLedger", lambda: ledger)
    answers = iter(["yes"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert approve.main([o["id"]]) == 1
    assert ledger.orders()["orders"][0]["status"] == "awaiting_approval"
    answers = iter([o["id"], ""])
    assert approve.main([o["id"]]) == 0
    assert ledger.orders()["orders"][0]["status"] == "open"


def test_the_agent_has_no_way_to_approve_or_send_orders():
    names = {t["name"] for t in TOOLS}
    assert not {n for n in names if any(w in n for w in ("approve", "execute", "send", "live", "place"))}
    assert "paper_propose_order" in names


# ------------------------------------------------------------------ MCP protocol

def test_stdio_protocol_end_to_end(tmp_path):
    msgs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "get_quote", "arguments": {"symbol": "BTCUSDT"}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
         "params": {"name": "get_quote", "arguments": {"symbol": "WHATEVER"}}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
         "params": {"name": "paper_propose_order", "arguments": {
             "symbol": "XAUUSD", "side": "buy", "qty": 1, "entry": 4300, "stop": 4260, "rationale": "t"}}},
        {"jsonrpc": "2.0", "id": 6, "method": "nope"},
    ]
    env = {"MONEY_ATLAS_FIXTURES": str(FIXTURES), "MONEY_ATLAS_HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    r = subprocess.run([sys.executable, str(ROOT / "money_atlas_mcp" / "server.py")],
                       input="\n".join(json.dumps(m) for m in msgs) + "\n",
                       capture_output=True, text=True, env=env, timeout=30)
    replies = {d["id"]: d for d in map(json.loads, r.stdout.splitlines())}
    assert set(replies) == {1, 2, 3, 4, 5, 6}                     # the notification got no reply
    assert replies[1]["result"]["protocolVersion"] == "2025-06-18"
    assert len(replies[2]["result"]["tools"]) == len(TOOLS)
    q = replies[3]["result"]["structuredContent"]
    assert q["source"] == "fixtures" and "FIXTURE" in q["note"] and q["as_of"]
    assert replies[4]["result"]["isError"] is True
    assert "approve" in replies[5]["result"]["structuredContent"]["next_step"]
    assert replies[6]["error"]["code"] == -32601


def test_server_is_stdlib_only():
    import ast
    stdlib = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else None
    for f in (ROOT / "money_atlas_mcp").glob("*.py"):
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                   [node.module] if isinstance(node, ast.ImportFrom) and node.module and node.level == 0 else []
            for m in mods:
                top = m.split(".")[0]
                if top in ("money_atlas_mcp", "MetaTrader5", "__future__"):
                    continue
                if stdlib is not None:
                    assert top in stdlib, f"{f.name} imports non-stdlib {m}"
