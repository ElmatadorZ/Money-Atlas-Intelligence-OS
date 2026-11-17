# Money Atlas as an AI agent — architecture and build order

Analysis run with Genesis Mind (first principles → system map → agent council → scenarios →
decision), 17 Nov 2026. Goal: turn the Money Atlas skill into an agent that finds and connects
market data (Binance, MT5, stocks/indices, macro), exposes it over MCP, and becomes the base for
AI-assisted fund management and a trading bot.

Constraints given: **Claude Skill = brain, Python = body, never merged**; sovereign architecture
(no third-party frameworks); first deliverable = this plan + a working MCP data server; trading =
**paper only, with a human approving every order**.

---

## 1. First principles

| Assumption | Challenge | What survives |
|---|---|---|
| "More data makes the agent better." | The blind tests showed the skill's main failure was *invented or stale* numbers, not missing analysis. More unlabelled data adds more ways to be wrong. | **Every number must carry its source and time.** Provenance matters more than volume. |
| "An agent that can trade is the goal." | An LLM that can place orders turns one hallucination into a real loss; the cost is asymmetric. | **The model may propose; only a person may commit money.** Approval must live outside the model's reach. |
| "Integrate a framework (LangChain, ccxt, an MCP SDK) to move fast." | Each dependency is code you do not control, and a breaking change you do not choose. MCP is a small JSON-RPC protocol. | **Stdlib is enough** for the protocol, HTTP and CSV; only MT5 needs its vendor package, kept optional. |

## 2. System map

```
data sources ──► provider layer ──► MCP server ──► Claude + Money Atlas skill ──► answer / paper order
 (Binance,MT5,     (source, as_of,     (tools,         (Data Rules, QUANTIFY,          │
  Stooq, FRED)      typed errors)      staleness)       scenarios, invalidation)        ▼
      ▲                                                                       human approval (CLI)
      └──────────── feedback: paper P&L and post-mortems refine the skill ◄──────── paper ledger
```

- **Reinforcing loop (good):** sourced data → better-quantified answers → paper results →
  post-mortems → better skill rules.
- **Reinforcing loop (dangerous):** an agent that can act → more autonomy granted → larger
  unreviewed losses. **Damped** by: no execution tool, hard risk limits in code, kill switch, and a
  human CLI as the only approval path.
- **Leverage point:** the provenance contract (`source`, `as_of`, `stale`) between body and brain.
  It is cheap, and it turns the skill's existing Data Rules from "admit you don't know" into
  "fetch it and cite it".

## 3. Agent council

- **Analyst** — Data needed, by question type: spot and candles (crypto via Binance, gold/FX via
  MT5, equities/indices via Stooq end-of-day), macro (FRED). Gaps: Thai SET intraday (needs a
  licensed feed), options, order-book depth, news.
- **Strategist** — Ship the data layer as an MCP server inside the existing Claude Code plugin: one
  install gives the brain and the body, and the skill already has the rules to use it.
- **Skeptic** — The repository already shows the two failure modes this design must prevent:
  `integration/market_api.py` ignores the symbol it is given (always fetches BTC) and returns
  `None` on any error; `execution_engine.py` sends **live market orders** to Binance with no limit,
  check or approval. Neither should be wired to an agent. Free sources (Stooq, FRED CSV) have no
  service guarantee and can change format; broker MT5 prices differ between brokers.
- **Forecaster** — See scenarios below.
- **Executor** — Build order below.

## 4. Scenarios

| | Condition | Outcome |
|---|---|---|
| 🐂 Bull | Providers stay stable; paper results are logged and reviewed | Answers cite live data; a measured paper track record exists before any money is at risk |
| ⚖️ Base | A free source breaks or rate-limits occasionally | Typed errors surface it; the skill falls back to last-known-with-date; the provider is fixed |
| 🐻 Bear | An unattended agent is given execution later, or limits are loosened | Real losses from model error — prevented here by design, but only as long as the design holds |
| 💀 Black swan | A data source returns plausible but wrong prices (bad tick, wrong symbol) | Sizing and paper orders built on it. Mitigation: staleness flags, cross-source checks (next phase), human approval |

## 5. Decision

| Option | Trade-off | What breaks it |
|---|---|---|
| **A. Stdlib MCP data server inside the plugin, paper-only (chosen)** | Slower to add exotic sources; no trading | Free-source changes; needs a person in the loop |
| B. Third-party SDKs (MCP SDK, ccxt, broker SDKs) and live execution | Faster coverage, real automation | Dependency drift, framework lock-in, and model error becomes money lost |

**Recommendation: A**, under these conditions, any of which invalidates it if it fails:
1. No MCP tool may approve, send or execute an order (enforced by a test).
2. Risk limits live in code, not in the prompt.
3. Every figure the server returns carries `source` and `as_of` (enforced by tests and the skill).

Confidence: HIGH that A is safer; MEDIUM that free sources will be reliable enough without a paid
feed. Unknown: real-world rate limits from Thailand; MT5 broker symbol naming.

## 6. What is built now (`money_atlas_mcp/`, v0.1.0)

| Part | What it does |
|---|---|
| `providers.py` | Binance (public REST), Stooq (daily CSV), FRED (CSV, no key), MT5 (optional `MetaTrader5`, read-only), Fixtures (offline, labelled). Typed `ProviderError`, never a silent `None`. Router infers the source from the symbol. |
| `analytics.py` | Wilder ATR, fractal swings, structure (higher lows / lower highs), range position, measured-move projection, position sizing — each labelled with its method. |
| `paper.py` | Paper ledger: hard limits (1% risk per trade, 3 open, 3% daily loss, no leverage by default), stop-side check, kill switch file. Orders start `awaiting_approval`. |
| `approve.py` | The **only** approval path: a person at an interactive terminal enters an approval passphrase (PBKDF2-hashed); approvals are HMAC-signed and `--verify` detects ledger edits. |
| `server.py` | MCP over stdio (JSON-RPC 2.0, protocol 2025-06-18): 8 tools, staleness flags, server instructions that bind the skill's Data Rules. |
| `.claude-plugin/plugin.json` | Registers the server, so installing the plugin installs brain and body together. |

## 7. Build order

| Phase | Deliverable | Gate to move on |
|---|---|---|
| **0 (done)** | MCP data server, paper ledger, human approval, skill DATA TOOLS section, tests | Tests pass; server connects in Claude Code |
| 1 | Run it daily on real data; journal every paper order with the skill's scenario and invalidation | 30+ paper trades logged with entry, stop, exit, reason |
| 2 | Cross-source checks (e.g. Binance vs a second venue; MT5 vs a reference gold price); news/calendar provider | Disagreement above a threshold is flagged in the tool result |
| 3 | Portfolio module: holdings, exposure by asset/currency, rebalancing *proposals*, drawdown tracking — still paper | A quarter of paper results reviewed against a benchmark |
| 4 | Strategy research: backtests on the same bars the server serves (reuse `backtest/`), walk-forward, costs included | Out-of-sample results that survive costs |
| 5 | Only then, and only if you decide to: live execution behind the same approval CLI, small fixed size, broker-side stop, daily loss limit, kill switch | Paper record, written risk policy, and a person approving every order |

**Security boundary (from the red team, `evals/2026-11-17-mcp-redteam/`).** An agent running as the
same OS user with a shell can rewrite or delete `~/.money_atlas`. It cannot approve without the
passphrase, and edits are detected, but before phase 5 approval must move to a channel the agent
cannot reach (a separate OS user or a second device).

Retire or isolate `execution_engine.py` (live orders, no limits) and `integration/market_api.py`
(ignores its symbol) before wiring anything else to an agent.
