# How the data was acquired, and what is not in this repo

Everything the pipeline needs to rebuild the panel is committed and pinned by SHA-256 in [`MANIFEST.json`](MANIFEST.json) (29 inputs) and in the `*.provenance.json` files under [`scaffold/inputs/`](../scaffold/inputs/). What is **not** committed is the raw material those inputs were cut from — bulk pulls, per-country exports, licensed microdata. This note says where each came from, how it was pulled, what shape it has, and how to get it again.

## Committed inputs and where they came from

| Input (committed) | Origin | How obtained | Shape |
|---|---|---|---|
| `scaffold/inputs/faostat/*.parquet` (7 files) | FAOSTAT, July-2026 release: Suite of Food Security Indicators items 21025, 21026, 21041, 21043, 21044, 21049 and the Cost and Affordability of a Healthy Diet release | pulled from the FAOSTAT bulk download by the atlas script `21_faostat_pull_coverage.py`, cut to the item and copied byte-identical ([`scaffold/inputs/raw_copies.provenance.json`](../scaffold/inputs/raw_copies.provenance.json)) | one row per country-year-item; 148 KB in total |
| [`scaffold/inputs/unicef/UNICEF_Global-database_Womens-Nutrition_August-2025_2.xlsx`](../scaffold/inputs/unicef/UNICEF_Global-database_Womens-Nutrition_August-2025_2.xlsx) | UNICEF Global Database, Women's Nutrition, August 2025 | downloaded from data.unicef.org; the workbook republishes the WHO 2025 anaemia series | 1.5 MB workbook; 194 countries; anaemia (women, pregnant, non-pregnant), underweight, overweight |
| [`gifna/gifna_policies.csv`](../gifna/gifna_policies.csv), `gifna_programmes_and_actions.csv`, `gifna_mechanisms.csv` | WHO Global database on the Implementation of Food and Nutrition Action (GIFNA), https://gifna.who.int/ | per-country exports of 3–5 September 2026, one file per (type, country, export date), combined and de-duplicated by [`gifna/combine_gifna_raw.py`](../gifna/combine_gifna_raw.py) | 5,580 policy rows, 8,442 programme-and-action rows, 131 mechanism rows; 8.8 MB |
| [`gifna/gifna_feature_table.csv`](../gifna/gifna_feature_table.csv) | derived from the three files above by [`gifna/build_feature_table.py`](../gifna/build_feature_table.py) | — | 1,350 country-year rows, 1999–2025 |
| [`subsaharan_data/GDP_per_capita.csv`](../subsaharan_data/GDP_per_capita.csv) | World Bank WDI `NY.GDP.PCAP.CD` (current US$ — the header says otherwise) | pulled through the WDI API | 1,274 rows |
| [`subsaharan_data/food_insecurity.csv`](../subsaharan_data/food_insecurity.csv) | FAOSTAT FIES | pulled through the FAOSTAT API | 1,274 rows |
| [`subsaharan_data/subsahran_africa_countries.csv`](../subsaharan_data/subsahran_africa_countries.csv) | the 49-country list | hand-assembled; the pipeline pins its own copy in `config.py` | 49 rows |
| [`scaffold/inputs/wb_gdp_pc_constant_2015usd_ssa.csv`](../scaffold/inputs/wb_gdp_pc_constant_2015usd_ssa.csv) | World Bank WDI `NY.GDP.PCAP.KD`, constant 2015 US$ | `api.worldbank.org/v2`, 2026-09-09 | 1,229 rows |
| [`scaffold/inputs/wb_context_ssa.csv`](../scaffold/inputs/wb_context_ssa.csv) | World Bank WDI: malaria incidence, fertility, urban share, employment, HIV prevalence, health expenditure, basic sanitation | [`scaffold/inputs/pull_wb_context.py`](../scaffold/inputs/pull_wb_context.py), 2026-09-13 | 1,274 rows × 10 |
| [`scaffold/inputs/igme_2025_ssa_national.csv`](../scaffold/inputs/igme_2025_ssa_national.csv) | UN IGME 2025 round, national, both sexes | tidied from the IGME release by the atlas script `10_igme_tidy.py` | 3,675 rows, three indicators |
| [`scaffold/inputs/gfdx_legislation_years_ssa.csv`](../scaffold/inputs/gfdx_legislation_years_ssa.csv), `gfdx_fortification_gaps.csv` | Global Fortification Data Exchange dataset snapshot | tidied by the atlas script `11_gfdx_tidy.py` | 225 and 200 rows |
| [`scaffold/inputs/dhs_anaemia_women_surveys.csv`](../scaffold/inputs/dhs_anaemia_women_surveys.csv) | DHS Program API, indicator `AN_ANEM_W_ANY`, national | API call, 2026-09-13 | 139 rows — the list of surveys with women's haemoglobin testing, used only to flag survey-anchored years |
| [`scaffold/inputs/STH_data.xlsx`](../scaffold/inputs/STH_data.xlsx) | WHO PCT databank, soil-transmitted helminthiases | downloaded 2026-09-12 | 3,256 rows, 1,484 in the 49 countries |
| [`scaffold/inputs/nunn_puga_ruggedness_ssa.csv`](../scaffold/inputs/nunn_puga_ruggedness_ssa.csv) | Nunn & Puga (2012) terrain ruggedness | `diegopuga.org/data/rugged/`, 2026-09-13 | 48 rows |
| [`scaffold/inputs/ssa_fies_3yr_average.csv`](../scaffold/inputs/ssa_fies_3yr_average.csv) | FAOSTAT FS July-2026, FIES three-year averages | rebuilt 2026-09-08 from the cached release | 321 rows, 40 countries |
| [`scaffold/inputs/gifna_cluster_rules.csv`](../scaffold/inputs/gifna_cluster_rules.csv), `country_codes_ssa.csv` | written by the team | — | 47 rules; 49 codes |

