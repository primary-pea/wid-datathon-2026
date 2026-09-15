"""Single configuration block for the SSA maternal-nutrition scaffold (v2.0, 2026-09-12).

Every parameter the pipeline uses lives here. Scripts import it as ``cfg`` — never as ``C``, because patsy formulas
use ``C()`` and the alias shadows it. Run from anywhere: ``.venv/bin/python scaffold/<NN>_*.py``.

v2.0 (methodology audit of 12 Sep 2026, research/scaffold-v2-methodology-audit.md): dated-only exposure for the
within-country design, an event study with heterogeneity-robust estimators, first-difference / lagged-outcome bracket
rows, context controls from the anaemia literature, equivalence bounds, a specification curve, a survey-anchored row,
a women's-nutrition summary index and a context-adjusted positive-deviance ranking.

Two environment overrides let the same files run unchanged in the private repo and in the shared team repo:

* ``SCAFFOLD_PANEL_DIR`` — where the panel, its dictionary, readiness and manifest live. Default: ``scaffold/panel/``
  when it holds a panel; otherwise the shared repo's ``derived/`` (the team-facing location).
* ``SCAFFOLD_ATLAS_DIR`` / ``SCAFFOLD_REPO_DIR`` — raw-input locations read by ``00_assemble_panel.py``.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

CONFIG_VERSION = "2026-09-13a"  # bump whenever a parameter below changes
SCAFFOLD_VERSION = "v2.0"
RUN_DATE = date.today().isoformat()  # the real run date, stamped at run time

SCAF = Path(__file__).resolve().parent
ROOT = SCAF.parent  # the folder scaffold/ sits in
INPUTS = SCAF / "inputs"  # pinned lookups and small interim inputs, committed with the code
RESULTS = SCAF / "results"
FIGS = RESULTS / "figures"
STATS = RESULTS / "stats"
FRAME_CSV = RESULTS / "frame.csv"


def _default_panel_dir() -> Path:
    local, shared = SCAF / "panel", ROOT.parent / "derived"
    if (local / "ssa_panel.csv").exists() or not (shared / "ssa_panel.csv").exists():
        return local
    return shared


PANEL_DIR = Path(os.environ.get("SCAFFOLD_PANEL_DIR", _default_panel_dir()))
PANEL_CSV = PANEL_DIR / "ssa_panel.csv"
EVENTS_CSV = PANEL_DIR / "events.csv"  # one row per country: dated policy and legislation events (v2.0)
MANIFEST = PANEL_DIR / "MANIFEST.json"
DATA_VERSION_FILE = PANEL_DIR / "data_version.txt"


def data_version() -> str:
    """Content-derived panel version (first 12 hex digits of the panel's sha256), written by 00_assemble_panel.py."""
    return DATA_VERSION_FILE.read_text(encoding="utf-8").strip() if DATA_VERSION_FILE.exists() else "unbuilt"


# ---- countries ---------------------------------------------------------------
# The 49-country list is pinned here; the team CSV (subsaharan_data/subsahran_africa_countries.csv) is provenance only
# and is cross-checked, not depended on (its encoding is not valid UTF-8). It is exactly UNICEF's Eastern and Southern
# Africa (25) plus West and Central Africa (24) — data.unicef.org/regionalclassifications.
SSA_ISO3 = [
    "AGO", "BDI", "BEN", "BFA", "BWA", "CAF", "CIV", "CMR", "COD", "COG", "COM", "CPV", "DJI", "ERI", "ETH", "GAB",
    "GHA", "GIN", "GMB", "GNB", "GNQ", "KEN", "LBR", "LSO", "MDG", "MLI", "MOZ", "MRT", "MUS", "MWI", "NAM", "NER",
    "NGA", "RWA", "SDN", "SEN", "SLE", "SOM", "SSD", "STP", "SWZ", "SYC", "TCD", "TGO", "TZA", "UGA", "ZAF", "ZMB",
    "ZWE",
]  # fmt: skip
WCA = {
    "BEN", "BFA", "CPV", "CMR", "CAF", "TCD", "COG", "CIV", "COD", "GNQ", "GAB", "GMB", "GHA", "GIN", "GNB", "LBR",
    "MLI", "MRT", "NER", "NGA", "STP", "SEN", "SLE", "TGO",
}  # fmt: skip
SUBREGION = {iso: ("WCA" if iso in WCA else "ESA") for iso in SSA_ISO3}  # UNICEF West & Central / Eastern & Southern
COUNTRY_CODES_CSV = (
    INPUTS / "country_codes_ssa.csv"
)  # iso3, iso2, m49, faostat_area_code, names — every join uses a code
YEARS = range(2000, 2026)

# ---- outcomes ---------------------------------------------------------------
OUTCOME = "out_anaemia_wra_fs_pct"
OUTCOME_LABEL = "Anaemia prevalence, women 15–49 (%)"
OUTCOME_SOURCE = (
    "WHO 2025 estimates (GHO indicator 4552, Bayesian hierarchical model on 412 surveys from 122 countries) "
    "as republished in FAOSTAT FS item 21043, July-2026 release"
)
SECONDARY = {
    "out_anaemia_pregnant_pct": "Anaemia, pregnant women (%) — WHO 2025 via UNICEF Aug-2025",
    "out_women_underweight_pct": "Women underweight, BMI<18.5 (%) — NCD-RisC via UNICEF Aug-2025",
    "out_women_overweight_pct": "Women overweight, BMI≥25 (%) — NCD-RisC via UNICEF Aug-2025",
    "out_lbw_pct": "Low birthweight (%) — UNICEF-WHO via FAOSTAT FS 21049 (to 2020)",
    "out_women_index": "Women's nutrition summary index (mean z-score of four women's indicators; higher = worse)",
}
WOMEN_INDEX_COMPONENTS = [
    "out_anaemia_wra_fs_pct",
    "out_anaemia_pregnant_pct",
    "out_women_underweight_pct",
    "out_women_overweight_pct",
]

# ---- exposure (the policy record) --------------------------------------------
# v2.0: the within-country design uses dated sources only. The main dose is the number of anaemia-cluster POLICIES
# active in the year (policies carry adoption years; programme rows are questionnaire answers dated by survey round and
# stay in the profiles). The team composite and the all-source stocks are kept as alternative-exposure rows.
POLICY_MAIN = "feat_gd_stock_anaemia_policies"
POLICY_UNIT = "active anaemia-cluster policy"
POLICY_TEAM = "feat_gifna_anemia_programming_intensity"
POLICY_ALL = [
    "feat_gd_stock_anaemia_policies",
    "feat_gd_logstock_anaemia_policies",
    "feat_gifna_anemia_programming_intensity",
    "feat_gd_stock_anaemia",
    "feat_gd_logstock_anaemia",
    "feat_gd_any_anaemia_policies",
    "feat_gd_any_fortification",
    "feat_gifna_policy_count_active",
]
POLICY_LABELS = {
    "feat_gd_stock_anaemia_policies": "anaemia-cluster policies active (GIFNA policies file, dated)",
    "feat_gd_logstock_anaemia_policies": "log(1 + anaemia-cluster policies active)",
    "feat_gifna_anemia_programming_intensity": "team composite: anaemia programming intensity (sum of six flag counts)",
    "feat_gd_stock_anaemia": "anaemia-cluster records active, all three registry files",
    "feat_gd_logstock_anaemia": "log(1 + anaemia-cluster records active, all files)",
    "feat_gd_any_anaemia_policies": "any anaemia-cluster policy ever adopted (0/1, absorbing)",
    "feat_gd_any_fortification": "any fortification record ever started (0/1, absorbing)",
    "feat_gifna_policy_count_active": "active policies, any topic (team table)",
}
GIFNA_SOURCE_URL = "https://gifna.who.int/"
# GIFNA count columns that the feature table leaves NaN when no record is active (they do not end in _count)
GIFNA_NAN_IS_ZERO = [
    "feat_gifna_policy_count_active",
    "feat_gifna_programme_count_active",
    "feat_gifna_mechanism_count_active",
]

# ---- income and controls -------------------------------------------------------
INCOME = "feat_gdp_pc_constant_2015_usd"  # World Bank NY.GDP.PCAP.KD, pinned API pull with provenance (real income)
INCOME_ALT = "feat_gdp_pc_current_usd"  # team file (World Bank NY.GDP.PCAP.CD; the file header says "Constant" but it is current)
LOG_INCOME = "log_gdp_pc_constant"
LOG_INCOME_ALT = "log_gdp_pc_current"
# Context block: within-country drivers of women's anaemia named by the literature (WHO 2023 framework; Balarajan 2011;
# Chaparro & Suchdev 2019): infection (malaria, HIV), fertility, urbanisation. Complete World Bank series, pinned.
CONTEXT = ["feat_malaria_incidence_per1000", "feat_fertility_rate", "feat_urban_pct"]
CONTEXT_EXTRA = ["feat_hiv_prev_pct", "feat_sanitation_basic_pct"]  # one-at-a-time context rows
RANKING_EXTRA = ["feat_sanitation_basic_pct"]  # added to the context ranking model (Smith & Haddad 2015)
TEAM_CONTROLS = ["feat_unemployment_pct", "feat_employment_pop_pct"]  # the team's ask (courtesy rows)
CONTROL_LABELS = {
    "feat_malaria_incidence_per1000": "malaria incidence per 1,000 population at risk (WHO via World Bank SH.MLR.INCD.P3)",
    "feat_fertility_rate": "total fertility rate (World Bank SP.DYN.TFRT.IN)",
    "feat_urban_pct": "urban population, % of total (World Bank SP.URB.TOTL.IN.ZS)",
    "feat_hiv_prev_pct": "HIV prevalence, % of population 15–49 (World Bank SH.DYN.AIDS.ZS)",
    "feat_sanitation_basic_pct": "people using at least basic sanitation, % (WHO/UNICEF JMP via World Bank SH.STA.BASS.ZS)",
    "feat_sth_pc_coverage_sac_pct": "national coverage of preventive chemotherapy for soil-transmitted helminths, school-age children, % (WHO PCT databank; 0 = no treatment reported in a year the country required PC)",  # noqa: E501
    "feat_unemployment_pct": "unemployment, % of labour force, ILO modelled (team file, World Bank SL.UEM.TOTL.ZS)",
    "feat_employment_pop_pct": "employment-to-population ratio 15+, ILO modelled (World Bank SL.EMP.TOTL.SP.ZS)",
    "feat_health_exp_pc_usd": "current health expenditure per capita, US$ (World Bank SH.XPD.CHEX.PC.CD)",
    "feat_hospital_beds_per1000": "hospital beds per 1,000 people (team file, World Bank SH.MED.BEDS.ZS; sparse)",
    "feat_fies_gap_fm_3yr": "FIES severe food insecurity, women minus men, 3-year average (pp)",
    "feat_fies_severe_total_pct_3yr": "FIES severe food insecurity, total, 3-year average (%)",
    "feat_pua_pct": "prevalence of unaffordability of a healthy diet (%)",
}
SUBPERIOD = {  # control -> first usable year; each runs on its own rows next to the base spec on the same rows
    "feat_fies_severe_total_pct_3yr": 2015,
    "feat_fies_gap_fm_3yr": 2015,
    "feat_pua_pct": 2017,
    "feat_hospital_beds_per1000": 2000,
    "feat_health_exp_pc_usd": 2000,
    "feat_sth_pc_coverage_sac_pct": 2005,
}
IMPLEMENTATION = [
    "feat_sth_pc_coverage_sac_pct"
]  # delivered deworming (WHO PCT databank): implementation, not policy on paper
SURVEY_FLAG = (
    "feat_dhs_anaemia_survey"  # 1 in a country-year with a DHS haemoglobin survey of women (survey-anchored row)
)
GEOGRAPHY = ["geo_rugged", "geo_tropical", "geo_dist_coast"]  # time-invariant (Nunn & Puga 2012); ranking model only

# ---- windows and rules ------------------------------------------------------
YEAR_MIN, YEAR_MAX = 2000, 2023
LAG = 3
LAGS_SENS = [2, 3, 5]
LEAD = 3
LONG_DIFF = 5
THIN = ["SSD", "ERI"]  # thinnest income coverage; dropped in one sensitivity run
RECENT_FROM = 2015  # window for the level/residual ranking
MIN_YEARS_RECENT = 5  # a country needs at least this many window years to be ranked
N_DEVIANTS = 8  # countries listed at each end of the ranking
CLUSTER = "iso3"
SESOI_PP_PER_WITHIN_SD = (
    1.0  # smallest effect of interest: 1 pp of anaemia per within-country SD of the exposure (pre-specified)
)
WCB_B = 999  # wild cluster bootstrap draws (Rademacher, null imposed)
SEED = 20260912
ES_PRE, ES_POST, ES_REF = (
    4,
    5,
    -1,
)  # event-study window: leads up to 4 years (binned), lags up to 5 (binned), reference t−1
EVENTS = {
    "anaemia_policy": {
        "column": "first_anaemia_policy_year",
        "label": "first dated anaemia-cluster policy (GIFNA policies file)",
    },
    "wheat_mandate": {"column": "gfdx_wheat_mandate_year", "label": "mandatory wheat-flour fortification (GFDx)"},
}

# ---- expected coverage gaps (facts of the sources; anything beyond these fails the assembly) -----------------
EXPECTED_MISSING = {
    "out_lbw_pct": {"CPV", "DJI", "ETH", "GIN", "GNQ", "MLI", "MRT", "NER", "NGA", "SDN", "SOM", "SSD", "TCD", "UGA"},
    "out_wasting_u5_pct": {"MUS"},
    "out_ebf_0_5mo_pct": {"MUS", "SYC"},
    "feat_cohd_ppp_per_day": {"ERI", "SDN", "SOM", "ZWE"},
    "feat_pua_pct": {"ERI", "SDN", "SOM", "ZWE"},
    "feat_nua_million": {"ERI", "SDN", "SOM", "ZWE"},
    "feat_fies_*": {"COG", "ERI", "GAB", "GIN", "GNQ", "MOZ", "RWA", "SDN", "SOM"},
}


# ---- claim-tag helper -------------------------------------------------------
def tag(script: str, key: str) -> str:
    return f"[E:{script}→{key}]"
