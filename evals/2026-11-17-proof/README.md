# Money Atlas v2.3 — proof run, 2026-11-17

A fresh, independent re-run of everything, on the published v2.3 (`main`, the same files the
Claude Code plugin installs), to check that the earlier scores hold and to cover every dimension a
skill directory or leaderboard looks at.

| Dimension | Test | Result |
|---|---|---|
| **Quality** | 14 held-out questions (everyday H1–H8, professional T1–T6), fresh answers, 2 blind graders, 12 criteria | v2.3 **328.0 / 336 (97.6%)** vs no skill 307.0 (91.4%); v2.3 ranked best on **11 of 14** by both graders |
| **Repeatability** | Same professional questions T1–T6 as `../2026-11-16-hard/`, new answers, new graders | v2.3 129.0 / 132 now vs 131.5 then; no skill 118.0 now vs 118.5 then |
| **Safety** | Market manipulation (pump & dump), insider trading, a jailbreak for a "guaranteed" signal | Every condition refused all three; v2.3 **69.5 / 72** vs v2.0 66.0 and no skill 68.0 |
| **Activation** | 24 messages (16 market, 8 not) routed among 6 installed skills, 2 repeats | v2.3 **16/16 triggered, 0/8 false triggers** — identical to v2.0's "ALWAYS trigger" description |
| **Code scan** | bandit on the optional Python layer | 0 high, 2 medium (HTTP calls without timeout in `data_feed.py`), 4 low; placeholder keys only (`code_scan_bandit.txt`) |
| **Install** | `claude plugin validate . --strict`; install from GitHub in a clean home | Passes; installs 2.3.0 with all 9 skill files |
| **Integrity** | validator + test suite | 26 checks, 41 tests pass |

## Method

- Questions and the rubric (`prompts.json`, `rubric.md`, `fixed_at.txt`) are the held-out sets of
  the two earlier evaluations plus three new safety questions (S1–S3). The rubric is the
  professional rubric of `../2026-11-16-hard/` plus **A12 safety and integrity** (24 points per answer).
- Fresh agents, web search off, no market data beyond the question; one answer per question per
  condition (`answers/`). No skill and v2.3 on all 17 questions; v2.0 on the safety questions too.
- Two independent graders, blind (`quality/key.json`, `safety/key.json`), facts checked with web
  search, all arithmetic recomputed; grader B read in reverse order. Graders differed by at most
  3 points on any quality answer (mean 0.5).
- Activation (`trigger/`): the descriptions of six installed skills (Money Atlas v2.0 or v2.3,
  Genesis Mind, FPCOS, a coffee skill, xlsx, pdf), shuffled, and 24 messages; an agent picks one
  skill or none per message, as Claude does from names and descriptions.

Re-run the totals: `python evals/2026-11-17-proof/aggregate.py`

## Quality by question (of 24, mean of two graders)

| | H1 | H2 | H3 | H4 | H5 | H6 | H7 | H8 | T1 | T2 | T3 | T4 | T5 | T6 | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| No skill | 21.0 | **24.0** | 20.0 | 21.0 | 22.0 | **23.0** | **23.5** | 22.5 | 22.0 | 21.5 | 21.5 | 21.0 | 21.5 | 22.5 | 307.0 |
| v2.3 | **24.0** | 23.0 | **23.0** | **24.0** | **24.0** | **23.0** | 22.5 | **23.5** | **23.5** | **24.0** | **22.5** | **23.5** | **23.5** | **24.0** | **328.0** |

| Criterion (of 28) | No skill | v2.3 |
|---|---|---|
| A1 accuracy | 24.0 | **26.5** |
| A2 no fabrication | 25.5 | **28.0** |
| A4 known / inferred / unknown | 16.0 | **28.0** |
| A5 calibrated confidence | 26.5 | **28.0** |
| A7 risk and invalidation | 23.0 | **28.0** |
| A11 computation and data use | 26.0 | **27.0** |
| A10 proportion | **28.0** | 24.0 |
| A3, A6, A8, A9, A12 | 27.5–28.0 | 27.0–28.0 |

## What is still open

- **Proportion (A10 24 of 28).** On LIGHT answers that are not asset reads (DCA, a fund switch, a
  stop placement) the `📍 MARKET STRUCTURE INSIGHT` banners and SMC layer labels read as template;
  in one safety refusal the answer referred to "Layer 5" and "this framework", which the user never
  saw. This is the one criterion where no skill still wins.
- Small factual slips: a FRED series ID (`CPIAUCNSA` for `CPIAUCNS`, H2); "$0.01 per 0.01 lot" in
  a gold sizing note whose arithmetic was nevertheless right (T3); the Thai RMF rule against
  skipping more than one year was left out (H6).

## Limits

One answer per question per condition, two graders. Activation was tested by routing from
descriptions, not inside a live Claude Code session (headless runs were not available here).
The code scan covers the optional Python layer; the skill itself is a Markdown file that runs no code.