## Raw material that is not committed

| Not committed | Why | Shape | To re-acquire |
|---|---|---|---|
| FAOSTAT domain-level bulk pulls (FS suite, CAHD, FBS) — the atlas cache the seven parquet extracts were cut from | size; fully reproducible | one long table per domain (area, item, element, year, unit, value, flag), tens of thousands of rows each | FAOSTAT bulk download at fao.org/faostat, July-2026 release, or the `faostat` Python package; cut to the items above |
| GIFNA per-country raw exports (`Africa_Data/`) | superseded by the combined files, which are committed | roughly 49 countries × 3 record types × 1–2 export dates, one CSV each | export per country from gifna.who.int and run [`gifna/combine_gifna_raw.py`](../gifna/combine_gifna_raw.py) |
| World Bank and DHS API responses | the tidied CSVs are committed with the exact query in their provenance files | JSON pages | the URLs in the `*.provenance.json` files |
| UN IGME and GFDx full releases | tidied extracts committed | the IGME release workbook; `GFDxDataSet.CSV` | childmortality.org; fortificationdata.org |
| MICS survey microdata | licensed per registered user; **not used by scaffold v2.0** | one archive per survey | register at mics.unicef.org; never commit |
| DHS survey microdata | not used; only the survey list is | — | dhsprogram.com |
| Team Google Drive: clips, deck assets, Presentation Prep | media, not data | — | the Drive folders |
| The submission video | up to 10 GB; submitted as a file on the entry form | — | not committed; the deck repo holds the assembled cut |

The panel is rebuilt in full by [`scaffold/run_all.sh`](../scaffold/run_all.sh) from the committed inputs alone; [`data_version.txt`](data_version.txt) must read `afe63e46c26b` afterwards, and [`scaffold/tests/`](../scaffold/tests/) checks the grid, the provenance hashes and the headline numbers.
