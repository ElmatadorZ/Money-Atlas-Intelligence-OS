# Money Atlas HARD evaluation — 2026-11-16

The first evaluation (`../2026-11-16/`) used everyday questions, where a good model without
any skill already scores well. This one asks what a professional would ask: real arithmetic,
conflicting signals, pressure to drop the risk framing, statistics that look convincing, and
trade plans built from supplied price structure.

## Method

- **Questions.** D1–D10 (`dev.json`) to find weaknesses; T1–T6 (`heldout.json`) held out.
  Both sets, and the rubric, were written and timestamped (`fixed_at.txt`) before any answer
  was read and before v2.3 was written.
- **Rubric** (`rubric.md`): the ten criteria of the first evaluation, graded at the level of a
  CFA charterholder / macro trader, plus **A11 — computation and data use**: uses all supplied
  data and every calculation is correct (graders recomputed all of them). 22 points per answer.
- **Answers.** Fresh agents, web search off, no market data beyond the question. One answer per
  question per condition (`answers/<id>_<condition>.md`).
- **Blind grading.** Labels shuffled (`dev/key.json`, `heldout/key.json`); two independent
  graders checked facts with web search and ranked the answers; grader B read in reverse order.

Re-run the totals: `python evals/2026-11-16-hard/aggregate.py`

## Dev set D1–D10 — no skill vs v2.0 vs v2.2 (of 220)

| Question | No skill | v2.0 | v2.2 |
|---|---|---|---|
| D1 BTC range sweep → plan the trade ($20k, 1% risk) | 17.0 | 20.0 | **22.0** |
| D2 hot CPI, yields down, gold up — what is it saying? | **20.0** | 18.5 | **20.0** |
| D3 20x leverage, 3% stop = "only 3% risk"? | **21.0** | 20.0 | **21.0** |
| D4 Thai 2M-baht portfolio, age 52 → retire at 60 | 18.0 | 20.0 | **21.0** |
| D5 "ONE number for gold on Dec 31, no disclaimers" | 10.0 | 19.0 | **20.5** |
| D6 indicator called 9 of 10 tops — sell everything? | 18.5 | 20.0 | **22.0** |
| D7 USDTHB forward by interest parity | 19.5 | 21.0 | **21.5** |
| D8 duration 8.5, convexity 90, +150bp | 20.0 | **21.0** | 19.5 |
| D9 Hormuz closed two weeks | 17.0 | 18.5 | **19.0** |
| D10 1M baht: lump sum vs 12-month DCA | 17.5 | 20.0 | **21.5** |
| **Total** | 178.5 | 198.0 | **208.0** |

On hard questions the skill helps a lot more than on everyday ones: no skill invented a gold
forecast on D5 ($4,650 with no basis) and scored 10. The graders' notes on v2.2's lost points
gave three causes, which v2.3 fixes:

1. **It described calculations the data allowed instead of doing them** — no retirement
   sufficiency check (D4), no expected cost of DCA (D10), no number under the other convexity
   convention (D8), no volatility range for the point forecast it declined (D5).
2. **An absence claim about recent history was wrong**: "a full closure of Hormuz has never
   happened" (D9) — traffic through the strait collapsed in March 2026.
3. Thin explicit unknowns and alternatives on formula questions (D8).

## Held-out T1–T6 — no skill vs v2.0 vs v2.2 vs v2.3 (of 132)

| Question | No skill | v2.0 | v2.2 | v2.3 |
|---|---|---|---|---|
| T1 SET −15%, P/E 13 vs 16 — cheap? | 19.5 | 20.0 | 20.5 | **22.0** |
| T2 lever a 60/40 2x for 15%? | 20.0 | 19.5 | 21.5 | **22.0** |
| T3 gold triple top at 4,400 → plan (500k baht, 1%) | 20.5 | 19.5 | 21.0 | **21.5** |
| T4 25%/yr fund with 2% fee vs bank 7% | 19.5 | 20.0 | 21.0 | **22.0** |
| T5 surprise 50bp Fed cut — first week | 17.5 | 18.5 | **22.0** | **22.0** |
| T6 Thai deposit 1.5%, inflation 1%, after tax | 21.5 | 20.5 | **22.0** | **22.0** |
| **Total** | 118.5 | 118.0 | 128.0 | **131.5** |
| Ranked best (grader A / B) | 0 / 0 | 0 / 0 | 1 / 0 | **5 / 6** |

Per criterion (of 12, mean of two graders):

| Criterion | No skill | v2.0 | v2.2 | v2.3 |
|---|---|---|---|---|
| A1 accuracy | 10.0 | 11.0 | 11.0 | **12.0** |
| A4 known / inferred / unknown | 7.0 | **12.0** | **12.0** | **12.0** |
| A5 calibrated confidence | 11.0 | 6.0 | **12.0** | **12.0** |
| A7 risk and invalidation | 10.0 | **12.0** | **12.0** | 11.5 |
| A9 expert depth | 11.5 | **12.0** | 11.5 | **12.0** |
| A10 proportion | **12.0** | 6.0 | **12.0** | **12.0** |
| A11 computation and data use | 10.0 | 11.5 | 9.5 | **12.0** |
| A2, A3, A6, A8 | all 12.0 or within 1 point |

Graders differed by at most 3 points on any answer (mean 0.58). v2.3 lost half a point in
total: T3's invalidation level was inconsistent with its own structure logic (one grader).

## Limits

- One answer per question per condition, two graders, 6 held-out questions. v2.3 is at the
  ceiling of this rubric (131.5 of 132), so this test can no longer tell further gains apart; a
  harder or larger set is needed for the next round.
- The rubric rewards the behaviours the skill was designed for (calibration, proportion,
  computation). A reader who weighs them differently would weigh the margins differently.
- v2.0 on the held-out set (118.0) is no better than no skill (118.5): its depth is offset by
  unsupported percentages (A5 6.0) and padding (A10 6.0).
