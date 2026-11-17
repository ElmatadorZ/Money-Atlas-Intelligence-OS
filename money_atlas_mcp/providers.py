"""Market-data providers. Stdlib only (urllib); the MT5 provider needs the optional
`MetaTrader5` package and a running MT5 terminal on Windows.

Each provider returns plain dicts that always carry `source` and `as_of` (UTC ISO 8601),
and raises ProviderError with a reason instead of returning None. A silent None is how a
reasoning layer ends up inventing a number.
"""
from __future__ import annotations

import csv
import io
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

USER_AGENT = "money-atlas-mcp/0.1"
TIMEOUT = 10

Fetch = Callable[[str], str]


class ProviderError(Exception):
    """A provider could not answer. The message says why, for the user to read."""


def http_get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # nosec B310 - fixed https hosts
            return r.read().decode("utf-8")
    except Exception as e:  # noqa: BLE001 - surface every network failure the same way
        raise ProviderError(f"request failed: {type(e).__name__}: {e}") from e


def clean(text: object, n: int = 80) -> str:
    """Remote text is untrusted: keep it short, printable and on one line before it can
    reach the model's context."""
    s = "".join(ch if ch.isprintable() else " " for ch in str(text))
    return " ".join(s.split())[:n]


def check_limit(limit, maximum: int = 1000) -> int:
    if isinstance(limit, bool) or not isinstance(limit, (int, float)) or limit != int(limit):
        raise ProviderError(f"limit must be a whole number from 1 to {maximum}")
    if not 1 <= int(limit) <= maximum:
        raise ProviderError(f"limit must be from 1 to {maximum}")
    return int(limit)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).replace(microsecond=0).isoformat()


# ------------------------------------------------------------------ Binance (crypto)

class Binance:
    """Public market-data endpoints; no API key, no trading."""
    name = "binance"
    base = "https://api.binance.com/api/v3"
    INTERVALS = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"}

    def __init__(self, fetch: Fetch = http_get):
        self.fetch = fetch

    def quote(self, symbol: str) -> Dict:
        sym = symbol.upper().replace("/", "")
        data = json.loads(self.fetch(f"{self.base}/ticker/24hr?symbol={urllib.parse.quote(sym)}"))
        if "lastPrice" not in data:
            raise ProviderError(f"binance: no quote for {clean(sym, 20)}: {clean(data.get('msg', 'unexpected response') if isinstance(data, dict) else 'unexpected response')}")
        return {"symbol": sym, "price": float(data["lastPrice"]),
                "change_pct_24h": float(data.get("priceChangePercent", 0.0)),
                "high_24h": float(data["highPrice"]), "low_24h": float(data["lowPrice"]),
                "as_of": ms_to_iso(int(data["closeTime"])), "source": self.name}

    def candles(self, symbol: str, interval: str = "1d", limit: int = 100) -> Dict:
        if interval not in self.INTERVALS:
            raise ProviderError(f"binance: interval must be one of {sorted(self.INTERVALS)}")
        sym = symbol.upper().replace("/", "")
        limit = check_limit(limit)
        rows = json.loads(self.fetch(
            f"{self.base}/klines?symbol={urllib.parse.quote(sym)}&interval={interval}&limit={limit}"))
        if not isinstance(rows, list) or not rows:
            raise ProviderError(f"binance: no candles for {clean(sym, 20)}: "
                                f"{clean(rows.get('msg', 'unexpected response') if isinstance(rows, dict) else 'empty')}")
        bars = [{"t": ms_to_iso(int(r[0])), "o": float(r[1]), "h": float(r[2]),
                 "l": float(r[3]), "c": float(r[4]), "v": float(r[5])} for r in rows]
        return {"symbol": sym, "interval": interval, "bars": bars,
                "as_of": ms_to_iso(int(rows[-1][6])), "source": self.name}


# ------------------------------------------------------------------ Stooq (stocks, indices, ETFs)

