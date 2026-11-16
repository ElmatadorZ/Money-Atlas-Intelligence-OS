# Money Atlas blind evaluation — 2026-11-16

Does installing Money Atlas Intelligence OS make answers better than answering without it?
Two rounds, same method. Everything needed to re-check the numbers is in this folder.

## Method

- **Answers.** Each answer was written by a fresh agent that saw only the question (no skill),
  or the question plus the skill folder (v2.0 or v2.1). Web search was off and no market data
  was supplied. One answer per question per condition, in `answers/<id>_<condition>.md`.
- **Rubric.** Ten criteria scored 0–2 (`rubric.md`), fixed before any answer was read.
- **Blind grading.** Answers were relabelled at random (`roundN/key.json`). Two independent
  graders scored every answer, checked facts with web search and ranked the answers per
  question. Grader B read questions and answers in reverse order.
- **Held-out questions.** `heldout.json` (H1–H4) was written and timestamped
  (`heldout_fixed_at.txt`) before any answer was read and before v2.1 was written.
  M1–M8 are the questions v2.1 was designed against.

Re-run the totals: `python evals/2026-11-16/aggregate.py`

## Round 1 — v2.0 vs no skill (M1–M8)

| | No skill | v2.0 |
|---|---|---|
| Total (of 160) | **152.0** | 141.0 |
| Ranked first (grader A / B) | 7 / 8 | 1 / 0 |

v2.0 already refused to invent prices (no fabrication 16.0 vs 14.5) and was stronger on
known/unknown (16.0 vs 12.5) and invalidation (16.0 vs 14.5). It lost on calibration
(10.0 vs 15.5: "~25%", "~95%" on a bond-math identity), proportion (7.5 vs 16.0: a full
framework around one-line concepts, an SMC map with no chart) and usefulness (14.5 vs 16.0:
asked for an entry, stop and target from a given price, it gave none).

## Round 2 — no skill vs v2.0 vs v2.1 (M1–M8 + held-out H1–H4)

| Question | No skill | v2.0 | v2.1 |
|---|---|---|---|
| M1 buy BTC now? (Thai) | 16.5 | 17.0 | **20.0** |
| M2 current Fed funds rate | **20.0** | 19.0 | **20.0** |
| M3 gold at $2,650: entry/stop/target | 19.0 | 16.5 | **19.5** |
| M4 nominal vs real rates | **20.0** | 18.5 | **20.0** |
| M5 age 30, 500k baht allocation (Thai) | **18.5** | 18.0 | **18.5** |
| M6 dollar crash from debt? | 18.0 | 16.5 | **20.0** |
| M7 "smart money" Tesla, all in? | 19.5 | 18.0 | **20.0** |
| M8 bond prices when yields rise | 19.5 | 17.0 | **20.0** |
| H1 does gold rise with inflation? *(held-out, Thai)* | **18.0** | **18.0** | 17.5 |
| H2 exact Sep 2026 CPI *(held-out)* | **20.0** | 19.0 | **20.0** |
| H3 start DCA into S&P 500 now? *(held-out)* | 19.0 | 17.5 | **20.0** |
| H4 backtest 300% / 2% drawdown *(held-out)* | 18.0 | 18.0 | **20.0** |
| **Total (of 240)** | 226.0 | 213.0 | **235.5** |
| Held-out only (of 80) | 75.0 | 72.5 | **77.5** |
| Ranked first (grader A / B) | 4 / 4 | 0 / 0 | **8 / 8** |

Per criterion (of 24, mean of two graders):

| Criterion | No skill | v2.0 | v2.1 |
|---|---|---|---|
| A1 accuracy | 22.0 | **23.5** | 22.5 |
| A2 no fabrication | 23.0 | **24.0** | **24.0** |
| A3 premise check | **24.0** | 23.0 | **24.0** |
| A4 known / unknown | 18.5 | **24.0** | 23.0 |
| A5 calibrated confidence | 23.5 | 14.0 | **24.0** |
| A6 alternatives | 23.5 | **24.0** | **24.0** |
| A7 risk and invalidation | 20.5 | **24.0** | 23.0 |
| A8 responsible scope | 23.5 | 23.5 | **24.0** |
| A9 usefulness | **24.0** | 22.0 | **24.0** |
| A10 proportion | **23.5** | 11.0 | 23.0 |

Graders differed by at most 2 points on any answer (mean 0.47).

## What is still open in v2.1

The 4.5 points v2.1 lost, from the graders' notes:

- **H1 (gold and inflation):** answered as a plain explanation, without an explicit
  known/inferred split or invalidation, and with a wrong detail: gold did not fall from about
  $2,000 to the $1,600s over 2022 (it started near $1,830, peaked near $2,070 in March and
  ended roughly flat). A myth-correcting mechanism question sits between DIRECT and LIGHT.
- **M5:** lists Thailand's SSF as a current tax-saving fund; its deduction ended after 2024.
  The skill marks figures by kind but not rules that may have changed since training.
- **M3, M5:** a little long.

## Limits

- Small sample: 12 questions, one answer per condition, two graders.
- The same no-skill and v2.0 answers scored differently in the two rounds (M1–M8: no skill
  152.0 → 151.0, v2.0 141.0 → 140.5). Compare conditions within a round.
- M1–M8 shaped v2.1, so the held-out H1–H4 are the fairer test (77.5 vs 75.0 and 72.5) — a
  smaller margin than on M1–M8 (158.0 vs 151.0 and 140.5).
- The rubric rewards proportion and grounded confidence, which v2.1 was designed for.
