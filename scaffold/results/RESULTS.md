# Scaffold v2.0 results — SSA women's-nutrition panel (2026-09-15)

_Every number carries a pointer `[E:script→key]` into `results/stats/`. Panel data version `afe63e46c26b` (sha256 `afe63e46c26b…`, see `MANIFEST.json`); config `2026-09-13a`. Methodology: `research/scaffold-v2-methodology-audit.md`._

## 0. The three questions and what this design can answer

1. **Where** is women's anaemia high and which way is it moving? Descriptive: levels, trends, the context ranking (§7) and the concern score.
2. **Does the dated policy record move with anaemia inside a country?** The within-country association between the number of anaemia-cluster policies in force three years earlier and anaemia in women 15–49, with country and year effects, log income and context controls; and an event study around the first dated anaemia policy and the wheat-flour fortification mandate (§2). Identifying assumption for reading any of it as more than association: absent the policy, adopters and comparison countries would have moved in parallel. The dose is anaemia-cluster policies active (GIFNA policies file, dated); programme rows are questionnaire answers dated by survey round and stay out of the within-country design.
3. **Who beats their context**, and what does their policy record look like over time (§7)?

All outcome series are modelled estimates (the WHO anaemia model uses the Socio-Demographic Index, meat supply and mean BMI as covariates; NCD-RisC for BMI; JME; IGME): association within countries, never causation, and the survey-anchored row (§9) is the honest check on the modelled series.

## 1. Modelling frame

- Estimation sample (main spec): **994 country-years, 49 countries, 2003–2023** [E:01_frame→estimation_sample]; outcome = Anaemia prevalence, women 15–49 (%) (WHO 2025 estimates (GHO indicator 4552, Bayesian hierarchical model on 412 surveys from 122 countries) as republished in FAOSTAT FS item 21043, July-2026 release); dose = anaemia-cluster policies active (GIFNA policies file, dated) lagged 3 years; income = log GDP per capita, constant 2015 US$ (current-US$ row in the ladder).
- Dose scale: mean 1.89, overall SD 2.12, within-country SD 1.66 [E:01_frame→policy_main_sd_within]. Outcome mean 38.5%, SD overall 11.2 pp, within-country 2.5 pp [E:01_frame→outcome_sd_within]. Identified from 44 countries; CAF, ERI, GNQ, SSD, SYC have no within-sample variation in the dose [E:01_frame→identified_from_countries].
- Alternative exposures are collinear (max |corr| between lag-3 exposures 0.95 [E:01_frame→max_abs_corr_between_exposures]); they enter one at a time (§3) and in the specification curve (§5), never jointly.
- Survey-anchored country-years in the window: 83 in 33 countries [E:01_frame→survey_anchor_country_years_in_window]; women's summary index rows: 1127 [E:01_frame→women_index_rows_in_window].

## 2. Event studies (the headline evidence on question 2)

### first dated anaemia-cluster policy (GIFNA policies file)

- Sample: 31 adopting countries in the window, 3 never-adopting; 15 countries adopted before 2002 and are excluded (BFA, BWA, CIV, CMR, COD, COG, GHA, GIN, GMB, KEN, MRT, SDN, SEN, TCD, ZMB); cohorts by year: {'2002': 1, '2003': 3, '2004': 2, '2005': 2, '2006': 3, '2008': 3, '2009': 4, '2010': 1, '2011': 2, '2012': 4, '2013': 1, '2014': 3, '2017': 1, '2022': 1} [E:02b_event→anaemia_policy.info].
- Static two-way FE: ATT -0.939 pp (SE 0.527, p = 0.084); share of negative weights in that coefficient 0.27 (135 negatively weighted treated cells of 451) [E:02b_event→anaemia_policy.twfe_static] — the de Chaisemartin–D'Haultfœuille diagnostic; a large share means the TWFE number mixes comparisons the design should not make.
- Two-stage DiD (Gardner; country cluster bootstrap, 299 draws): ATT +0.098 pp, 95% CI [-2.042, +2.086], p = 0.928 [E:02b_event→anaemia_policy.did2s_static].
- Local-projections DiD (Dube, Girardi, Jordà & Taylor; clean controls): pooled ATT -0.080 pp (SE 0.192, p = 0.678) [E:02b_event→anaemia_policy.lpdid_att].
- two-way FE event study: mean post-period coefficient -0.666 pp; largest pre-period |t| 2.01; pre-trend slope -0.112 pp/year, trend-adjusted post mean -0.331 pp [E:02b_event→anaemia_policy.twfe_event_pretrend].
- two-stage DiD: mean post-period coefficient -0.492 pp; largest pre-period |t| 0.97; pre-trend slope -0.040 pp/year, trend-adjusted post mean -0.372 pp [E:02b_event→anaemia_policy.did2s_event_pretrend].
- local-projections DiD: mean post-period coefficient -0.075 pp; largest pre-period |t| 1.24; pre-trend slope -0.037 pp/year, trend-adjusted post mean +0.036 pp [E:02b_event→anaemia_policy.lpdid_event_pretrend].

### mandatory wheat-flour fortification (GFDx)

