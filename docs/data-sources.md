# Data sources

Every file the pipeline reads is committed and pinned by SHA-256 ([`derived/MANIFEST.json`](../derived/MANIFEST.json), 29 inputs; `scaffold/inputs/*.provenance.json`). How each was pulled, and what raw material is *not* committed, is in [`derived/DATA_ACQUISITION.md`](../derived/DATA_ACQUISITION.md). Each source is used under its own terms of use, linked below.

| Source | What we use | Release / access | Enters the panel as |
|---|---|---|---|
| WHO Global Health Observatory, via FAOSTAT Suite of Food Security Indicators (item 21043) — https://www.fao.org/faostat/en/#data/FS | anaemia prevalence, women 15–49 | FAOSTAT July-2026 release | `out_anaemia_wra_fs_pct` — the main outcome |
| UNICEF Global Database, Women's Nutrition — https://data.unicef.org/topic/nutrition/womens-nutrition/ | anaemia (women, pregnant, non-pregnant), underweight, overweight (NCD-RisC) | August 2025 workbook | `out_anaemia_*`, `out_women_underweight_pct`, `out_women_overweight_pct`; the concern score |
| FAOSTAT FS items 21025, 21026, 21041, 21044, 21049 | stunting, wasting, overweight under 5, exclusive breastfeeding, low birthweight | July-2026 release | `out_*` child outcomes |
| FAOSTAT Cost and Affordability of a Healthy Diet — https://www.fao.org/faostat/en/#data/CAHD | cost of a healthy diet, share unable to afford it | July-2026 release, 2017 on | `feat_pua_pct` and the diet-cost columns (sub-sample rows) |
| FAOSTAT FIES | severe food insecurity, three-year averages, by sex | July-2026 release, 2014 on | `feat_fies_*` (sub-sample rows) |
| UN IGME 2025 — https://childmortality.org | neonatal, infant and under-5 mortality | 2025 round | `out_nmr_per1000`, `out_imr_per1000`, `out_u5mr_per1000` |
| WHO GIFNA — https://gifna.who.int/ | nutrition policies, programmes and actions, mechanisms | per-country exports, 3–5 September 2026 | `feat_gd_stock_*` by topic cluster and source file; the events table; the team feature table `feat_gifna_*` |
| Global Fortification Data Exchange — https://fortificationdata.org | mandatory fortification status and legislation years by food vehicle | dataset snapshot, September 2026 | `feat_gd_any_fortification`, wheat-mandate year in `events.csv`, fortification status in the residual ranking |
| World Bank WDI — https://data.worldbank.org | GDP per capita (constant 2015 US$ and current US$), malaria incidence, fertility, urban share, employment, HIV prevalence, health expenditure, basic sanitation (WHO/UNICEF JMP) | API pulls, 9 and 13 September 2026 | `feat_gdp_pc_*`, the context block |
| DHS Program API — https://api.dhsprogram.com | the list of surveys with women's haemoglobin testing | 13 September 2026 | `feat_dhs_anaemia_survey` — the survey-anchored flag |
| WHO PCT databank, soil-transmitted helminthiases — https://www.who.int/teams/control-of-neglected-tropical-diseases/data-platforms/pct-databank | national deworming coverage among school-age children | downloaded 12 September 2026 | `feat_sth_pc_coverage_sac_pct` — the one delivery measure |
| Nunn & Puga (2012) — https://diegopuga.org/data/rugged/ | terrain ruggedness, tropical share, distance to coast | 13 September 2026 | `geo_rugged`, `geo_tropical`, `geo_dist_coast` |
| Team files | the 49-country list; the cluster rules | — | `config.py`; [`scaffold/inputs/gifna_cluster_rules.csv`](../scaffold/inputs/gifna_cluster_rules.csv) |

Not used by scaffold v2.0 and never committed: MICS and DHS survey microdata (licensed per registered user).
