# SSA panel — readiness (scaffold v2.0, built 2026-09-15, data version afe63e46c26b)

Panel: 1274 rows (49 countries × 26 years, 2000–2025) × 174 columns. File: `ssa_panel.csv`; manifest: `MANIFEST.json`. Script: `scaffold/00_assemble_panel.py`.

| group | column | source | countries (of 49) | years | cells | countries without values |
|---|---|---|---:|---|---:|---|
| outcome | out_women_underweight_pct | UNICEF Global database on women's nutrition, Aug-2025 (underweight, modelled point estimates) | 49 | 2000–2022 | 1127 | — |
| outcome | out_women_overweight_pct | UNICEF Global database on women's nutrition, Aug-2025 (overweight, modelled point estimates) | 49 | 2000–2022 | 1127 | — |
| outcome | out_anaemia_wra_unicef_pct | UNICEF Global database on women's nutrition, Aug-2025 (anaemia_WRA, modelled point estimates) | 49 | 2000–2023 | 1176 | — |
| outcome | out_anaemia_pregnant_pct | UNICEF Global database on women's nutrition, Aug-2025 (anaemia_pregnant_women, modelled point estimates) | 49 | 2000–2023 | 1176 | — |
| outcome | out_anaemia_wra_fs_pct | FAOSTAT FS item 21043 (July-2026 release), joined on FAOSTAT area code | 49 | 2000–2023 | 1176 | — |
| outcome | out_lbw_pct | FAOSTAT FS item 21049 (July-2026 release), joined on FAOSTAT area code | 35 | 2000–2020 | 735 | CPV DJI ETH GIN GNQ MLI MRT NER NGA SDN SOM SSD TCD UGA |
| outcome | out_stunting_u5_pct | FAOSTAT FS item 21025 (July-2026 release), joined on FAOSTAT area code | 49 | 2000–2024 | 1225 | — |
| outcome | out_wasting_u5_pct | FAOSTAT FS item 21026 (July-2026 release), joined on FAOSTAT area code | 48 | 2000–2024 | 302 | MUS |
| outcome | out_overweight_u5_pct | FAOSTAT FS item 21041 (July-2026 release), joined on FAOSTAT area code | 49 | 2000–2024 | 1225 | — |
| outcome | out_ebf_0_5mo_pct | FAOSTAT FS item 21044 (July-2026 release), joined on FAOSTAT area code | 47 | 2000–2024 | 247 | MUS SYC |
| outcome | out_nmr_per1000 | UN IGME 2025 round (Neonatal mortality rate, both sexes) | 49 | 2000–2024 | 1225 | — |
| outcome | out_imr_per1000 | UN IGME 2025 round (Infant mortality rate, both sexes) | 49 | 2000–2024 | 1225 | — |
| outcome | out_u5mr_per1000 | UN IGME 2025 round (Under-five mortality rate, both sexes) | 49 | 2000–2024 | 1225 | — |
| feature | feat_gdp_pc_current_usd | World Bank NY.GDP.PCAP.CD via subsaharan_data/GDP_per_capita.csv, joined on ISO2 (series is CURRENT US$ despite the file header) | 49 | 2000–2025 | 1242 | — |
| feature | feat_gdp_pc_constant_2015_usd | World Bank NY.GDP.PCAP.KD (constant 2015 US$), pinned API pull 2026-09-09 in scaffold/inputs/ with provenance — the main income measure from v2.0 | 49 | 2000–2025 | 1229 | — |
| feature | feat_malaria_incidence_per1000 | malaria incidence per 1,000 population at risk (WHO via World Bank SH.MLR.INCD.P3) — scaffold/inputs/wb_context_ssa.csv (World Bank API pull 12 Sep 2026) | 46 | 2000–2024 | 1150 | LSO MUS SYC |
| feature | feat_fertility_rate | total fertility rate (World Bank SP.DYN.TFRT.IN) — scaffold/inputs/wb_context_ssa.csv (World Bank API pull 12 Sep 2026) | 49 | 2000–2024 | 1225 | — |
| feature | feat_urban_pct | urban population, % of total (World Bank SP.URB.TOTL.IN.ZS) — scaffold/inputs/wb_context_ssa.csv (World Bank API pull 12 Sep 2026) | 49 | 2000–2025 | 1274 | — |
| feature | feat_hiv_prev_pct | HIV prevalence, % of population 15–49 (World Bank SH.DYN.AIDS.ZS) — scaffold/inputs/wb_context_ssa.csv (World Bank API pull 12 Sep 2026) | 45 | 2000–2024 | 1125 | GNQ MUS STP SYC |
| feature | feat_employment_pop_pct | employment-to-population ratio 15+, ILO modelled (World Bank SL.EMP.TOTL.SP.ZS) — scaffold/inputs/wb_context_ssa.csv (World Bank API pull 12 Sep 2026) | 48 | 2000–2025 | 1243 | SYC |
| feature | feat_health_exp_pc_usd | current health expenditure per capita, US$ (World Bank SH.XPD.CHEX.PC.CD) — scaffold/inputs/wb_context_ssa.csv (World Bank API pull 12 Sep 2026) | 49 | 2000–2023 | 1136 | — |
| feature | feat_sanitation_basic_pct | people using at least basic sanitation, % (WHO/UNICEF JMP via World Bank SH.STA.BASS.ZS) — scaffold/inputs/wb_context_ssa.csv (World Bank API pull 12 Sep 2026) | 49 | 2000–2024 | 1193 | — |
| feature | feat_unemployment_pct | unemployment, % of labour force, ILO modelled (team file, World Bank SL.UEM.TOTL.ZS) — subsaharan_data/GDP_per_capita.csv, joined on ISO2 | 48 | 2000–2025 | 1243 | SYC |
| feature | feat_hospital_beds_per1000 | hospital beds per 1,000 people (team file, World Bank SH.MED.BEDS.ZS; sparse) — subsaharan_data/GDP_per_capita.csv, joined on ISO2 | 48 | 2000–2023 | 324 | SSD |
| feature | feat_sth_pc_coverage_sac_pct | national coverage of preventive chemotherapy for soil-transmitted helminths, school-age children, % (WHO PCT databank; 0 = no treatment reported in a year the country required PC) — scaffold/inputs/STH_data.xlsx (WHO PCT databank download, 12 Sep 2026) | 47 | 2003–2024 | 913 | ERI SYC |
| feature | feat_dhs_anaemia_survey | 1 = a DHS survey with women's haemoglobin testing in that country-year (DHS API, indicator AN_ANEM_W_ANY, pinned); absent = 0 — filled with 0 elsewhere, so complete on the grid | 49 | 2000–2024 | 1274 | — |
| feature | feat_cohd_ppp_per_day | FAOSTAT CAHD 7S2026: Cost of a healthy diet (CoHD), joined on FAOSTAT area code | 45 | 2017–2025 | 405 | ERI SDN SOM ZWE |
| feature | feat_pua_pct | FAOSTAT CAHD 7S2026: Prevalence of unaffordability (PUA), joined on FAOSTAT area code | 45 | 2017–2025 | 405 | ERI SDN SOM ZWE |
| feature | feat_nua_million | FAOSTAT CAHD 7S2026: Number of people unable to afford a healthy diet (NUA), joined on FAOSTAT area code | 45 | 2017–2025 | 405 | ERI SDN SOM ZWE |
| feature | feat_fies_severe_female_pct_3yr | FAOSTAT FS FIES 3-year average (scaffold/inputs/ssa_fies_3yr_average.csv, rebuilt 8 Sep from the cached July-2026 release) | 40 | 2015–2024 | 321 | COG ERI GAB GIN GNQ MOZ RWA SDN SOM |
| feature | feat_fies_severe_male_pct_3yr | FAOSTAT FS FIES 3-year average (scaffold/inputs/ssa_fies_3yr_average.csv, rebuilt 8 Sep from the cached July-2026 release) | 40 | 2015–2024 | 321 | COG ERI GAB GIN GNQ MOZ RWA SDN SOM |
| feature | feat_fies_severe_total_pct_3yr | FAOSTAT FS FIES 3-year average (scaffold/inputs/ssa_fies_3yr_average.csv, rebuilt 8 Sep from the cached July-2026 release) | 40 | 2015–2024 | 321 | COG ERI GAB GIN GNQ MOZ RWA SDN SOM |
| feature | feat_fies_mod_sev_female_pct_3yr | FAOSTAT FS FIES 3-year average (scaffold/inputs/ssa_fies_3yr_average.csv, rebuilt 8 Sep from the cached July-2026 release) | 40 | 2015–2024 | 321 | COG ERI GAB GIN GNQ MOZ RWA SDN SOM |
| feature | feat_fies_mod_sev_male_pct_3yr | FAOSTAT FS FIES 3-year average (scaffold/inputs/ssa_fies_3yr_average.csv, rebuilt 8 Sep from the cached July-2026 release) | 40 | 2015–2024 | 321 | COG ERI GAB GIN GNQ MOZ RWA SDN SOM |
| feature | feat_fies_mod_sev_total_pct_3yr | FAOSTAT FS FIES 3-year average (scaffold/inputs/ssa_fies_3yr_average.csv, rebuilt 8 Sep from the cached July-2026 release) | 40 | 2015–2024 | 321 | COG ERI GAB GIN GNQ MOZ RWA SDN SOM |
| feature | feat_gifna_* (76 columns) | GIFNA via gifna/build_feature_table.py (policies, programmes, mechanisms; 1999–2025) | 49 | 2000–2025 | 1274 | — |
| feature | feat_gd_* (60 columns) | WHO GIFNA registry files read directly by gifna_direct.py (policies, programmes & actions, mechanisms; clusters from inputs/gifna_cluster_rules.csv; 0 = no record) | 49 | 2000–2025 | 1274 | — |

