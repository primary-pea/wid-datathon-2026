# scaffold/ — SSA women's-nutrition panel, dose ladder, event studies (v2.0, 2026-09-12)

One table, one set of rules, one command, so nobody assembles data twice and every number on a slide traces to a script, a stats key and a panel hash. v2.0 follows the methodology audit in `research/scaffold-v2-methodology-audit.md` (75 open-access references): the within-country design uses only dated policy records, the decisive dynamic check is an event study with heterogeneity-robust estimators, the null is stated as a bound, the controls come from the anaemia literature, and the positive-deviance ranking adjusts for context, not income alone.

## What is here

- **The panel** — `panel/` here, `derived/` in the shared repo: `ssa_panel.csv` (49 Sub-Saharan African countries × 2000–2025, 172 columns: `out_*` outcomes, `feat_*` features incl. the context block, `feat_gifna_*` = GIFNA composites unchanged from the team feature table, `feat_gd_*` = features the panel derives itself from the three GIFNA registry files, now with per-file anaemia and fortification families), `events.csv` (one row per country: first dated anaemia policy, GFDx fortification-mandate years, sub-region, terrain), `DATA_DICTIONARY.md`, `ssa_panel_readiness.md/.csv`, `MANIFEST.json` (sha256 of every input, the panel and the events table), `data_version.txt`.
- **`inputs/`** — everything the assembly needs that is not already a team file, pinned with a `*.provenance.json`: the UNICEF workbook, the FAOSTAT parquets, IGME, GFDx status, the country-code lookup, FIES 3-year averages, World Bank GDP in constant 2015 US$, and (v2.0) `wb_context_ssa.csv` (malaria incidence, fertility, urbanisation, HIV, employment, health expenditure), `gfdx_legislation_years_ssa.csv` (mandatory-fortification years), `dhs_anaemia_women_surveys.csv` (country-years with a DHS haemoglobin survey), `nunn_puga_ruggedness_ssa.csv` (terrain). The team files themselves (`gifna/gifna_feature_table.csv`, the three registry files, `subsaharan_data/GDP_per_capita.csv` with the team's unemployment and hospital-beds columns) are read from the shared repo.
- **The pipeline** — `00_assemble_panel.py` (+ `gifna_direct.py`) → `01_prep_frame.py` → `02_fe_model.py` (the dose ladder) → `02b_event_study.py` → `02c_spec_curve.py` → `03_loco.py` → `04_residuals.py` → `05_figures.py` → sidebars `08_concern_score.py`, `09_dml_sidebar.py` → `06_report.py` (RESULTS.md + data dictionary) → `07_make_notebook.py` (the team notebook, executed on a fresh kernel and cross-checked against the pipeline). `config.py` holds every parameter; `util.py` the shared helpers (hashing, fixed-effects fits, wild cluster bootstrap, Benjamini–Hochberg).
- **Results** — `results/RESULTS.md` (every number claim-tagged `[E:script→key]` into `results/stats/*.json`), the CSVs (`fe_coefficients`, `fe_sensitivity`, `fe_subsample`, `event_study`, `event_att`, `spec_curve`, `loco_*`, `residuals_by_country`, `deviants_*`, `concern_score`), the figures in `results/figures/`.
- **Tests** — `tests/` (24: panel grid and provenance, direct GIFNA features incl. a hand recount, model reproduction, v2.0 guarantees). `./run_all.sh` runs everything and the tests in about two minutes.

## The design in one paragraph

Three questions. Q1, descriptive: where is women's anaemia high and which way is it moving. Q2, association: does the number of anaemia-cluster policies in force three years earlier move with anaemia in women 15–49 inside a country, with country and year effects, log income and context controls; and does anaemia break after the first dated anaemia policy or after a wheat-flour fortification mandate. Q3, comparative: which countries sit below what their context predicts, and what their dated policy record looks like over time. Identifying assumption for reading Q2 as more than association: parallel trends. The outcome is a modelled series (the WHO model's own covariates include the Socio-Demographic Index and mean BMI), so a survey-anchored row is the honest check.

## What v2.0 found (data version in `panel/data_version.txt`; numbers in `results/RESULTS.md`)

