"""Money Atlas data agent — the "body" that feeds the Money Atlas skill (the "brain").

A stdlib-only MCP server (JSON-RPC 2.0 over stdio) that finds and fetches market data
(Binance, MetaTrader 5, Stooq, FRED), computes the numbers the skill's
QUANTIFY rule needs, and runs a paper-trading ledger whose orders only a human can
approve, from a separate command, outside the chat.

Every figure it returns carries its source and an `as_of` timestamp, so the skill can
label it as *given* data under its Data Rules.
"""
from __future__ import annotations

__version__ = "0.1.0"
