# Money Atlas Intelligence OS
### Claude Skill (Agent) — Financial Market Strategic Intelligence

**Version:** 2.1  
**Author:** Bunyawat Dechanon (ElmatadorZ)  
**Brand:** Money Atlas / Alternative Slowbar  
**Type:** Custom Skill (SKILL.md format)

---

## What This Is

A skill that transforms financial market questions into structured, scenario-based intelligence.

Not a prediction engine.  
Not a signal bot.  
A thinking system — built to reason the way a disciplined analyst does.

When you ask about BTC, gold, macro, forex, or any asset — this skill activates a multi-layer reasoning pipeline that separates what's actually happening from what the market narrative wants you to believe.

---

## Core Engine

### Genesis Protocol — 3-Step Thinking Pipeline

**Step 1: First Principle Codex**
Deconstruct the market from root causes — not price action alone.
- What is *actually* happening?
- Why is price/macro moving this way?
- What is the structural driver?
- Where is the asymmetric opportunity?
- What happens next under each scenario?

**Step 2: System Thinking — Micro → Macro**
- Micro: Asset-specific technicals, on-chain data, positioning
- Meso: Sector rotation, correlated assets, sentiment
- Macro: Fed, DXY, liquidity cycle, geopolitics
- Meta: What narrative is the market constructing — and who benefits?

**Step 3: AI Fluency 4D**
- Delegation — Pattern recognition across data
- Description — Convert market noise → structured signal
- Discernment — Question bias, timeframe, missing information
- Diligence — Human makes the final decision. Always.

---

### SMC Layer — Smart Money Cycle Map

Identifies where price is in the institutional cycle:

| Layer | Phase | What's Happening |
|---|---|---|
| L1 | Accumulation | Quiet buying, engineered fake breakdowns |
| L2 | Expansion | Breakout, momentum building |
| L3 | Decision Zone | High-stakes inflection point |
| L4 | Distribution | Quiet selling, engineered fake breakouts |
| L5 | Exit Liquidity | Retail buys tops, institutions exit |

With price-structure data, an analysis maps the current layer + next probable move + invalidation condition. Without it, the skill says the layer cannot be placed and names the input that would place it.

---

## Output Modes

Pick the smallest mode that carries the answer. Auto-detected; override with `FULL`, `LIGHT` or `short`.

| Mode | When | Shape |
|---|---|---|
| **DIRECT** | A concept, definition, mechanism or settled fact | A plain answer — no banners, scenarios or confidence field |
| **LIGHT** | One asset, a quick view, a premise to check | The Market Core in a few paragraphs (~300 words) |
| **FULL** | An investment or allocation decision, a trading plan, a macro thesis | The template below, only the sections with real content (~700 words) |

Every LIGHT and FULL answer carries the **Market Core**: the premise checked, known vs unknown
(including what cannot be known without live data), at least two scenarios with triggers, the risk
and its invalidation, and confidence stated with its basis.

```
📍 SITUATION MAP          given inputs, last known context with its date, unknowns
📍 FIRST PRINCIPLE BREAKDOWN
📍 SYSTEM MAP (Macro → Liquidity → Asset → Price)
📍 SMC LAYER MAP          only when there is price-structure data to read
📍 NARRATIVE INTELLIGENCE the story, who benefits, the evidence that tests it
📍 SCENARIOS
   🐂 Bull: [trigger | target | condition]
   🐻 Bear: [trigger | target | condition]
   ⚖️ Base: [most probable path, and why]
📍 DECISION FRAMEWORK
📍 RISK & FAILURE MODE
   CONFIDENCE: [HIGH / MEDIUM / LOW — basis] | KEY UNKNOWNS: [list]
```

**Data Rules.** Every figure is *given* (from the user, sanity-checked), *last known* (with its
date, never presented as current) or *assumed* (labelled `[ASSUMED]`, with the arithmetic shown).
Anything else is invented. Asked for an entry, stop and target from a single price, the skill builds
them from that price plus labelled assumptions instead of refusing.

**Confidence.** HIGH / MEDIUM / LOW with its basis; a percentage only when it is computed from a
stated base rate, model or data.

---

## Test results — with the skill vs without it