- The dose ladder is null in every row, and the null is a bound: effects more beneficial than about 1 percentage point of anaemia per within-country standard deviation of the policy dose are ruled out (TOST against the pre-specified smallest effect of interest), smaller effects were never detectable. The lead test is the one row that separates from zero: a policy stock three years in the future predicts lower anaemia today, which is what pre-existing trends and targeting look like, not what an effect looks like.
- The two-way FE event study around the first anaemia policy shows a post-adoption decline, but with a pre-trend of the same sign and a 27% negative-weight share; the two estimators built for staggered adoption (two-stage DiD with a country bootstrap; local-projections DiD) put the effect at about zero. The wheat-flour mandate shows no break under any estimator.
- 336 pre-specified specifications: median −0.02 pp per within-country SD; the interval excludes zero in 7% of them, about the false-positive rate.
- Leave-one-country-out: no exposure lowers the held-out error.
- Context explains 80% of the level differences (sub-region, fertility, urbanisation, terrain) where income alone explains 6%; the context ranking and the income ranking name different countries, and neither tail's policy record differs from the other's.

## How to run

```
cd scaffold && ./run_all.sh            # private repo: uses ../.venv (uv venv --python 3.12 .venv && uv pip install -p .venv/bin/python -r requirements.txt)
PY=python3 ./run_all.sh                # shared repo, any interpreter with requirements.txt installed
./sync_to_shared.sh                    # copy code, inputs, panel, results to the team repo and print the hashes
```

Environment overrides: `SCAFFOLD_PANEL_DIR`, `SCAFFOLD_ATLAS_DIR`, `SCAFFOLD_REPO_DIR` (see `config.py`).

## v2.0 (2026-09-12) — what changed from v1.2

- Exposure: the main dose is the number of anaemia-cluster **policies** in force (dated adoption years) instead of the team's six-flag composite; programme rows (questionnaire answers dated by survey round) stay in the profiles. Alternative constructions remain as rows and in the specification curve.
- Event studies (`02b`): first dated anaemia policy and GFDx wheat-flour mandate; two-way FE, two-stage DiD, local-projections DiD; negative-weight diagnostic; pre-trend slope adjustment.
- Ladder (`02`): first-difference, long-difference and lagged-outcome rows (the bracket); context block (malaria, fertility, urbanisation, HIV); the team's unemployment and employment rows; hospital beds, health expenditure and the FIES women-minus-men gap in the sub-sample block; pregnant-women anaemia and a women's summary index among the outcome swaps with Benjamini–Hochberg adjustment; a survey-anchored row; wild-cluster-bootstrap p-values; minimum detectable effect and TOST bounds. Spec B (all composites jointly) removed.
- Specification curve (`02c`), context ranking with terrain and sub-region (`04`), a bootstrap interval on the LOCO difference (`03`), the concern-score reproduction (`08`) and the DML sidebar (`09`).
- Implementation contrast (13 Sep): delivered deworming coverage among school-age children from the WHO PCT databank (`inputs/STH_data.xlsx`, pinned with provenance) as an exposure row and a sub-sample control, next to the paper record.
- Income: constant 2015 US$ is the main measure; the team's current-US$ series is a row.
- The R replica was retired (10 Sep call); the estimator-agreement table in RESULTS.md §8 replaces it.
- New pinned inputs with provenance: World Bank context series (pulled by the committed `inputs/pull_wb_context.py`, incl. basic sanitation from the WHO/UNICEF JMP), GFDx legislation years, DHS survey list, Nunn–Puga terrain. Panel 145 → 173 columns; `events.csv` added; 19 → 24 tests. Wild-cluster-bootstrap p-values on every fixed-effects, first-difference and lagged-outcome row.

## v1.2 (2026-09-11) and earlier

v1.2 read the three GIFNA registry files directly (`gifna_direct.py`, cluster rules in `inputs/gifna_cluster_rules.csv`, token map for audit). v1.1 (9 Sep) applied the review fixes (code-based joins, manifest hash chain, country-trend rows, correct within-R², tested tail contrast). v1 (9 Sep) was the first panel, fixed-effects model, LOCO and ranking.