class Stooq:
    """Daily OHLCV CSV. Symbols like `spy.us`, `aapl.us`, `^spx`. Check stooq.com's terms
    for your use; it is a free source with no service guarantee."""
    name = "stooq"

    def __init__(self, fetch: Fetch = http_get):
        self.fetch = fetch

    def candles(self, symbol: str, interval: str = "1d", limit: int = 100) -> Dict:
        if interval not in {"1d", "1w", "1M"}:
            raise ProviderError("stooq: interval must be 1d, 1w or 1M")
        limit = check_limit(limit)
        i = {"1d": "d", "1w": "w", "1M": "m"}[interval]
        text = self.fetch(f"https://stooq.com/q/d/l/?s={urllib.parse.quote(symbol.lower())}&i={i}")
        rows = list(csv.DictReader(io.StringIO(text)))
        if not rows or "Close" not in rows[0]:
            raise ProviderError(f"stooq: no data for {clean(symbol, 20)} (unexpected response, {len(text)} bytes)")
        bars = [{"t": r["Date"], "o": float(r["Open"]), "h": float(r["High"]), "l": float(r["Low"]),
                 "c": float(r["Close"]), "v": float(r.get("Volume") or 0)} for r in rows[-int(limit):]]
        return {"symbol": symbol.lower(), "interval": interval, "bars": bars,
                "as_of": bars[-1]["t"], "source": self.name, "note": "end-of-day data"}

    def quote(self, symbol: str) -> Dict:
        c = self.candles(symbol, "1d", 2)
        last = c["bars"][-1]
        prev = c["bars"][-2]["c"] if len(c["bars"]) > 1 else None
        return {"symbol": c["symbol"], "price": last["c"],
                "change_pct_1d": round((last["c"] / prev - 1) * 100, 3) if prev else None,
                "as_of": c["as_of"], "source": self.name, "note": "last daily close, not live"}


# ------------------------------------------------------------------ FRED (macro)