- Sample: 26 adopting countries in the window, 23 never-adopting; 0 countries adopted before 2002 and are excluded (none); cohorts by year: {'2003': 1, '2005': 2, '2006': 1, '2009': 1, '2010': 5, '2011': 1, '2012': 3, '2013': 2, '2014': 1, '2015': 2, '2016': 2, '2017': 1, '2019': 1, '2020': 1, '2021': 1, '2022': 1} [E:02b_event→wheat_mandate.info].
- Static two-way FE: ATT -0.564 pp (SE 0.765, p = 0.465); share of negative weights in that coefficient 0.02 (29 negatively weighted treated cells of 298) [E:02b_event→wheat_mandate.twfe_static] — the de Chaisemartin–D'Haultfœuille diagnostic; a large share means the TWFE number mixes comparisons the design should not make.
- Two-stage DiD (Gardner; country cluster bootstrap, 299 draws): ATT -1.052 pp, 95% CI [-2.595, +0.393], p = 0.184 [E:02b_event→wheat_mandate.did2s_static].
- Local-projections DiD (Dube, Girardi, Jordà & Taylor; clean controls): pooled ATT -0.173 pp (SE 0.343, p = 0.616) [E:02b_event→wheat_mandate.lpdid_att].
- two-way FE event study: mean post-period coefficient -0.154 pp; largest pre-period |t| 0.14; pre-trend slope +0.028 pp/year, trend-adjusted post mean -0.239 pp [E:02b_event→wheat_mandate.twfe_event_pretrend].
- two-stage DiD: mean post-period coefficient -0.244 pp; largest pre-period |t| 0.61; pre-trend slope +0.023 pp/year, trend-adjusted post mean -0.314 pp [E:02b_event→wheat_mandate.did2s_event_pretrend].
- local-projections DiD: mean post-period coefficient -0.058 pp; largest pre-period |t| 0.65; pre-trend slope +0.054 pp/year, trend-adjusted post mean -0.219 pp [E:02b_event→wheat_mandate.lpdid_event_pretrend].

Event-study coefficients (pp of anaemia relative to the year before the event; bins at the window ends):

| event | estimator | k | coef | 95% CI |
|---|---|---:|---:|---|
| anaemia_policy | did2s_event | -4 | +0.048 | [-0.097, +0.311] |
| anaemia_policy | did2s_event | -3 | +0.048 | [-0.034, +0.162] |
| anaemia_policy | did2s_event | -2 | +0.008 | [-0.067, +0.130] |
| anaemia_policy | did2s_event | +0 | -0.181 | [-0.503, +0.197] |
| anaemia_policy | did2s_event | +1 | -0.266 | [-0.705, +0.186] |
| anaemia_policy | did2s_event | +2 | -0.567 | [-1.178, +0.207] |
| anaemia_policy | did2s_event | +3 | -0.700 | [-1.499, +0.304] |
| anaemia_policy | did2s_event | +4 | -0.747 | [-1.753, +0.465] |
| anaemia_policy | did2s_event | +5 | +0.424 | [-2.400, +3.001] |
| anaemia_policy | lpdid_event | -4 | +0.103 | [-0.175, +0.380] |
| anaemia_policy | lpdid_event | -3 | +0.088 | [-0.081, +0.256] |
| anaemia_policy | lpdid_event | -2 | +0.051 | [-0.032, +0.133] |
| anaemia_policy | lpdid_event | +0 | -0.034 | [-0.125, +0.056] |
| anaemia_policy | lpdid_event | +1 | -0.061 | [-0.254, +0.133] |
| anaemia_policy | lpdid_event | +2 | -0.086 | [-0.380, +0.207] |
| anaemia_policy | lpdid_event | +3 | -0.125 | [-0.563, +0.312] |
| anaemia_policy | lpdid_event | +4 | -0.067 | [-0.630, +0.497] |
| anaemia_policy | lpdid_event | +5 | +0.015 | [-0.665, +0.695] |
| anaemia_policy | twfe_event | -4 | +0.653 | [-0.695, +2.001] |
| anaemia_policy | twfe_event | -3 | +0.284 | [-0.079, +0.646] |
| anaemia_policy | twfe_event | -2 | +0.172 | [-0.002, +0.346] |
| anaemia_policy | twfe_event | +0 | -0.248 | [-0.492, -0.004] |
| anaemia_policy | twfe_event | +1 | -0.426 | [-0.816, -0.037] |
| anaemia_policy | twfe_event | +2 | -0.693 | [-1.321, -0.065] |
| anaemia_policy | twfe_event | +3 | -0.897 | [-1.700, -0.094] |
| anaemia_policy | twfe_event | +4 | -1.068 | [-2.013, -0.122] |
| anaemia_policy | twfe_event | +5 | -1.103 | [-2.620, +0.413] |
| wheat_mandate | did2s_event | -4 | +0.039 | [-0.143, +0.232] |
| wheat_mandate | did2s_event | -3 | -0.115 | [-0.523, +0.219] |
| wheat_mandate | did2s_event | -2 | -0.092 | [-0.572, +0.351] |
| wheat_mandate | did2s_event | +0 | -0.093 | [-0.873, +0.648] |
| wheat_mandate | did2s_event | +1 | -0.137 | [-1.036, +0.759] |
| wheat_mandate | did2s_event | +2 | -0.269 | [-1.300, +0.852] |
| wheat_mandate | did2s_event | +3 | -0.100 | [-1.308, +1.138] |
| wheat_mandate | did2s_event | +4 | -0.623 | [-1.945, +0.677] |
| wheat_mandate | did2s_event | +5 | -1.621 | [-3.761, +0.390] |
| wheat_mandate | lpdid_event | -4 | -0.144 | [-0.589, +0.300] |
| wheat_mandate | lpdid_event | -3 | -0.068 | [-0.369, +0.234] |
| wheat_mandate | lpdid_event | -2 | -0.014 | [-0.170, +0.142] |
| wheat_mandate | lpdid_event | +0 | +0.019 | [-0.140, +0.178] |
| wheat_mandate | lpdid_event | +1 | +0.018 | [-0.317, +0.354] |
| wheat_mandate | lpdid_event | +2 | -0.033 | [-0.560, +0.494] |
| wheat_mandate | lpdid_event | +3 | +0.011 | [-0.746, +0.768] |
| wheat_mandate | lpdid_event | +4 | -0.305 | [-1.210, +0.601] |
| wheat_mandate | lpdid_event | +5 | -0.345 | [-1.544, +0.854] |
| wheat_mandate | twfe_event | -4 | -0.016 | [-1.331, +1.299] |
| wheat_mandate | twfe_event | -3 | -0.016 | [-0.382, +0.350] |
| wheat_mandate | twfe_event | -2 | +0.013 | [-0.173, +0.198] |
| wheat_mandate | twfe_event | +0 | -0.066 | [-0.302, +0.170] |
| wheat_mandate | twfe_event | +1 | -0.078 | [-0.473, +0.317] |
| wheat_mandate | twfe_event | +2 | -0.174 | [-0.774, +0.426] |
| wheat_mandate | twfe_event | +3 | -0.011 | [-0.897, +0.876] |
| wheat_mandate | twfe_event | +4 | -0.440 | [-1.458, +0.577] |
| wheat_mandate | twfe_event | +5 | -1.321 | [-3.039, +0.396] |

