"""Paper-trading ledger with hard risk limits and human-only approval.

The model can only *propose* an order. Approval happens outside the chat, by a person
running `python -m money_atlas_mcp.approve <order_id>` at a real terminal and entering an
approval passphrase that only they know. There is deliberately no approve tool on the MCP
server. Nothing here sends an order to any exchange or broker.

Security boundary (red-team result, see docs/AGENT_ARCHITECTURE.md): an agent that runs
as the same OS user with a shell can read and rewrite files in ~/.money_atlas. It cannot
approve without the passphrase, and approvals are signed with a key derived from it, so a
hand-edited ledger is detected by `approve --verify`. Before any real money, approval must
move to a channel the agent cannot reach (another OS user or device).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from money_atlas_mcp.analytics import finite

DEFAULT_HOME = Path(os.environ.get("MONEY_ATLAS_HOME", Path.home() / ".money_atlas"))
PBKDF2_ITERATIONS = 300_000
MIN_PASSPHRASE = 8

DEFAULT_LIMITS = {
    "account_equity": 10000.0,      # paper account, in quote currency
    "max_risk_pct_per_trade": 1.0,  # loss at stop, % of equity
    "max_open_positions": 3,
    "max_daily_loss_pct": 3.0,      # realised losses today, % of equity
    "max_notional_pct": 100.0,      # position notional, % of equity (no leverage by default)
}

SIGNED_FIELDS = ("id", "symbol", "side", "qty", "entry", "stop", "take_profit", "fill_price", "approved")


class RiskError(Exception):
    """An order breaks a hard limit or an approval rule. The message names it."""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _derive(passphrase: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, PBKDF2_ITERATIONS)


def _canonical(order: Dict) -> bytes:
    return json.dumps({k: order.get(k) for k in SIGNED_FIELDS}, sort_keys=True).encode("utf-8")


class PaperLedger:
    def __init__(self, home: Optional[Path] = None):
        self.home = Path(home or DEFAULT_HOME)
        self.home.mkdir(parents=True, exist_ok=True)
        self.path = self.home / "paper_ledger.json"
        self.kill_switch = self.home / "KILL"
        self.auth_path = self.home / "approval_auth.json"
        self._lock = self.home / "ledger.lock"

    # ------------------------------------------------------------ storage
    @contextmanager
    def locked(self, timeout: float = 10.0):
        """Cross-platform exclusive lock (O_EXCL lock file), so two servers or a server and
        the approval CLI cannot lose each other's writes."""
        deadline = time.monotonic() + timeout
        while True:
            try:
                fd = os.open(self._lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                if time.monotonic() > deadline:
                    try:   # a lock older than 60 s is from a crashed process
                        if time.time() - self._lock.stat().st_mtime > 60:
                            self._lock.unlink()
                            continue
                    except FileNotFoundError:
                        continue
                    raise RiskError("ledger is busy (lock held); try again")
                time.sleep(0.01)
        try:
            yield
        finally:
            os.close(fd)
            try:
                self._lock.unlink()
            except FileNotFoundError:
                pass

    def load(self) -> Dict:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {"limits": dict(DEFAULT_LIMITS), "orders": {}, "realised": []}

    def save(self, state: Dict) -> None:
        tmp = self.path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    # ------------------------------------------------------------ approval passphrase
    def has_passphrase(self) -> bool:
        return self.auth_path.exists()

    def set_passphrase(self, passphrase: str) -> None:
        if len(passphrase) < MIN_PASSPHRASE:
            raise RiskError(f"passphrase must be at least {MIN_PASSPHRASE} characters")
        salt_check, salt_sign = secrets.token_bytes(16), secrets.token_bytes(16)
        self.auth_path.write_text(json.dumps({
            "salt_check": salt_check.hex(), "salt_sign": salt_sign.hex(),
            "check": _derive(passphrase, salt_check).hex(), "iterations": PBKDF2_ITERATIONS}),
            encoding="utf-8")
        try:
            os.chmod(self.auth_path, 0o600)
        except OSError:
            pass

    def _signing_key(self, passphrase: str) -> bytes:
        if not self.has_passphrase():
            raise RiskError("no approval passphrase set; run: python -m money_atlas_mcp.approve --set-passphrase")
        auth = json.loads(self.auth_path.read_text(encoding="utf-8"))
        if not hmac.compare_digest(_derive(passphrase, bytes.fromhex(auth["salt_check"])).hex(), auth["check"]):
            raise RiskError("wrong approval passphrase")
        return _derive(passphrase, bytes.fromhex(auth["salt_sign"]))

    # ------------------------------------------------------------ checks
    def _check(self, state: Dict, order: Dict) -> None:
        lim = state["limits"]
        if self.kill_switch.exists():
            raise RiskError(f"kill switch is on ({self.kill_switch}); delete the file to resume")
        if order["side"] not in ("buy", "sell"):
            raise RiskError("side must be buy or sell")
        entry, stop, tp = order["entry"], order["stop"], order["take_profit"]
        if order["side"] == "buy" and stop >= entry:
            raise RiskError("a buy needs its stop below entry")
        if order["side"] == "sell" and stop <= entry:
            raise RiskError("a sell needs its stop above entry")
        if tp is not None and (tp <= entry if order["side"] == "buy" else tp >= entry):
            raise RiskError("take-profit is on the wrong side of entry")
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
        try:
            order = {"id": "PA-" + secrets.token_hex(3).upper(), "symbol": str(symbol)[:20],
                     "side": str(side).lower(),
                     "qty": finite("qty", qty, positive=True),
                     "entry": finite("entry", entry, positive=True),
                     "stop": finite("stop", stop, positive=True),
                     "take_profit": None if take_profit is None else finite("take_profit", take_profit, positive=True),
                     "rationale": str(rationale)[:500], "status": "awaiting_approval", "created": _now()}
        except ValueError as e:
            raise RiskError(str(e)) from e
        with self.locked():
            state = self.load()
            self._check(state, order)
            order["risk_at_stop"] = round(abs(order["entry"] - order["stop"]) * order["qty"], 2)
            state["orders"][order["id"]] = order
            self.save(state)
        return order

    def approve(self, order_id: str, fill_price: float, passphrase: str) -> Dict:
        """Called only by the human CLI. Checks the passphrase, signs the approval, and fills
        the paper order at `fill_price`."""
        key = self._signing_key(passphrase)
        fill = finite("fill_price", fill_price, positive=True)
        with self.locked():
            state = self.load()
            o = state["orders"].get(order_id)
            if not o:
                raise RiskError(f"no order {order_id}")
            if o["status"] != "awaiting_approval":
                raise RiskError(f"{order_id} is {o['status']}, not awaiting approval")
            if self.kill_switch.exists():
                raise RiskError("kill switch is on")
            o.update(status="open", fill_price=fill, approved=_now())
            o["approval_sig"] = hmac.new(key, _canonical(o), hashlib.sha256).hexdigest()
            self.save(state)
        return o

    def reject(self, order_id: str) -> Dict:
        with self.locked():
            state = self.load()
            o = state["orders"].get(order_id)
            if not o:
                raise RiskError(f"no order {order_id}")
            o.update(status="rejected", closed=_now())
            self.save(state)
        return o

    def close(self, order_id: str, exit_price: float) -> Dict:
        exit_price = finite("exit_price", exit_price, positive=True)
        with self.locked():
            state = self.load()
            o = state["orders"].get(order_id)
            if not o or o["status"] != "open":
                raise RiskError(f"{order_id} is not open")
            sign = 1 if o["side"] == "buy" else -1
            pnl = round(sign * (exit_price - o["fill_price"]) * o["qty"], 2)
            o.update(status="closed", exit_price=exit_price, pnl=pnl, closed=_now())
            state["realised"].append({"id": order_id, "date": _now()[:10], "pnl": pnl})
            self.save(state)
        return o

    def verify(self, passphrase: str) -> Dict:
        """Recompute every approval signature. Orders that are open or closed without a
        valid signature were not approved through the CLI."""
        key = self._signing_key(passphrase)
        bad = []
        for o in self.load()["orders"].values():
            if o["status"] in ("open", "closed"):
                good = hmac.new(key, _canonical(o), hashlib.sha256).hexdigest()
                if not hmac.compare_digest(o.get("approval_sig", ""), good):
                    bad.append(o["id"])
        return {"tampered": bad, "ok": not bad}

    def orders(self, status: Optional[str] = None) -> Dict:
        state = self.load()
        items = []
        for o in state["orders"].values():
            if status in (None, o["status"]):
                o = dict(o)
                if o["status"] in ("open", "closed") and not o.get("approval_sig"):
                    o["warning"] = "UNVERIFIED: no approval signature — not approved through the CLI"
                items.append(o)
        return {"orders": items, "limits": state["limits"], "kill_switch": self.kill_switch.exists(),
                "realised_pnl_total": round(sum(r["pnl"] for r in state["realised"]), 2),
                "integrity": "signatures are checked by a person with: python -m money_atlas_mcp.approve --verify"}