class Fred:
    """FRED series as CSV (no key needed for fredgraph.csv). IDs like DGS10, CPIAUCSL,
    FEDFUNDS, DTWEXBGS."""
    name = "fred"

    def __init__(self, fetch: Fetch = http_get):
        self.fetch = fetch

    def series(self, series_id: str, limit: int = 24) -> Dict:
        sid = series_id.upper()
        text = self.fetch(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={urllib.parse.quote(sid)}")
        limit = check_limit(limit)
        rows = list(csv.reader(io.StringIO(text)))
        if len(rows) < 2 or len(rows[0]) != 2:
            raise ProviderError(f"fred: no data for {clean(sid, 20)} (unexpected response, {len(text)} bytes)")
        obs = []
        for row in rows[1:]:
            if len(row) == 2 and row[1] not in (".", ""):
                try:
                    obs.append({"date": clean(row[0], 10), "value": float(row[1])})
                except ValueError:
                    continue
        if not obs:
            raise ProviderError(f"fred: {sid} has no numeric observations")
        obs = obs[-int(limit):]
        return {"series_id": sid, "observations": obs, "as_of": obs[-1]["date"],
                "source": self.name, "note": "latest observation date; releases lag the period"}


# ------------------------------------------------------------------ MetaTrader 5 (gold, FX, CFDs)

class MT5:
    """Reads from a running MT5 terminal via the optional `MetaTrader5` package (Windows).
    Read-only here: this server never sends orders to MT5."""
    name = "mt5"
    TIMEFRAMES = {"1m": "TIMEFRAME_M1", "5m": "TIMEFRAME_M5", "15m": "TIMEFRAME_M15",
                  "30m": "TIMEFRAME_M30", "1h": "TIMEFRAME_H1", "4h": "TIMEFRAME_H4",
                  "1d": "TIMEFRAME_D1", "1w": "TIMEFRAME_W1", "1M": "TIMEFRAME_MN1"}

    def __init__(self, module=None):
        self._mt5 = module

    def _lib(self):
        if self._mt5 is None:
            try:
                import MetaTrader5 as mt5  # type: ignore
            except ImportError as e:
                raise ProviderError("mt5: the MetaTrader5 package is not installed "
                                    "(pip install MetaTrader5, Windows with MT5 running)") from e
            self._mt5 = mt5
        if not self._mt5.initialize():
            raise ProviderError(f"mt5: cannot connect to the terminal: {self._mt5.last_error()}")
        return self._mt5

    def quote(self, symbol: str) -> Dict:
        mt5 = self._lib()
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise ProviderError(f"mt5: no tick for {symbol} (is it in Market Watch?)")
        return {"symbol": symbol, "price": (tick.bid + tick.ask) / 2, "bid": tick.bid, "ask": tick.ask,
                "as_of": datetime.fromtimestamp(tick.time, tz=timezone.utc).isoformat(),
                "source": self.name, "note": "broker quote; prices differ between brokers"}

    def candles(self, symbol: str, interval: str = "1d", limit: int = 100) -> Dict:
        if interval not in self.TIMEFRAMES:
            raise ProviderError(f"mt5: interval must be one of {sorted(self.TIMEFRAMES)}")
        limit = check_limit(limit)
        mt5 = self._lib()
        rates = mt5.copy_rates_from_pos(symbol, getattr(mt5, self.TIMEFRAMES[interval]), 0, int(limit))
        if rates is None or len(rates) == 0:
            raise ProviderError(f"mt5: no candles for {symbol}: {mt5.last_error()}")
        bars = [{"t": datetime.fromtimestamp(int(r["time"]), tz=timezone.utc).isoformat(),
                 "o": float(r["open"]), "h": float(r["high"]), "l": float(r["low"]),
                 "c": float(r["close"]), "v": float(r["tick_volume"])} for r in rates]
        return {"symbol": symbol, "interval": interval, "bars": bars, "as_of": bars[-1]["t"],
                "source": self.name}


# ------------------------------------------------------------------ fixtures (offline / tests)

class Fixtures:
    """Serves recorded data from a JSON file (MONEY_ATLAS_FIXTURES). For tests, demos and
    offline work; every answer is marked so it is never mistaken for live data."""
    name = "fixtures"

    def __init__(self, path: str):
        with open(path, encoding="utf-8") as f:
            self.data = json.load(f)

    def _get(self, kind: str, key: str) -> Dict:
        try:
            out = dict(self.data[kind][key])
        except KeyError as e:
            raise ProviderError(f"fixtures: no {kind} for {key}") from e
        out.setdefault("source", self.name)
        out["note"] = "FIXTURE DATA — recorded, not live"
        return out

    def quote(self, symbol: str) -> Dict:
        return self._get("quotes", symbol)

    def candles(self, symbol: str, interval: str = "1d", limit: int = 100) -> Dict:
        limit = check_limit(limit)
        c = self._get("candles", symbol)
        c["bars"] = c["bars"][-int(limit):]
        return c

    def series(self, series_id: str, limit: int = 24) -> Dict:
        limit = check_limit(limit)
        s = self._get("series", series_id)
        s["observations"] = s["observations"][-int(limit):]
        return s


# ------------------------------------------------------------------ routing

MT5_HINTS = ("XAU", "XAG", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF", "USDTHB", "US30", "NAS100")


SYMBOL_OK = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.^/_-")


def check_symbol(symbol) -> str:
    if not isinstance(symbol, str) or not 1 <= len(symbol) <= 20 or not set(symbol) <= SYMBOL_OK:
        raise ProviderError("symbol must be 1-20 characters: letters, digits and . ^ / _ -")
    return symbol


def resolve_source(symbol: str) -> str:
    """Pick a provider from the symbol's shape when the caller does not name one."""
    s = check_symbol(symbol).strip()
    if s.startswith("^") or "." in s:
        return "stooq"                      # ^spx, spy.us, ptt.th (if covered)
    up = s.upper().replace("/", "")
    if up.endswith(("USDT", "USDC", "FDUSD", "BTC")) and len(up) > 5:
        return "binance"
    if any(up.startswith(h) for h in MT5_HINTS) and len(up) <= 7:
        return "mt5"
    raise ProviderError(f"cannot tell which source serves {symbol!r}; pass source="
                        "'binance' (BTCUSDT), 'mt5' (XAUUSD, EURUSD) or 'stooq' (spy.us, ^spx)")


class Router:
    def __init__(self, providers: Optional[Dict[str, object]] = None):
        if providers is None:
            fx = os.environ.get("MONEY_ATLAS_FIXTURES")
            if fx:
                f = Fixtures(fx)
                providers = {"binance": f, "stooq": f, "fred": f, "mt5": f}
            else:
                providers = {"binance": Binance(), "stooq": Stooq(), "fred": Fred(), "mt5": MT5()}
        self.providers = providers

    def get(self, source: Optional[str], symbol: str):
        check_symbol(symbol)
        if source is not None and not isinstance(source, str):
            raise ProviderError("source must be a string")
        name = (source or resolve_source(symbol)).lower()
        if name not in self.providers:
            raise ProviderError(f"unknown source {clean(name, 20)!r}; available: {sorted(self.providers)}")
        return self.providers[name]

    def quote(self, symbol: str, source: Optional[str] = None) -> Dict:
        return self.get(source, symbol).quote(symbol)

    def candles(self, symbol: str, interval: str = "1d", limit: int = 100,
                source: Optional[str] = None) -> Dict:
        return self.get(source, symbol).candles(symbol, interval, limit)

    def series(self, series_id: str, limit: int = 24) -> Dict:
        if not isinstance(series_id, str) or not 1 <= len(series_id) <= 30 or not series_id.replace("_", "").isalnum():
            raise ProviderError("series_id must be a FRED id such as DGS10 or CPIAUCSL")
        return self.providers["fred"].series(series_id, limit)


def stale_after_seconds(interval: str) -> int:
    """How old the last bar may be before it is called stale."""
    return {"1m": 180, "5m": 900, "15m": 2700, "30m": 5400, "1h": 10800, "4h": 43200,
            "1d": 4 * 86400, "1w": 15 * 86400, "1M": 45 * 86400}.get(interval, 4 * 86400)


def age_seconds(as_of: str) -> Optional[float]:
    try:
        t = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - t).total_seconds()


def as_list(x) -> List:
    return x if isinstance(x, list) else [x]
