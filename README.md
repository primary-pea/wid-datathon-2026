# Ink and Iron: Primary Pea

**Women in Data 2026 Datathon (Eat track)**

---

**Question.** Across 49 sub-Saharan African countries, do the nutrition policies governments write down move with the anaemia measured in women aged 15–49?

**Answer in four numbers** (scaffold v2.0, data version `afe63e46c26b`, every figure claim-tagged in `scaffold/results/RESULTS.md`):

| | |
| --- | --- |
| One more anaemia policy on the books, three years earlier | **−0.21** points of anaemia, 95% interval −0.62 to +0.20, p = 0.32 — a null |
| Policies three years in the *future* | **−0.34**, p = 0.03 — a future policy cannot cause a past outcome; something else moves both |
| Effects the data rule out | anything at or beyond **0.60** points per policy (equivalence p = 0.03) |
| Countries where policy improves an out-of-sample forecast | **22 of 49** — a coin toss |

The registry counts what governments write, not what reaches women: three in four programme records carry no date and none records coverage. *Until delivery is recorded, nobody can say which policies work.*

## Run it

```sh
uv venv --python 3.12 .venv && uv pip install -p .venv/bin/python -r requirements.txt
cd scaffold && PY=../.venv/bin/python ./run_all.sh
```

Rebuilds the panel, every result and the report in about two minutes; then runs the tests (24 pass, 1 skipped).

The pipeline reads two team folders at the repo root by name — `gifna/` and `subsaharan_data/` — and every other input from `scaffold/inputs/`, each pinned with a `*.provenance.json`.

## Where things are

| Folder | What is in it | Kept by |
| --- | --- | --- |
| `scaffold/` | the pipeline: assembly, the dose ladder, event studies, specification curve, validation, tests, the executed cross-check notebook, `results/` | Saarah |
| `derived/` | the product — `ssa_panel.csv` (49 countries × 2000–2025 × 174 columns), `events.csv`, the data dictionary, manifest and data version. **`derived/DATA_ACQUISITION.md` explains how every source was obtained and describes the raw data that is not committed.** | Saarah |
| `gifna/` | the WHO GIFNA policy registry: combined exports, the combine and feature-table scripts, the feature table | Tiana |
| `subsaharan_data/` | World Bank GDP per capita, FIES food insecurity, the 49-country list | Hope |
| `eda/` | exploratory notebooks, by topic — see `eda/README.md` for who did which | everyone |
| `dashboard/` | the generator and data snapshot behind the live dashboard | Saarah |
| `presentation/` | the final script, the deck as PDF, captions, the video link | Ramya |
| `docs/` | method, data sources, known limits, changelog | Saarah |

## Links

- Project site: <https://primary-pea.github.io/>
  - Deck: <https://primary-pea.github.io/ink-and-iron/>
  - Dashboard: <https://primary-pea.github.io/dashboard/>
- Method page: <https://primary-pea.github.io/method/>
  - Reproduce page: <https://primary-pea.github.io/reproduce/>

## Team

Primary Pea:

- Alison Nichols (analytics)
- Hope Winsor (data science)
- Saarah Hossain (modelling scaffold and dashboard)
- Tatiana Gabel (policy feature table, background on maternal nutrition)
- Ramyashree Shetty (presentation lead)

---

Data: WHO, UNICEF, FAOSTAT, UN IGME, World Bank, WHO GIFNA, GFDx, DHS, WHO PCT databank, Nunn & Puga.

Licence: see `LICENSE`.