Reading (first anaemia policy): the two-way FE event study shows a post-adoption decline (mean -0.67 pp over years 0–4), but the pre-period slopes the same way (-0.11 pp per year; trend-adjusted post mean -0.33 pp), 27% of the static coefficient's weight is negative, and the two estimators built for staggered adoption put the effect at +0.10 pp (two-stage DiD) and -0.08 pp (local projections), both intervals straddling zero. The wheat-flour mandate shows no pre-trend and no post-period break under any estimator. The event study replaces the country-trend rows as the decisive dynamic check, because unit trends absorb effects that phase in slowly (Wolfers 2006; Meer & West 2016).

## 3. The dose ladder (coefficient on the listed term)

- **Main spec (two-way FE, SE clustered by country): -0.209 pp per active anaemia-cluster policy (t−3), 95% CI [-0.623, +0.204], p = 0.321, wild-cluster-bootstrap p = 0.326**, n = 994, 49 countries, two-way within-R² 0.023 [E:02_fe→spec_A]. Per within-country SD of the dose (1.66): -0.35 pp (SE 0.35) [E:02_fe→spec_A_std].
| variant | block | term | coef | 95% CI | p | p (BH) | p (wild bootstrap) | n | note |
|---|---|---|---:|---|---:|---:|---:|---:|---|
| A_main | main | `direct:stock_anaemia_policies_lag3` | -0.209 | [-0.623, +0.204] | 0.321 |  | 0.326 | 994 | main spec: anaemia-cluster policies active (GIFNA policies file, dated) lagged 3 y + log GDP pc (constant 2015 US$); country + year FE; SE clustered by country |
| lag2 | main | `direct:stock_anaemia_policies_lag2` | -0.248 | [-0.656, +0.160] | 0.233 |  | 0.240 | 1041 | policy lagged 2 years instead of 3 |
| lag5 | main | `direct:stock_anaemia_policies_lag5` | -0.156 | [-0.569, +0.257] | 0.459 |  | 0.456 | 900 | policy lagged 5 years instead of 3 |
| drop_thin | main | `direct:stock_anaemia_policies_lag3` | -0.214 | [-0.629, +0.201] | 0.312 |  | 0.332 | 977 | without SSD, ERI (thinnest income coverage) |
| income_current_usd | main | `direct:stock_anaemia_policies_lag3` | -0.154 | [-0.533, +0.226] | 0.427 |  | 0.420 | 1004 | log GDP pc in current US$ (team file) instead of constant 2015 US$ |
| lead_test_only | lead_test | `direct:stock_anaemia_policies_lead3` | -0.342 | [-0.655, -0.029] | 0.032 |  | 0.040 | 1088 | policy 3 years LATER instead of earlier — a lead that predicts today's anaemia signals pre-existing trend or targeting |
| lead_test_with_lag | lead_test | `direct:stock_anaemia_policies_lead3` | -0.274 | [-0.539, -0.009] | 0.043 |  | 0.069 | 947 | lead and lag together — the lead is the reported term |
| trend_main | trend | `direct:stock_anaemia_policies_lag3` | -0.017 | [-0.126, +0.091] | 0.756 |  |  | 994 | main spec plus a linear trend per country (absorbs slowly phasing-in effects too — Wolfers 2006) |
| trend_lead | trend | `direct:stock_anaemia_policies_lead3` | -0.028 | [-0.168, +0.112] | 0.696 |  |  | 1088 | lead test plus a linear trend per country |
| fd | bracket | `d1_direct:stock_anaemia_policies_lag3` | -0.013 | [-0.044, +0.018] | 0.415 |  | 0.395 | 945 | first differences (Δ outcome on Δ lagged policy and Δ log income, year effects) |
| longdiff5 | bracket | `d5_direct:stock_anaemia_policies_lag3` | -0.058 | [-0.235, +0.119] | 0.523 |  | 0.506 | 749 | 5-year differences |
| ldv | bracket | `direct:stock_anaemia_policies_lag3` | -0.025 | [-0.059, +0.009] | 0.154 |  | 0.161 | 994 | lagged outcome instead of country effects (year effects kept); with FE this brackets the effect |
| ctx_all | context | `direct:stock_anaemia_policies_lag3` | -0.052 | [-0.369, +0.265] | 0.748 |  | 0.749 | 931 | main spec + malaria incidence + fertility + urbanisation (complete World Bank series) |
| ctx_malaria | context | `direct:stock_anaemia_policies_lag3` | -0.037 | [-0.353, +0.279] | 0.819 |  | 0.818 | 931 | main spec + malaria incidence per 1,000 population at risk (WHO via World Bank SH.MLR.INCD.P3) |
| ctx_fertility | context | `direct:stock_anaemia_policies_lag3` | -0.131 | [-0.511, +0.249] | 0.499 |  | 0.491 | 994 | main spec + total fertility rate (World Bank SP.DYN.TFRT.IN) |
| ctx_urban | context | `direct:stock_anaemia_policies_lag3` | -0.206 | [-0.607, +0.194] | 0.311 |  | 0.311 | 994 | main spec + urban population, % of total (World Bank SP.URB.TOTL.IN.ZS) |
| ctx_hiv | context | `direct:stock_anaemia_policies_lag3` | -0.012 | [-0.362, +0.337] | 0.946 |  | 0.944 | 910 | main spec + HIV prevalence, % of population 15–49 (World Bank SH.DYN.AIDS.ZS) |
| ctx_sanitation | context | `direct:stock_anaemia_policies_lag3` | -0.222 | [-0.597, +0.152] | 0.244 |  | 0.247 | 982 | main spec + people using at least basic sanitation, % (WHO/UNICEF JMP via World Bank SH.STA.BASS.ZS) |
| team_unemployment | team | `direct:stock_anaemia_policies_lag3` | -0.171 | [-0.612, +0.270] | 0.448 |  | 0.461 | 972 | main spec + unemployment, % of labour force, ILO modelled (team file, World Bank SL.UEM.TOTL.ZS) (the team's ask) |
| team_employment | team | `direct:stock_anaemia_policies_lag3` | -0.173 | [-0.621, +0.275] | 0.449 |  | 0.459 | 972 | main spec + employment-to-population ratio 15+, ILO modelled (World Bank SL.EMP.TOTL.SP.ZS) (the team's ask) |
| impl_sth | implementation | `feat_sth_pc_coverage_sac_pct_lag3` | +0.001 | [-0.007, +0.009] | 0.796 |  | 0.782 | 744 | national coverage of preventive chemotherapy for soil-transmitted helminths, school-age children, % (WHO PCT databank; 0 = no treatment reported in a year the country required PC) lagged 3 y as the exposure (implementation, not policy on paper) |
| impl_sth_with_policy | implementation | `feat_sth_pc_coverage_sac_pct_lag3` | +0.001 | [-0.007, +0.009] | 0.797 |  | 0.788 | 744 | the same with the policy dose alongside; the reported term is the coverage |
| alt_logstock_anaemia_policies | alt_policy | `direct:logstock_anaemia_policies_lag3` | -0.566 | [-1.627, +0.495] | 0.296 |  | 0.314 | 994 | log(1 + anaemia-cluster policies active) lagged 3 y instead of the main dose |
| alt_team_anemia_programming_intensity | alt_policy | `team:anemia_programming_intensity_lag3` | -0.177 | [-0.410, +0.056] | 0.137 |  | 0.153 | 994 | team composite: anaemia programming intensity (sum of six flag counts) lagged 3 y instead of the main dose |
| alt_team_anemia_programming_intensity_trend | alt_policy | `team:anemia_programming_intensity_lag3` | +0.042 | [-0.018, +0.102] | 0.167 |  |  | 994 | team composite: anaemia programming intensity (sum of six flag counts) lagged 3 y plus a linear trend per country |
| alt_stock_anaemia | alt_policy | `direct:stock_anaemia_lag3` | -0.083 | [-0.317, +0.150] | 0.483 |  | 0.514 | 994 | anaemia-cluster records active, all three registry files lagged 3 y instead of the main dose |
| alt_logstock_anaemia | alt_policy | `direct:logstock_anaemia_lag3` | -0.278 | [-1.088, +0.532] | 0.501 |  | 0.539 | 994 | log(1 + anaemia-cluster records active, all files) lagged 3 y instead of the main dose |
| alt_any_anaemia_policies | alt_policy | `direct:any_anaemia_policies_lag3` | +0.811 | [-0.503, +2.124] | 0.226 |  | 0.199 | 994 | any anaemia-cluster policy ever adopted (0/1, absorbing) lagged 3 y instead of the main dose |
| alt_any_anaemia_policies_trend | alt_policy | `direct:any_anaemia_policies_lag3` | -0.716 | [-1.203, -0.229] | 0.004 |  |  | 994 | any anaemia-cluster policy ever adopted (0/1, absorbing) lagged 3 y plus a linear trend per country |
| alt_any_fortification | alt_policy | `direct:any_fortification_lag3` | -0.493 | [-2.130, +1.145] | 0.555 |  | 0.560 | 994 | any fortification record ever started (0/1, absorbing) lagged 3 y instead of the main dose |
| alt_any_fortification_trend | alt_policy | `direct:any_fortification_lag3` | +0.667 | [+0.025, +1.309] | 0.042 |  |  | 994 | any fortification record ever started (0/1, absorbing) lagged 3 y plus a linear trend per country |
| alt_team_policy_count_active | alt_policy | `team:policy_count_active_lag3` | -0.016 | [-0.198, +0.167] | 0.866 |  | 0.861 | 994 | active policies, any topic (team table) lagged 3 y instead of the main dose |
| outcome_out_anaemia_pregnant_pct | outcome_swap | `direct:stock_anaemia_policies_lag3` | -0.047 | [-0.271, +0.177] | 0.678 | 0.798 | 0.663 | 994 | outcome swapped: Anaemia, pregnant women (%) — WHO 2025 via UNICEF Aug-2025 |
| outcome_out_women_underweight_pct | outcome_swap | `direct:stock_anaemia_policies_lag3` | +0.058 | [-0.064, +0.179] | 0.353 | 0.798 | 0.344 | 947 | outcome swapped: Women underweight, BMI<18.5 (%) — NCD-RisC via UNICEF Aug-2025 |
| outcome_out_women_overweight_pct | outcome_swap | `direct:stock_anaemia_policies_lag3` | -0.117 | [-0.368, +0.134] | 0.361 | 0.798 | 0.356 | 947 | outcome swapped: Women overweight, BMI≥25 (%) — NCD-RisC via UNICEF Aug-2025 |
| outcome_out_lbw_pct | outcome_swap | `direct:stock_anaemia_policies_lag3` | -0.012 | [-0.107, +0.083] | 0.798 | 0.798 | 0.790 | 621 | outcome swapped: Low birthweight (%) — UNICEF-WHO via FAOSTAT FS 21049 (to 2020) |
| outcome_out_women_index | outcome_swap | `direct:stock_anaemia_policies_lag3` | -0.005 | [-0.020, +0.010] | 0.495 | 0.798 | 0.502 | 947 | outcome swapped: Women's nutrition summary index (mean z-score of four women's indicators; higher = worse) |
| survey_anchored | anchor | `direct:stock_anaemia_policies_lag3` | -0.036 | [-0.609, +0.537] | 0.899 |  | 0.833 | 80 | only country-years with a DHS survey that measured women's haemoglobin (the estimates are anchored there) |
| income_only | reference | `log_gdp_pc_constant` | +1.209 | [-1.510, +3.927] | 0.383 |  | 0.402 | 1135 | log GDP pc only — the reported term is the INCOME coefficient (reference row) |

All rows [E:02_fe→sensitivity]. Blocks: `main` = the specification and its lags and income measure; `lead_test` = the policy stock three years LATER (a lead that predicts today's anaemia signals pre-existing trend or targeting: -0.342 [-0.655, -0.029], p = 0.032, n = 1088); `trend` = a linear trend per country added (-0.017 [-0.126, +0.091], p = 0.756, n = 994), one sensitivity among several, not the verdict; `bracket` = first differences (-0.013 [-0.044, +0.018], p = 0.415, n = 945), 5-year differences (-0.058 [-0.235, +0.119], p = 0.523, n = 749) and the lagged-outcome model (-0.025 [-0.059, +0.009], p = 0.154, n = 994, persistence 0.987, implied long-run -1.94) — the fixed-effects and lagged-outcome estimates bracket the effect under their respective assumptions (Ding & Li 2019); `context` = the anaemia-literature drivers; `team` = the confounders the team asked for; `implementation` = delivered deworming coverage (WHO PCT databank, school-age children) as the exposure instead of the paper record, a contrast, not a control; `alt_policy` = other constructions of the exposure; `outcome_swap` = the other women's indicators, low birthweight and the summary index, with Benjamini–Hochberg-adjusted p-values across the five; `anchor` = survey-anchored country-years only.

### 3b. Sub-sample controls (base spec re-estimated on the same rows for comparison)

| control | from | model | coef | 95% CI | p | n |
|---|---:|---|---:|---|---:|---:|
| `feat_fies_severe_total_pct_3yr` | 2015 | base_same_rows | +0.031 | [-0.281, +0.343] | 0.845 | 280 |
| `feat_fies_severe_total_pct_3yr` | 2015 | with_control | +0.021 | [-0.279, +0.320] | 0.892 | 280 |
| `feat_fies_gap_fm_3yr` | 2015 | base_same_rows | +0.031 | [-0.281, +0.343] | 0.845 | 280 |
| `feat_fies_gap_fm_3yr` | 2015 | with_control | +0.058 | [-0.240, +0.356] | 0.702 | 280 |
| `feat_pua_pct` | 2017 | base_same_rows | +0.002 | [-0.253, +0.256] | 0.990 | 308 |
| `feat_pua_pct` | 2017 | with_control | -0.000 | [-0.250, +0.250] | 0.997 | 308 |
| `feat_hospital_beds_per1000` | 2000 | base_same_rows | -0.400 | [-0.970, +0.170] | 0.168 | 295 |
| `feat_hospital_beds_per1000` | 2000 | with_control | -0.417 | [-1.060, +0.227] | 0.203 | 295 |
| `feat_health_exp_pc_usd` | 2000 | base_same_rows | -0.192 | [-0.620, +0.236] | 0.379 | 969 |
| `feat_health_exp_pc_usd` | 2000 | with_control | -0.039 | [-0.395, +0.317] | 0.830 | 969 |
| `feat_sth_pc_coverage_sac_pct` | 2005 | base_same_rows | +0.037 | [-0.309, +0.383] | 0.833 | 796 |
| `feat_sth_pc_coverage_sac_pct` | 2005 | with_control | +0.037 | [-0.301, +0.375] | 0.829 | 796 |

[E:02_fe→subsample]. The FIES rows are 3-year moving averages and therefore autocorrelated by construction; the hospital-beds rows cover the country-years the series exists for.

## 4. What the null means: bounds, not absence

- Smallest effect of interest, pre-specified: 1.0 pp of anaemia per within-country SD of the dose (= 0.604 pp per active anaemia-cluster policy). Minimum detectable effect at 80% power: 0.591 pp per active anaemia-cluster policy = 0.98 pp per within-SD = 1.25 pp per overall SD [E:02_fe→bounds].
- 90% interval (the two one-sided tests): [-0.556, +0.137] pp per active anaemia-cluster policy, i.e. [-0.92, +0.23] pp per within-SD. TOST p = 0.031: the estimate is statistically equivalent to zero within the smallest effect of interest at the 5% level.
- Wording for the script: effects more beneficial than about 0.9 pp of anaemia per within-country SD of the policy dose are ruled out; smaller effects could not have been detected. For scale, halving anaemia from the regional mean of 39% is about 19 pp.

## 5. Specification curve

- 336 pre-specified specifications (exposure construction × estimator × income measure × lag × control set): median -0.02 pp per within-SD, interquartile range [-0.06, +0.00], range [-0.62, +0.43]; the interval excludes zero in 7% of specifications (4% negative, 2% positive) [E:02c_spec→share_ci_excludes_zero].
| estimator | specifications | median pp per within-SD | share excluding zero |
|---|---:|---:|---:|
| fe | 84 | -0.10 | 0% |
| fe_trend | 84 | -0.01 | 20% |
| fd | 84 | -0.01 | 4% |
| ldv | 84 | -0.03 | 2% |

By exposure [E:02c_spec→by_exposure]: anaemia-cluster policies active (GIFNA policies file, dated) median -0.04 (0% exclude zero); log(1 + anaemia-cluster policies active) median -0.04 (6% exclude zero); team composite: anaemia programming intensity (sum of six flag counts) median -0.02 (8% exclude zero); anaemia-cluster records active, all three registry files median -0.01 (0% exclude zero); log(1 + anaemia-cluster records active, all files) median -0.03 (0% exclude zero); any anaemia-cluster policy ever adopted (0/1, absorbing) median +0.00 (21% exclude zero); any fortification record ever started (0/1, absorbing) median -0.01 (10% exclude zero).

## 6. Leave-one-country-out validation

| model | RMSE (pp) | MAE | R² of deviations |
|---|---:|---:|---:|
| naive_flat | 2.50 | 1.96 | 0.000 |
| M0_year_effects | 1.91 | 1.35 | 0.412 |
| M1_income | 1.92 | 1.35 | 0.407 |
| M2_income_policy | 1.93 | 1.38 | 0.399 |
| M2t_income_team_composite | 1.92 | 1.39 | 0.409 |
| M3_income_all_exposures | 1.93 | 1.43 | 0.402 |

Adding the policy dose to the income model changes held-out RMSE by +0.7% (+0.013 pp; country-bootstrap 95% interval [-0.030, +0.061]) [E:03_loco→m2_vs_m1_rmse_diff_boot95]; calibration r = 0.63; the dose lowers a country's own held-out error in 22 of 49 countries (binomial p = 0.57) [E:03_loco→countries_where_policy_helps]. Context ladder on its own sample (46 countries): C1_income 1.70, C2_income_context 1.70, C3_income_context_policy 1.72 [E:03_loco→context_ladder]. Method: within-country deviations from own mean; year effects transferred from the training set; common estimation sample.

## 7. Who beats their context (question 3)

- Income-only cross-country model (v1.2's ranking, kept for continuity): -1.72 pp per log-unit of GDP pc, R² 0.060, n = 1135 [E:04_residuals→income_only]; its residual ranking is the level ranking (Spearman with the raw level 0.98).
- Context model (year effects + log income + malaria incidence + fertility + urbanisation + UNICEF sub-region + terrain): R² 0.806, n = 1046, 45 countries [E:04_residuals→context_model]. Spearman of its residual ranking with the raw level 0.27, with the income-only ranking 0.27, with the fixed-effects country effect 0.23; the tails overlap the raw-level tails in 3/8 and 2/8 [E:04_residuals→ranking_vs_level]. Not ranked: {'ERI': None, 'GNQ': 3, 'LSO': None, 'MUS': None, 'SSD': None, 'SYC': None} [E:04_residuals→excluded_from_context_ranking].
- Context-model coefficients: C(subregion)[T.WCA] +11.46 (p 0.00); log_gdp_pc_constant +0.02 (p 0.99); feat_malaria_incidence_per1000 +0.01 (p 0.38); feat_fertility_rate +3.85 (p 0.00); feat_urban_pct +0.16 (p 0.02); feat_sanitation_basic_pct +0.03 (p 0.55); geo_rugged -2.79 (p 0.00); geo_tropical -0.03 (p 0.14); geo_dist_coast -7.38 (p 0.00).
- Lower than their context predicts (mean 2015–2023): Nigeria (-9.6 pp; level 39.6%); Namibia (-9.0 pp; level 21.6%); Cameroon (-9.0 pp; level 37.8%); Ghana (-6.7 pp; level 37.1%); Liberia (-6.4 pp; level 40.7%); Democratic Republic of the Congo (-6.1 pp; level 40.1%); Ethiopia (-4.6 pp; level 20.5%); Zambia (-4.5 pp; level 26.4%) [E:04_residuals→positive_deviants].
- Higher than their context predicts: Comoros (+4.4 pp; level 28.0%); Eswatini (+4.4 pp; level 25.5%); Madagascar (+5.7 pp; level 35.1%); United Republic of Tanzania (+6.4 pp; level 37.6%); Mali (+7.3 pp; level 54.6%); Gabon (+8.0 pp; level 59.5%); Burundi (+8.2 pp; level 33.9%); Mozambique (+11.2 pp; level 45.9%) [E:04_residuals→under_performers].
- The income-only tails for comparison — lower: Rwanda, Ethiopia, Namibia, Uganda, Zimbabwe, Zambia, Eswatini, Malawi; higher: Chad, Gambia, Congo, Benin, Côte d'Ivoire, Mauritania, Mali, Gabon; overlap with the context tails 3/8 and 2/8 [E:04_residuals→tails_overlap_context_vs_income].
- Policy record of the two context tails (means over 2015–2023, Mann-Whitney, 8 vs 8 countries) [E:04_residuals→policy_stock_contrast]:

| exposure | lower-than-context mean | higher-than-context mean | p |
|---|---:|---:|---:|
| anaemia-cluster policies active (GIFNA policies file, dated) | 4.54 | 2.75 | 0.115 |
| log(1 + anaemia-cluster policies active) | 1.60 | 1.18 | 0.105 |
| team composite: anaemia programming intensity (sum of six flag counts) | 10.85 | 6.62 | 0.074 |
| anaemia-cluster records active, all three registry files | 5.39 | 3.68 | 0.172 |
| log(1 + anaemia-cluster records active, all files) | 1.76 | 1.36 | 0.130 |
| any anaemia-cluster policy ever adopted (0/1, absorbing) | 1.00 | 0.97 | 0.382 |
| any fortification record ever started (0/1, absorbing) | 1.00 | 1.00 | n/a (no variation) |
| active policies, any topic (team table) | 15.67 | 11.04 | 0.130 |

Dated anaemia-policy stock of the two tails over time [E:04_residuals→timeline]:

| group | country | 2005 | 2010 | 2015 | 2020 | 2023 | first anaemia policy | wheat mandate |
|---|---|---:|---:|---:|---:|---:|---:|---|
| positive deviant | Nigeria | 2 | 3 | 6 | 5 | 9 | 2004 | YES (2005) |
| positive deviant | Namibia | 0 | 0 | 2 | 1 | 1 | 2011 | NO |
| positive deviant | Cameroon | 1 | 2 | 5 | 5 | 5 | 1996 | YES (2011) |
| positive deviant | Ghana | 1 | 5 | 6 | 7 | 6 | 1995 | YES (2010) |
| positive deviant | Liberia | 0 | 1 | 2 | 3 | 3 | 2008 | YES (2017) |
| positive deviant | Democratic Republic of the Congo | 1 | 1 | 2 | 2 | 4 | 1994 | UNKNOWN |
| positive deviant | Ethiopia | 2 | 3 | 3 | 7 | 5 | 2005 | YES (2022) |
| positive deviant | Zambia | 2 | 5 | 7 | 7 | 6 | 1978 | NO |
| under-performer | Comoros | 0 | 0 | 1 | 1 | 2 | 2012 | UNKNOWN |
| under-performer | Eswatini | 0 | 2 | 3 | 3 | 2 | 2008 |  |
| under-performer | Madagascar | 1 | 1 | 2 | 0 | 2 | 2004 | UNKNOWN |
| under-performer | United Republic of Tanzania | 0 | 3 | 6 | 5 | 2 | 2008 |  |
| under-performer | Mali | 0 | 1 | 4 | 3 | 3 | 2006 | YES (2010) |
| under-performer | Gabon | 0 | 0 | 0 | 1 | 1 | 2017 | UNKNOWN |
| under-performer | Burundi | 1 | 1 | 3 | 4 | 4 | 2003 | YES (2015) |
| under-performer | Mozambique | 0 | 0 | 5 | 4 | 4 | 2011 | YES (2016) |

No exposure separates the tails; the records of the countries that beat their context look like everyone else's. GIFNA counts measure reporting as much as programming, so none of this is evidence about what produces the lower levels.

## 8. Do the estimators agree? (replaces the R replica)

| estimator | estimand | estimate | 95% CI | p |
|---|---|---:|---|---:|
| two-way FE (levels) | pp per active anaemia-cluster policy | -0.209 | [-0.623, +0.204] | 0.321 |
| first differences | pp per active anaemia-cluster policy | -0.013 | [-0.044, +0.018] | 0.415 |
| 5-year differences | pp per active anaemia-cluster policy | -0.058 | [-0.235, +0.119] | 0.523 |
| lagged outcome | pp per active anaemia-cluster policy | -0.025 | [-0.059, +0.009] | 0.154 |
| FE + country trends | pp per active anaemia-cluster policy | -0.017 | [-0.126, +0.091] | 0.756 |
| static two-way FE, first dated anaemia-cluster policy (GIFNA policies file) | ATT, pp | -0.939 | [-1.972, +0.094] | 0.084 |
| two-stage DiD, first dated anaemia-cluster policy (GIFNA policies file) | ATT, pp | +0.098 | [-2.042, +2.086] | 0.928 |
| local-projections DiD, first dated anaemia-cluster policy (GIFNA policies file) | ATT, pp | -0.080 | [-0.455, +0.295] | 0.678 |
| static two-way FE, mandatory wheat-flour fortification (GFDx) | ATT, pp | -0.564 | [-2.064, +0.936] | 0.465 |
| two-stage DiD, mandatory wheat-flour fortification (GFDx) | ATT, pp | -1.052 | [-2.595, +0.393] | 0.184 |
| local-projections DiD, mandatory wheat-flour fortification (GFDx) | ATT, pp | -0.173 | [-0.844, +0.499] | 0.616 |

Agreement is read on the sign of the interval, not the point estimate: every interval straddles zero, and the two estimators built for staggered adoption sit closer to zero than the static two-way FE row they correct.

## 9. Survey-anchored row

- Only country-years in which a DHS survey measured women's haemoglobin (80 rows, 33 countries): -0.036 pp per active anaemia-cluster policy (SE 0.278, p = 0.899) [E:02_fe→survey_anchored]. This is the sample in which the WHO estimate is anchored by data rather than by its covariates; it is small, and it says the same thing.

## 10. Figures

- `results/figures/fig_sensitivity.png` — the dose ladder: main, lags, lead test, trends, bracket, context, team and survey-anchored rows
- `results/figures/fig_event_study.png` — event studies around the first anaemia policy and the wheat-flour mandate (three estimators)
- `results/figures/fig_spec_curve.png` — specification curve over exposure × estimator × income × lag × controls
- `results/figures/fig_loco.png` — leave-one-country-out RMSE by nested model
- `results/figures/fig_calibration.png` — LOCO calibration scatter for the income + policy model
- `results/figures/fig_residuals.png` — context ranking (residual from the context model), recent window
- `results/figures/fig_rankings_compare.png` — income-only vs context residuals, one point per country
- `results/figures/fig_map.png` — choropleth of the context ranking (plotly/kaleido)
- `results/figures/fig_trends_anaemia.png` — anaemia small multiples, 49 countries

## 11. Caveats that ride with every number

- The outcome is a modelled series: the WHO anaemia model pools sparse surveys and uses the Socio-Demographic Index, meat supply and mean BMI as covariates, so in a country-year without a survey the value is a covariate prediction; within-country movement is partly the estimation model's smoothing (within-country autocorrelation about 0.98). Associations, not effects.
- GIFNA records what governments reported, not funding or implementation; policy counts measure reporting intensity. The within-country design uses only records with a real start year (policies; mechanisms for the all-file stocks); programme rows are questionnaire answers dated by survey round and are used descriptively only. Records without a usable date are excluded and counted in the readiness report.
- Event studies: small cohorts and few never-adopters make the intervals wide; countries that adopted before the window has two pre-years are excluded, not used as controls; the static two-way FE row carries negative weights (§2) and is reported only next to the estimators that correct it.
- Malaria incidence, HIV and health-system series can sit downstream of the same policy commitment (bad controls); the context rows are reported next to the main row, not instead of it.
- The context ranking inherits every omitted driver and the modelled outcome's smoothing; it is a screening device for the profiles, never a verdict on a country.
- The within-country coefficient is identified from 44 countries; ERI contributes income data to 2011 only.
