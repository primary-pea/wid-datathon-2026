# Changelog

## v2.0 (12 September 2026) — the frozen submission version, data version `afe63e46c26b`

- Exposure: the main dose is the number of anaemia-cluster **policies** in force (dated adoption years) instead of the team's six-flag composite; programme rows (questionnaire answers dated by survey round) stay in the profiles. Alternative constructions remain as ladder rows and in the specification curve.
- Event studies (`02b`): first dated anaemia policy and the GFDx wheat-flour mandate; two-way FE, two-stage DiD, local-projections DiD; negative-weight diagnostic; pre-trend slope adjustment.
- Ladder (`02`): first-difference, long-difference and lagged-outcome rows (the bracket); the context block (malaria, fertility, urbanisation, HIV); unemployment and employment rows; hospital beds, health expenditure and the FIES women-minus-men gap in the sub-sample block; pregnant-women anaemia and a women's summary index among the outcome swaps with Benjamini–Hochberg adjustment; a survey-anchored row.
- Specification curve (`02c`), context ranking with terrain and sub-region (`04`), a bootstrap interval on the leave-one-country-out difference (`03`), the concern-score reproduction (`08`) and the DML sidebar (`09`).
- Implementation contrast (13 September): delivered deworming coverage among school-age children from the WHO PCT databank as an exposure row and a sub-sample control, next to the paper record.
- Income: constant 2015 US$ is the main measure; the current-US$ series is a row.
- The R replica was retired (10 September call); the estimator-agreement table in `RESULTS.md` §8 replaces it. Its test is skipped by design, hence 25 collected, 24 passed, 1 skipped.
- New pinned inputs with provenance: World Bank context series (pulled by the committed `inputs/pull_wb_context.py`, incl. basic sanitation from the WHO/UNICEF JMP), GFDx legislation years, the DHS survey list, Nunn–Puga terrain. Panel 145 → 174 columns; `events.csv` added; 19 → 24 tests. Wild-cluster-bootstrap p-values on every fixed-effects, first-difference and lagged-outcome row.

## 15 September 2026 — repository layout only

- The registry folder the pipeline reads was renamed from a member's name to [`gifna/`](../gifna/); the notebook's fallback paths follow the public layout. No number changed: the panel hash is unchanged.

## v1.2 (11 September 2026) and earlier

- The methodology audit that produced v2.0 is summarised in [`scaffold/README.md`](../scaffold/README.md); earlier versions are not published.
