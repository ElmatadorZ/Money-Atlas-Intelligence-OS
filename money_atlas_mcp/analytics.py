"""Numbers the skill's QUANTIFY rule asks for, computed from real bars.

Deterministic, stdlib only. Every function states its method so the skill can show it.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional


def finite(name: str, v, positive: bool = False) -> float:
    """Reject bools, strings, NaN and infinity: NaN passes every `<`/`>` check silently."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError(f"{name} must be a finite number")
    if positive and v <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return float(v)


def atr(bars: List[Dict], period: int = 14) -> Optional[float]:
    """Wilder's Average True Range over `period` bars (simple mean of true range for the
    seed, then Wilder smoothing). None if there are not enough bars."""
    if len(bars) < period + 1:
        return None
    trs = []
    for prev, cur in zip(bars, bars[1:]):
        trs.append(max(cur["h"] - cur["l"], abs(cur["h"] - prev["c"]), abs(cur["l"] - prev["c"])))
    value = sum(trs[:period]) / period
    for tr in trs[period:]:
        value = (value * (period - 1) + tr) / period
    return value


def swings(bars: List[Dict], lookback: int = 2) -> Dict[str, List[Dict]]:
    """Fractal swing points: a high (low) higher (lower) than `lookback` bars either side."""
    highs, lows = [], []
    for i in range(lookback, len(bars) - lookback):
        window = bars[i - lookback:i + lookback + 1]
        if bars[i]["h"] == max(b["h"] for b in window):
            highs.append({"t": bars[i]["t"], "price": bars[i]["h"]})
        if bars[i]["l"] == min(b["l"] for b in window):
            lows.append({"t": bars[i]["t"], "price": bars[i]["l"]})
    return {"highs": highs, "lows": lows}


def snapshot(candles: Dict, atr_period: int = 14) -> Dict:
    """What a market read needs, from the bars alone: last price, range, ATR, the latest
    swing high and low, structure (higher lows / lower highs), and a measured-move
    projection if price breaks the recent range. Labels every derived number."""
    bars = candles["bars"]
    if len(bars) < 3:
        raise ValueError("need at least 3 bars")
    last = bars[-1]["c"]
    hi = max(b["h"] for b in bars)
    lo = min(b["l"] for b in bars)
    a = atr(bars, atr_period)
    sw = swings(bars)
    lows = [s["price"] for s in sw["lows"][-3:]]
    highs = [s["price"] for s in sw["highs"][-3:]]
    structure = "mixed"
    if len(lows) >= 2 and all(x < y for x, y in zip(lows, lows[1:])):
        structure = "higher lows"
    if len(highs) >= 2 and all(x > y for x, y in zip(highs, highs[1:])):
        structure = "lower highs" if structure == "mixed" else "higher lows and lower highs (compression)"
    height = hi - lo
    out = {
        "symbol": candles["symbol"], "interval": candles["interval"], "source": candles["source"],
        "as_of": candles["as_of"], "bars_used": len(bars), "last": last,
        "range": {"high": hi, "low": lo, "height": round(height, 8),
                  "position_pct": round((last - lo) / height * 100, 1) if height else None},
        "atr": {"value": None if a is None else round(a, 8), "period": atr_period, "pct_of_price": round(a / last * 100, 3) if a else None,
                "method": "Wilder ATR"},
        "swings": {"recent_highs": sw["highs"][-3:], "recent_lows": sw["lows"][-3:]},
        "structure": structure,
        "measured_move": {"if_break_up": round(hi + height, 8), "if_break_down": round(lo - height, 8),
                          "method": "range height added to the breakout level — a heuristic, not a forecast"},
    }
    if "note" in candles:
        out["note"] = candles["note"]
    return out


def position_size(account: float, risk_pct: float, entry: float, stop: float,
                  contract_size: float = 1.0) -> Dict:
    """Units so that a stop-out loses `risk_pct` of `account`."""
    account = finite("account", account, positive=True)
    risk_pct = finite("risk_pct", risk_pct, positive=True)
    entry = finite("entry", entry, positive=True)
    stop = finite("stop", stop, positive=True)
    contract_size = finite("contract_size", contract_size, positive=True)
    if risk_pct > 100:
        raise ValueError("risk_pct cannot exceed 100")
    if entry == stop:
        raise ValueError("entry and stop must differ")
    risk_cash = account * risk_pct / 100
    per_unit = abs(entry - stop) * contract_size
    units = risk_cash / per_unit
    return {"units": units, "risk_cash": risk_cash, "stop_distance": abs(entry - stop),
            "notional": units * entry * contract_size,
            "method": "units = account × risk% ÷ (|entry − stop| × contract size)"}
