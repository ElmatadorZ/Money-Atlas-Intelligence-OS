# Changelog

## [2.4.0] — 2026-11-17 — The data agent

- **`money_atlas_mcp/`**: a stdlib-only MCP server (JSON-RPC 2.0 over stdio) registered by the
  plugin. Providers: Binance (public), MetaTrader 5 (optional package, read-only), Stooq (daily),
  FRED (CSV), offline fixtures. Tools: `get_quote`, `get_candles`, `get_macro_series`,
  `market_snapshot`, `position_size`, `paper_propose_order`, `paper_orders`. Every result carries
  `source`, `as_of` and `stale`; failures are typed errors, never a silent `None`.
- **Paper trading with human-only approval**: hard limits in code (1% risk per trade, 3 open, 3%
  daily loss, no leverage), stop-side check, kill switch; approval only via
  `python -m money_atlas_mcp.approve`. No tool can approve or send an order (tested).
- **SKILL.md DATA TOOLS** section: fetch before reasoning, quote source and time, paper-only orders,
  say which source failed instead of guessing.
- `docs/AGENT_ARCHITECTURE.md`: the Genesis Mind analysis, decision and build order.
- 71 tests (25 for the server, run offline with recorded responses).

## [2.3.1] — 2026-11-17 — Speak the user's language

- **No internal machinery in answers**: no mode names, "Market Core", "L1–L5"/"Layer 5" or "this
  framework"; say it in plain words.
- **📍 banners only for asset reads**; personal-money decisions, trade mechanics and refusals are
  prose or plain headings.
- **Refusals** (manipulation, insider or front-running trades, "guaranteed" signals): one or two
  plain sentences, then the legitimate alternative — no framework, no lecture.
- Dated example of a changed rule: Thailand's SSF deduction (mid-2020 to end-2024).
- `data_feed.py`: HTTP timeouts (bandit: no medium or high issues).
- Measured on six new held-out questions (`evals/2026-11-17-v2.3.1/`): proportion 7.5 → 10.5 of 12,
  no banners outside asset reads; total 135.5 vs v2.3 135.0 vs no skill 126.0 (of 144).

## 2026-11-17 — Proof run (no skill change)

Fresh re-run of v2.3 on every held-out question with new graders, plus safety, activation, code
scan and install checks (`evals/2026-11-17-proof/`). Quality 328.0 / 336 vs 307.0 without the
skill; repeatability within 2.5 points of the first run; all harmful requests refused; activation
16/16 with 0/8 false triggers, the same as v2.0; 0 high-severity code-scan issues.

## [2.3.0] — 2026-11-16 — Claude Code plugin

- Install from the Claude Code CLI:
  `/plugin install money-atlas-intelligence-os --marketplace ElmatadorZ/Money-Atlas-Intelligence-OS`,
  or `claude plugin marketplace add ElmatadorZ/Money-Atlas-Intelligence-OS` then
  `claude plugin install money-atlas-intelligence-os@elmatadorz-money-atlas`.
- `.claude-plugin/plugin.json` (2.3.0) and `marketplace.json` (`elmatadorz-money-atlas`, so it can
  sit beside the other ElmatadorZ marketplaces).
- `skills/money-atlas-intelligence-os/` holds SKILL.md and every file it loads, kept identical to
  the root by `tools/sync_plugin_skill.py`, a test and a CI job that runs
  `claude plugin validate --strict`.

## [2.3] — 2026-11-16 — Passes a professional-level test

A harder evaluation (`evals/2026-11-16-hard/`: CFA-level grading, recomputed arithmetic, a new
criterion for computation and data use) found v2.2 described calculations instead of doing them
and stated that a recent event "has never happened".

### Added
- **QUANTIFY WHAT THE DATA ALLOWS**: sizing and leverage, plan sufficiency and drawdown, the
  expected cost of each choice (DCA, fees, tax, real return), pricing formulas with their
  convention (and the other convention's number), and — when a point forecast is demanded — the
  honest best estimate (spot or forward) with a volatility range instead of a bare refusal.
- **Absence claims are dated**: never "has never happened" about recent history; "as far as my
  data goes".

### Measured
Held-out T1–T6 (of 132): no skill 118.5, v2.0 118.0, v2.2 128.0, **v2.3 131.5**; ranked best
answer 5 of 6 (grader A) and 6 of 6 (grader B). Dev set D1–D10 (of 220): no skill 178.5,
v2.0 198.0, v2.2 208.0.

## [2.2] — 2026-11-16 — The two misses from round 2

### Changed
- A question that asks why something "always" or "every time" happens is no longer DIRECT: the
  claim inside it is tested with the Market Core (what the evidence shows, when it held and
  failed, how to tell the regime), written as prose without the LIGHT banners.
- **Historical figures** follow the Data Rules: quote a level or date only when sure, otherwise
  describe the move without the number.
- **Rules and products change**: tax schemes and limits, regulations, fund availability, fees and
  tickers are dated last-known facts, with the official source to confirm.
- FULL mode target length ~600 words (was ~700).

### Measured
Round 3, four fresh held-out questions: no skill 74.5, v2.1 78.0, v2.2 76.5 of 80. Both skill
versions beat no skill; v2.2 did not beat v2.1 (within noise on 4 questions). The prose rule
for myth questions was added after round 3 and is not yet measured. See `evals/2026-11-16/`.

## [2.1] — 2026-11-16 — Measured, then fixed

A blind A/B test of v2.0 (`evals/2026-11-16/`) found that answers written with the skill
scored **lower** than answers written without it (141.0 vs 152.0 of 160). v2.0 already refused
to invent prices; it lost on calibration, proportion and usefulness. v2.1 fixes the causes.

### Changed
- **DIRECT mode**: a concept, definition or settled fact gets a plain answer — no banners,
  scenarios or confidence field. LIGHT and FULL show only sections with real content.
- **Market Core**: the five moves every LIGHT and FULL answer carries (premise, known/unknown,
  scenarios with triggers, risk and invalidation, confidence with basis).
- **SMC layer** only when there is price-structure data; otherwise one line naming the input
  that would place it. A layer is a hypothesis about structure, not a fact about intent.
- **Data Rules**: every figure is given (and sanity-checked), last known (with its date) or
  `[ASSUMED]`. "Abstain from facts, not from method": trade levels are built from the user's
  price plus labelled assumptions, with the arithmetic shown.
- **Confidence Rules**: HIGH / MEDIUM / LOW with its basis; a % only when computed. Identities
  are stated as fact.
- **Personal money decisions**: name the deciding personal facts, never endorse all-in,
  concentration or leverage.
- The description no longer says "ALWAYS trigger — do not skip"; when Genesis Protocol (the
  router skill) is installed, it decides when this runs.
- Worked examples, `full_mode.txt`, `light_mode.txt`, `system_prompt.txt` and
  `session_boot.txt` updated to match (no bare `X%`); new `examples/worked/04-concept-direct-mode.md`.

### Added
- `evals/2026-11-16/`: prompts, rubric, all 36 answers, both graders' scores and keys.
- Contract tests and validator checks for all of the above, including that every file SKILL.md
  points to exists case-exactly (30 tests, 26 validator checks).

Round 2 (12 questions incl. 4 held-out): no skill 226.0, v2.0 213.0, v2.1 235.5 of 240;
held-out 75.0 / 72.5 / 77.5.

## [2.0]

Initial public version.
