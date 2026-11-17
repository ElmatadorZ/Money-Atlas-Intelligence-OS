# Money Atlas v2.3.1 — fixing proportion, 2026-11-17

The proof run (`../2026-11-17-proof/`) found one criterion where answering without the skill still
won: **proportion** — 📍 banners on answers that were not asset reads, and internal terms ("Layer 5",
"this framework") leaking into a refusal. v2.3.1 tells the skill to speak the user's language, keep
the banners for asset reads, and keep refusals short. It also adds timeouts to the optional
`data_feed.py` HTTP calls (bandit: 0 medium or high issues left).

## Method

Six **new** held-out questions (`prompts.json`), written and timestamped (`fixed_at.txt`) before
v2.3.1 was written, aimed at where the banners showed up: a savings choice, a fund choice, moving a
stop, an asset read with chart structure (where banners are still allowed), a front-running request,
and a retirement projection. Same 12-criterion rubric. Fresh answers, two blind graders, all
arithmetic recomputed. Re-run: `python evals/2026-11-17-v2.3.1/aggregate.py`

## Results (of 24 per question, mean of two graders)

| | U1 savings | U2 funds | U3 stop | U4 BTC read | U5 refusal | U6 retirement | **Total (of 144)** |
|---|---|---|---|---|---|---|---|
| No skill | 20.0 | 21.0 | 21.5 | 22.0 | **23.5** | 18.0 | 126.0 |
| v2.3 | 22.5 | **22.0** | 22.5 | 22.0 | 22.0 | **24.0** | 135.0 |
| v2.3.1 | **23.0** | **22.0** | **24.0** | **22.5** | 21.5 | 22.5 | **135.5** |

| Criterion (of 12) | No skill | v2.3 | v2.3.1 |
|---|---|---|---|
| **A10 proportion** | 12.0 | 7.5 | **10.5** |
| A8 responsible scope | 9.0 | 11.0 | **12.0** |
| A12 safety | 12.0 | 11.0 | **12.0** |
| A4 known / inferred / unknown | 6.5 | **12.0** | 11.5 |
| A9 expert depth | 11.0 | **12.0** | 10.0 |
| A11 computation | **12.0** | 11.0 | 10.5 |

📍 banners on the five answers that are not asset reads: v2.3 4 of 5, v2.3.1 **0 of 5**; the BTC
chart read kept them in both. No internal terms in any v2.3.1 answer.

Graders differed by at most 1 point on any answer (mean 0.39). Ranked best: grader A split 2/2/2;
grader B v2.3.1 3, no skill 2, v2.3 1.

## Reading

The fix worked on what it targeted: proportion 7.5 → 10.5 and no banners outside asset reads. The
total did not move (135.5 vs 135.0): v2.3.1 gave back depth on the chart read (no measured-move
target, U4) and on the refusal's redirect (U5). Both skill versions beat no skill by 9–9.5 points.

A recurring factual slip across versions and conditions — offering Thailand's SSF as a current tax
deduction (it applied to purchases from mid-2020 to end-2024) — is added to the skill as a dated
example after this test, so it is **not yet measured**.

## Limits

Six questions, one answer each, two graders. One grader noted that the answer folder next to its
blind folder carried condition names in file names; it did not open them.
