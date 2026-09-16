# scaffold/ — the pipeline

One table, one set of rules, one command: every number on a slide traces to a script, a stats key and a panel hash. Scaffold v2.0 (12 September 2026), data version `afe63e46c26b`.

## What is here

- **The pipeline** — [`00_assemble_panel.py`](00_assemble_panel.py) (with [`gifna_direct.py`](gifna_direct.py)) → [`01_prep_frame.py`](01_prep_frame.py) → [`02_fe_model.py`](02_fe_model.py) (the dose ladder) → [`02b_event_study.py`](02b_event_study.py) → [`02c_spec_curve.py`](02c_spec_curve.py) → [`03_loco.py`](03_loco.py) → [`04_residuals.py`](04_residuals.py) → [`05_figures.py`](05_figures.py) → sidebars [`08_concern_score.py`](08_concern_score.py), [`09_dml_sidebar.py`](09_dml_sidebar.py) → [`06_report.py`](06_report.py) (the report and data dictionary) → [`07_make_notebook.py`](07_make_notebook.py) (the cross-check notebook, executed on a fresh kernel and compared with the pipeline). [`config.py`](config.py) holds every parameter; [`util.py`](util.py) the shared helpers (hashing, fixed-effects fits, wild cluster bootstrap, Benjamini–Hochberg).
- **[`inputs/`](inputs/)** — every input that is not a team table, pinned with a `*.provenance.json` beside it: the UNICEF workbook, the FAOSTAT extracts, UN IGME, GFDx, the DHS survey list, WHO PCT deworming, World Bank context series (pulled by [`inputs/pull_wb_context.py`](inputs/pull_wb_context.py)), Nunn–Puga terrain, the country-code lookup and the 47 cluster rules ([`inputs/gifna_cluster_rules.csv`](inputs/gifna_cluster_rules.csv)). The two team tables are read from the repo root: [`gifna/`](../gifna/) and [`subsaharan_data/`](../subsaharan_data/).
- **The panel** — written to [`derived/`](../derived/): `ssa_panel.csv` (49 countries × 2000–2025, 174 columns), `events.csv`, the dictionary, the manifest of input hashes and the data version.
- **[`results/`](results/)** — [`results/RESULTS.md`](results/RESULTS.md) with every number claim-tagged into [`results/stats/`](results/stats/); the result tables (`fe_coefficients`, `fe_sensitivity`, `fe_subsample`, `event_study`, `event_att`, `spec_curve`, `loco_*`, `residuals_by_country`, `deviants_*`, `concern_score`); [`results/figures/`](results/figures/).
- **[`tests/`](tests/)** — 25 collected, 24 pass, 1 skipped by design (the retired R replica): the panel grid and provenance hashes, the registry features including a hand recount, the stored coefficients, the v2.0 guarantees.
- **[`90_team_notebook.ipynb`](90_team_notebook.ipynb)** — the executed cross-check: re-fits the headline model from the panel and compares with [`results/stats/02_fe.json`](results/stats/02_fe.json).

## The design in one paragraph

Three questions. *Descriptive:* where is women's anaemia high and which way is it moving. *Association:* does the number of anaemia-cluster policies in force three years earlier move with anaemia in women 15–49 inside a country, once country and year effects and income are held fixed. *Context:* how much of the level differences do income, malaria, fertility, urbanisation, sanitation, sub-region and terrain explain, and do the countries that beat that prediction have a different policy record from those that fall short. The dose is the count of dated policies in the WHO GIFNA registry whose tokens match the anaemia cluster; every guard on the main estimate is a row of the ladder, and 336 pre-specified specifications, three event-study estimators and leave-one-country-out prediction sit around it. The full method is in [`docs/method.md`](../docs/method.md).

## What v2.0 found

- The dose ladder is null in every row, and the null is a bound: benefits of 0.60 points of anaemia per policy or more are ruled out (equivalence p = 0.03; about 1 point per within-country standard deviation of the dose).
- Policies three years in the *future* "predict" current anaemia (−0.34, p = 0.03): governments react to the trend; with country trends the estimate is −0.02.
- The two-way FE event study around the first anaemia policy shows a post-adoption decline with a pre-trend of the same sign and a 27% negative-weight share; the two estimators built for staggered adoption find nothing.
- 336 specifications: median −0.02 points per within-country SD; 22 exclude zero (15 one way, 7 the other), about the false-positive rate.
- Leave-one-country-out: no exposure lowers the held-out error (policy helps in 22 of 49, binomial p = 0.57).
- Context explains 81% of the level differences where income plus year effects explain 6%; the two tails of the context ranking have indistinguishable policy records (Mann-Whitney p = 0.11).

## How to run

```sh
# from the repo root
uv venv --python 3.12 .venv && uv pip install -p .venv/bin/python -r requirements.txt
cd scaffold && PY=../.venv/bin/python ./run_all.sh        # about two minutes, then the tests
```

Any interpreter with [`requirements.txt`](../requirements.txt) installed works (`PY=python3`). After a run, [`derived/data_version.txt`](../derived/data_version.txt) must still read `afe63e46c26b`. Environment overrides: `SCAFFOLD_PANEL_DIR`, `SCAFFOLD_ATLAS_DIR`, `SCAFFOLD_REPO_DIR` (see [`config.py`](config.py)). What changed between versions: [`docs/changelog.md`](../docs/changelog.md); what the numbers cannot carry: [`docs/known-limits.md`](../docs/known-limits.md).