Fresh agents answered the same questions with no skill, with v2.0 and with v2.1, without web access
or live data. Two independent graders scored every answer blind against a fixed 10-criterion rubric
and checked the facts with web search. Everything is in
[`evals/2026-11-16/`](evals/2026-11-16/README.md): prompts, rubric, all 36 answers, both graders'
scores, the unblinding keys and `aggregate.py`.

**Round 1 found v2.0 made answers worse:** 141.0 vs 152.0 of 160 without the skill, and the graders
preferred the no-skill answer on 15 of 16 calls. v2.0 already refused to invent prices, but it wrapped
concept questions in the full framework, forced an SMC map onto questions with no chart, put
unsupported percentages on its confidence, and refused to build trade levels from the price given.
v2.1 fixes those causes and was re-tested with 4 held-out questions written before v2.1 existed.

| Round 2 (12 questions, 2 graders) | No skill | v2.0 | **v2.1** |
|---|---|---|---|
| Total (of 240) | 226.0 | 213.0 | **235.5** |
| Held-out questions only (of 80) | 75.0 | 72.5 | **77.5** |
| Ranked best answer (grader A / B) | 4 / 4 | 0 / 0 | **8 / 8** |

| Criterion (of 24) | No skill | v2.0 | **v2.1** |
|---|---|---|---|
| No fabrication | 23.0 | 24.0 | **24.0** |
| Known / unknown | 18.5 | 24.0 | 23.0 |
| Calibrated confidence | 23.5 | 14.0 | **24.0** |
| Risk and invalidation | 20.5 | 24.0 | 23.0 |
| Usefulness | 24.0 | 22.0 | **24.0** |
| Proportion (length fits question) | **23.5** | 11.0 | 23.0 |

