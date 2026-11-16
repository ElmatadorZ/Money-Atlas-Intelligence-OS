# Changelog

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
