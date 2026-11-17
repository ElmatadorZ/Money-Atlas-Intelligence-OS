"""Paper-trading ledger with hard risk limits and human-only approval.

The model can only *propose* an order. Approval happens outside the chat, by a person
running `python -m money_atlas_mcp.approve <order_id>` and typing the order id back. There
is deliberately no approve tool on the MCP server: the agent cannot approve its own
orders. Nothing here sends an order to any exchange or broker.
"""
from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

DEFAULT_HOME = Path(os.environ.get("MONEY_ATLAS_HOME", Path.home() / ".money_atlas"))

DEFAULT_LIMITS = {
    "account_equity": 10000.0,      # paper account, in quote currency
    "max_risk_pct_per_trade": 1.0,  # loss at stop, % of equity
    "max_open_positions": 3,
    "max_daily_loss_pct": 3.0,      # realised losses today, % of equity
    "max_notional_pct": 100.0,      # position notional, % of equity (no leverage by default)
}


class RiskError(Exception):
    """An order breaks a hard limit. The message names the limit."""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class PaperLedger:
    def __init__(self, home: Optional[Path] = None):
        self.home = Path(home or DEFAULT_HOME)
        self.home.mkdir(parents=True, exist_ok=True)
        self.path = self.home / "paper_ledger.json"
        self.kill_switch = self.home / "KILL"

    # ------------------------------------------------------------ storage
    def load(self) -> Dict:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {"limits": dict(DEFAULT_LIMITS), "orders": {}, "realised": []}

    def save(self, state: Dict) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    # ------------------------------------------------------------ checks
    def _check(self, state: Dict, order: Dict) -> None:
        lim = state["limits"]
        if self.kill_switch.exists():
            raise RiskError(f"kill switch is on ({self.kill_switch}); delete the file to resume")
        if order["side"] not in ("buy", "sell"):
            raise RiskError("side must be buy or sell")
        if order["qty"] <= 0:
            raise RiskError("qty must be positive")
        entry, stop = order["entry"], order["stop"]
        if order["side"] == "buy" and stop >= entry:
            raise RiskError("a buy needs its stop below entry")
        if order["side"] == "sell" and stop <= entry:
            raise RiskError("a sell needs its stop above entry")
        eq = lim["account_equity"]
        risk = abs(entry - stop) * order["qty"]
        if risk > eq * lim["max_risk_pct_per_trade"] / 100 + 1e-9:
            raise RiskError(f"risk at stop {risk:.2f} exceeds {lim['max_risk_pct_per_trade']}% of "
                            f"equity ({eq * lim['max_risk_pct_per_trade'] / 100:.2f})")
        if entry * order["qty"] > eq * lim["max_notional_pct"] / 100 + 1e-9:
            raise RiskError(f"notional {entry * order['qty']:.2f} exceeds {lim['max_notional_pct']}% of equity")
        open_n = sum(1 for o in state["orders"].values() if o["status"] in ("awaiting_approval", "open"))
        if open_n >= lim["max_open_positions"]:
            raise RiskError(f"already {open_n} open or pending orders (limit {lim['max_open_positions']})")
        today = _now()[:10]
        lost = -sum(r["pnl"] for r in state["realised"] if r["date"] == today and r["pnl"] < 0)
        if lost >= eq * lim["max_daily_loss_pct"] / 100:
            raise RiskError(f"daily loss limit reached ({lost:.2f}); no new orders today")

    # ------------------------------------------------------------ actions
    def propose(self, symbol: str, side: str, qty: float, entry: float, stop: float,
                take_profit: Optional[float] = None, rationale: str = "") -> Dict:
        state = self.load()
        order = {"id": "PA-" + secrets.token_hex(3).upper(), "symbol": symbol, "side": side.lower(),
                 "qty": float(qty), "entry": float(entry), "stop": float(stop),
                 "take_profit": None if take_profit is None else float(take_profit),
                 "rationale": rationale, "status": "awaiting_approval", "created": _now()}
        self._check(state, order)
        order["risk_at_stop"] = round(abs(order["entry"] - order["stop"]) * order["qty"], 2)
        state["orders"][order["id"]] = order
        self.save(state)
        return order

    def approve(self, order_id: str, fill_price: float) -> Dict:
        """Called only by the human CLI. Fills the paper order at `fill_price`."""
        state = self.load()
        o = state["orders"].get(order_id)
        if not o:
            raise RiskError(f"no order {order_id}")
        if o["status"] != "awaiting_approval":
            raise RiskError(f"{order_id} is {o['status']}, not awaiting approval")
        if self.kill_switch.exists():
            raise RiskError("kill switch is on")
        o.update(status="open", fill_price=float(fill_price), approved=_now())
        self.save(state)
        return o

    def reject(self, order_id: str) -> Dict:
        state = self.load()
        o = state["orders"][order_id]
        o.update(status="rejected", closed=_now())
        self.save(state)
        return o

    def close(self, order_id: str, exit_price: float) -> Dict:
        state = self.load()
        o = state["orders"][order_id]
        if o["status"] != "open":
            raise RiskError(f"{order_id} is not open")
        sign = 1 if o["side"] == "buy" else -1
        pnl = round(sign * (float(exit_price) - o["fill_price"]) * o["qty"], 2)
        o.update(status="closed", exit_price=float(exit_price), pnl=pnl, closed=_now())
        state["realised"].append({"id": order_id, "date": _now()[:10], "pnl": pnl})
        self.save(state)
        return o

    def orders(self, status: Optional[str] = None) -> Dict:
        state = self.load()
        items = [o for o in state["orders"].values() if status in (None, o["status"])]
        return {"orders": items, "limits": state["limits"], "kill_switch": self.kill_switch.exists(),
                "realised_pnl_total": round(sum(r["pnl"] for r in state["realised"]), 2)}