Still open: one held-out mechanism question (does gold rise with inflation?) scored 17.5, below both
other conditions — it was answered as a plain explanation, without an explicit known/inferred split
or invalidation, and with a wrong detail about gold's 2022 path. Facts that changed after training
(Thailand's SSF tax deduction ended after 2024) still slip through. Limits: 12 questions, one answer
each, two graders; M1–M8 shaped v2.1, so the held-out rows are the fairer comparison.

---

## Trigger Topics

This skill activates when you ask about:

- **Crypto:** BTC, ETH, altcoins, on-chain data
- **Commodities:** Gold, silver, oil, soft commodities
- **Macro:** Fed policy, interest rates, inflation, DXY, liquidity cycles
- **Equities:** Stocks, indices, sector rotation
- **Forex:** Currency pairs, emerging markets
- **Geopolitics:** Events affecting market structure
- **Strategy:** Portfolio allocation, risk management, entry/exit frameworks

---

## What This Skill Does NOT Do

- Give single-point price predictions without scenarios
- Express certainty without evidence
- Omit the risk or invalidation condition
- Tell you what to do — it gives you a framework to decide

If output violates any of these → the system flags `⚠️ INSUFFICIENT EDGE` and re-evaluates before responding.

---

## Architecture

```
Input (market question)
│
├── Genesis Protocol
│   ├── First Principle Codex (root cause decomposition)
│   ├── System Thinking (micro → macro chain)
│   └── AI Fluency 4D (bias check + discernment)
│
├── SMC Layer Engine
│   ├── Market structure mapping
│   ├── Liquidity zone identification
│   └── Smart money vs. retail narrative separation
│
├── Scenario Engine
│   ├── Bull / Bear / Base case
│   ├── Entry-exit zones
│   └── Invalidation conditions
│
└── Output (LIGHT or FULL mode)
```

---

## File Structure

```
money-atlas-intelligence-os/
├── SKILL.md                    ← Claude skill definition (main entry point)
├── skill_config.json           ← Skill metadata and trigger config
├── architecture.md             ← System architecture overview
├── system_prompt.txt           ← Session boot prompt
├── full_mode.txt               ← Full mode output spec
├── light_mode.txt              ← Light mode output spec
│
├── core/                       ← Genesis Protocol engine
│   ├── genesis_core.py
│   ├── ai_fluency_4d.py
│   ├── discernment_engine.py
│   └── decision_engine.py
│
├── agents/                     ← Specialist agent layer
│   ├── orchestrator.py
│   ├── analyst_agent.py
│   ├── macro_agent.py
│   ├── smc_agent.py
│   ├── risk_agent.py
│   ├── sentiment_agent.py
│   ├── skeptic_agent.py
│   └── strategist_agent.py
│
├── smc/                        ← Smart Money Concept engine
├── intelligence/               ← Alpha, macro, geopolitics engines
├── strategy/                   ← Scenario + asymmetric opportunity engine
├── execution/                  ← Signal, risk, trade logging
├── orchestrator/               ← Multi-agent coordination
├── cli/                        ← Command-line runners
│
├── tests/                      ← unit tests for the reasoning engines + skill contract
├── evals/2026-11-16/           ← blind A/B test: prompts, answers, grades, aggregate.py
├── examples/                   ← worked input→output examples + runnable demo
│   └── worked/
└── tools/validate_skill.py     ← installability + integrity checker (run in CI)
```

---

## How to Install (Claude Custom Skill)

1. Clone or download this repository
2. Place the `money-atlas-intelligence-os/` folder in your Claude skills directory
3. The skill activates automatically when Claude detects relevant financial market questions
4. Or call it explicitly by referencing the skill name in your system prompt

The skill entry point is **`SKILL.md`** (the Anthropic standard filename). The reasoning is
self-contained in that file and needs no tools to run — see `metadata.compatibility` in its
frontmatter. The Python modules are an optional execution layer.

---

## Verifying it before you trust it

Two things are checked on every push, and you can run both locally:

```bash
pip install pytest pyyaml

python tools/validate_skill.py   # frontmatter, license, and safety structure intact
python -m pytest -q              # unit tests over the reasoning engines + skill contract
```

The tests are not decorative. They pin the gates that would cost money if they drifted — a BUY
signal only on high-confidence accumulation, risk raised on distribution, First Principle truths
kept separate from inference — and the skill's own promises: every scenario carries an invalidation
condition, the skill abstains rather than invent a price when it has no data, concept questions get a
plain answer, confidence carries its basis, and every file SKILL.md points to exists. See
[`examples/worked/`](examples/worked/) for what the output looks like in each case, including the
[insufficient-data case](examples/worked/03-insufficient-data.md) where the correct answer is to
decline.

---

## Non-Negotiable Constraints

Every market read or decision must include (a concept question gets a plain answer instead):

- **Multiple scenarios** — no single prediction
- **Explicit uncertainty** — confidence level with its basis + key unknowns
- **No invented figures** — every number given, last known with its date, or labelled `[ASSUMED]`
- **Invalidation point** — what breaks the entire analysis
- **Human decision primacy** — the skill advises, the human decides

Violation of any constraint → output is invalid → re-evaluate.

---

## Part of the Skynet Skill Ecosystem

This skill operates within the broader **Skynet Elite Commander** meta-intelligence system:

| Skill | Domain |
|---|---|
| `skynet-elite-commander` | Meta-cognition OS — routes all domains |
| `money-atlas-intelligence-os` | Financial markets, macro, trading |
| `alternative-coffee-intelligence` | Coffee science and roastery operations |
| `genesis-mind-strategic-intelligence` | Strategic thinking, business, philosophy |
| `first-principle-codex-os` | Anti-hallucination cognitive base layer |

---

## ⚠️ Not financial advice

This system **analyses** markets. It does not advise. Its output is structured scenarios with
explicit uncertainty — an analytical instrument, not a recommendation, and it can be wrong.
You are solely responsible for your own decisions. Consult a licensed financial adviser before
acting on any output, and never deploy it against capital you cannot afford to lose.
See [NOTICE](NOTICE) and the warranty disclaimer in the [LICENSE](LICENSE).

---

## License

**[Apache License 2.0](LICENSE)** — OSI-approved, with an express patent grant. Free to use,
modify, and redistribute, including commercially at any revenue. Keep the licence and
[NOTICE](NOTICE), and state any changed files.

Attribution is requested (not required beyond NOTICE):
**Built on Money Atlas Intelligence OS by Bunyawat Dechanon (ElmatadorZ)**

Apache §6 grants no rights to the name: a derivative that removes the uncertainty disclosure,
the scenario structure, or the refusal to present analysis as advice must be renamed.

*(Earlier releases used the custom Open Cognitive License v1.0 with a 2% clause above $10M/year;
it was replaced to remove adoption friction. Prior text is in the git history.)*

---

## Author

**Bunyawat Dechanon**  
Independent Builder & Architect  
Brand: Alternative Slowbar / Money Atlas  
Location: Thailand

> *"The market is always telling a story. This skill helps you read who wrote it."*