Events (v2.0, `events.csv`, one row per country): first dated anaemia-cluster policy year per registry file and across files (survey-window rows never date an event), GFDx mandatory wheat-/maize-flour fortification years and status, UNICEF sub-region, Nunn–Puga terrain variables.

Identical series check: `out_anaemia_wra_unicef_pct` vs `out_anaemia_wra_fs_pct` max |difference| = 0 (the UNICEF workbook republishes the same WHO 2025 edition; not independent).

## Candidate modelling frame (2000–2023): rows with all of ['out_anaemia_wra_fs_pct', 'out_anaemia_pregnant_pct', 'out_women_underweight_pct', 'feat_gdp_pc_constant_2015_usd', 'feat_gifna_policy_count_active'] non-null: 1064 of 1176 country-years, 49 countries.

Countries with fewest complete rows: SSD (4), DJI (10), ERI (12), LBR (16), MOZ (17), AGO (18), CPV (21), MUS (23), ZAF (23), MWI (23)

team country list: 49 names; 48 match the pinned lookup; unmatched (encoding): ["Cô´te d'Ivoire"]

## GIFNA registry files read directly (`gifna_direct.py`; v2.0 adds per-file anaemia and fortification families and the dated events table `events.csv`)

Source: WHO GIFNA (https://gifna.who.int/), per-country exports of 3–5 Sep 2026 combined by `gifna/combine_gifna_raw.py`. Features come from the controlled topic / theme / target-group columns only (rules: `inputs/gifna_cluster_rules.csv`; every token and its clusters: `gifna_direct_token_map.csv`). Policies are active from start to end year (open end = still active); undated GNPR questionnaire rows are placed in their survey window (2009–2010, 2016–2017); other undated rows are excluded.

| source | rows in file | rows in the 49 | records used | dated | open end | survey window | undated, excluded | countries with records | tokens | unmapped tokens (share of mentions) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| policies | 944 | 928 | 928 | 408 | 520 | 0 | 0 | 49 | 457 | 51 (2.9%) |
| programmes | 1803 | 1756 | 1647 | 206 | 203 | 1238 | 109 | 46 | 124 | 9 (8.1%) |
| mechanisms | 131 | 131 | 96 | 0 | 96 | 0 | 35 | 38 | 20 | 0 (0.0%) |

Records per cluster (a record can sit in several): anaemia 543, fortification 633, micronutrient 1033, maternal 860, iycf 862, wasting_stunting 655, infection 676, food_security 683, ncd_diet 820, schools_education 927, governance 200; records in no cluster: 64.
Countries with no usable record in a file (their features are 0 there): programmes: AGO CAF GNQ; mechanisms: AGO CAF ETH GAB GNQ MOZ MUS NGA SSD SYC UGA.
