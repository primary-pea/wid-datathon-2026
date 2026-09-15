"""Write the dashboard's precomputed JSON from the pipeline's results and the panel.

Nothing is computed on a server: this script is the only step between scaffold v2.0
(data version afe63e46c26b) and the static page at primary-pea.github.io/dashboard/
(page source: the primary-pea/dashboard repo). Run it from anywhere after a pipeline
re-run, then commit dashboard/data/.

    python dashboard/build_data.py [--out DIR]

Files written: meta.json (versions, headline numbers, labels, the 47 cluster rules),
countries.json (one record per country), series.json (per-country-year outcomes and
per-cluster policy stocks), model.json (ladder, event studies, validation, contrast,
specification curve).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pycountry

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]                       # the repo root
RESULTS = ROOT / "scaffold" / "results"
PANEL = ROOT / "derived" / "ssa_panel.csv"
RULES = ROOT / "scaffold" / "inputs" / "gifna_cluster_rules.csv"
DEFAULT_OUT = HERE.parent / "data"

YEAR_MIN, YEAR_MAX = 2000, 2023
RECENT_FROM = 2015

# Outcomes the page can switch between: column -> (label, unit, source). Sources follow 00_assemble_panel.py.
OUTCOMES = {
    "out_anaemia_wra_fs_pct": ("Anaemia, women 15–49", "%", "WHO estimates, FAOSTAT item 21043"),
    "out_anaemia_pregnant_pct": ("Anaemia, pregnant women", "%", "WHO estimates via UNICEF"),
    "out_women_underweight_pct": ("Women underweight, BMI under 18.5", "%", "NCD-RisC via UNICEF"),
    "out_women_overweight_pct": ("Women overweight, BMI 25 and over", "%", "NCD-RisC via UNICEF"),
    "out_lbw_pct": ("Low birthweight", "%", "UNICEF and WHO, FAOSTAT item 21049; 35 countries"),
    "out_stunting_u5_pct": ("Stunting, children under 5", "%", "JME, FAOSTAT item 21025"),
    "out_u5mr_per1000": ("Under-5 mortality", "per 1,000 live births", "UN IGME"),
}
# GIFNA topic clusters, in the order gifna_direct.py defines them, plus two totals.
CLUSTERS = {
    "anaemia": "Anaemia (iron, folate, MMS)",
    "fortification": "Fortification",
    "micronutrient": "Other micronutrients",
    "maternal": "Maternal and women",
    "iycf": "Infant and young child feeding",
    "wasting_stunting": "Wasting and stunting",
    "infection": "Infection and WASH",
    "food_security": "Food security and agriculture",
    "ncd_diet": "Diet and NCDs",
    "schools_education": "Schools and education",
    "governance": "Governance and monitoring",
    "all": "All records, any topic",
    "policies": "All policies (dated file)",
}
STOCK_MAIN = "feat_gd_stock_anaemia_policies"  # the model's dose: anaemia-cluster records in the dated policies file
SUBREGIONS = {"WCA": "West and Central Africa", "ESA": "Eastern and Southern Africa"}
# Small islands that Natural Earth 110m leaves out: (lon, lat) so they can still be drawn and clicked.
CENTROIDS = {"CPV": (-23.6, 15.1), "COM": (43.9, -11.9), "MUS": (57.6, -20.3), "STP": (6.7, 0.3), "SYC": (55.5, -4.7)}

LADDER = {  # variant -> (block, label)
    "A_main": ("main", "Main model: three-year lag, income, country and year effects"),
    "lag2": ("lags", "Two-year lag"),
    "lag5": ("lags", "Five-year lag"),
    "drop_thin": ("guards", "Drop thinly observed countries"),
    "income_current_usd": ("guards", "Income in current US$"),
    "lead_test_only": ("lead", "Lead test: policies three years in the future"),
    "lead_test_with_lag": ("lead", "Lead test, with the lag alongside"),
    "trend_main": ("trend", "Country-specific trends"),
    "trend_lead": ("trend", "Country-specific trends, lead"),
    "fd": ("bracket", "First differences"),
    "longdiff5": ("bracket", "Five-year differences"),
    "ldv": ("bracket", "Lagged outcome"),
    "ctx_all": ("context", "All context controls"),
    "ctx_malaria": ("context", "With malaria incidence"),
    "ctx_fertility": ("context", "With fertility rate"),
    "ctx_urban": ("context", "With urban share"),
    "ctx_hiv": ("context", "With HIV prevalence"),
    "ctx_sanitation": ("context", "With basic sanitation"),
    "team_unemployment": ("context", "With unemployment"),
    "team_employment": ("context", "With employment rate"),
    "impl_sth_with_policy": ("context", "With deworming coverage, 2006 on"),
    "survey_anchored": ("sample", "Survey-anchored years only, 33 countries"),
    "sub_feat_fies_severe_total_pct_3yr": ("sample", "With severe food insecurity, 2015 on"),
    "sub_feat_fies_gap_fm_3yr": ("sample", "With the food-insecurity gender gap, 2015 on"),
    "sub_feat_pua_pct": ("sample", "With unaffordable-diet share, 2017 on"),
    "sub_feat_hospital_beds_per1000": ("sample", "With hospital beds"),
    "sub_feat_health_exp_pc_usd": ("sample", "With health spending per head"),
    "sub_feat_sth_pc_coverage_sac_pct": ("sample", "With deworming coverage, 2005 on"),
}
ALT = {  # other doses: variant -> (label, unit)
    "alt_logstock_anaemia_policies": ("log(1 + policies)", "pp per log unit"),
    "alt_stock_anaemia": ("Anaemia records, all three registry files", "pp per record"),
    "alt_logstock_anaemia": ("log(1 + records, all files)", "pp per log unit"),
    "alt_any_anaemia_policies": ("Any anaemia policy ever adopted (0/1)", "pp when switched on"),
    "alt_any_anaemia_policies_trend": ("Any policy ever, with country trends", "pp when switched on"),
    "alt_any_fortification": ("Any fortification record ever (0/1)", "pp when switched on"),
    "alt_any_fortification_trend": ("Any fortification, with country trends", "pp when switched on"),
    "alt_team_anemia_programming_intensity": ("Team composite: anaemia programming intensity", "pp per point"),
    "alt_team_anemia_programming_intensity_trend": ("Team composite, with country trends", "pp per point"),
    "alt_team_policy_count_active": ("Active policies, any topic (team table)", "pp per policy"),
}
EVENTS = {"anaemia_policy": "First dated anaemia policy", "wheat_mandate": "Wheat-flour fortification mandate"}
ESTIMATORS = {"twfe": "Two-way fixed effects", "did2s": "Two-stage DiD (Gardner)", "lpdid": "Local-projections DiD"}


def clean(x):
    """JSON has no NaN: round floats, and turn anything missing into None."""
    if x is None:
        return None
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, (np.integer, int)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return None if not np.isfinite(x) else round(float(x), 4)
    if isinstance(x, str):
        return x
    return x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    out = ap.parse_args().out
    out.mkdir(parents=True, exist_ok=True)

    panel = pd.read_csv(PANEL)
    panel = panel[(panel.year >= YEAR_MIN) & (panel.year <= YEAR_MAX)].copy()
    resid = pd.read_csv(RESULTS / "residuals_by_country.csv")
    concern = pd.read_csv(RESULTS / "concern_score.csv").set_index("iso3")
    deviants = pd.read_csv(RESULTS / "deviants_policy_stock.csv").set_index("iso3")
    loco = pd.read_csv(RESULTS / "loco_per_country.csv").set_index("iso3")
    loco_rmse = pd.read_csv(RESULTS / "loco_rmse.csv")
    spec = pd.read_csv(RESULTS / "spec_curve.csv")
    sens = pd.read_csv(RESULTS / "fe_sensitivity.csv")
    coefs = pd.read_csv(RESULTS / "fe_coefficients.csv")
    ev = pd.read_csv(RESULTS / "event_study.csv")
    att = pd.read_csv(RESULTS / "event_att.csv")
    contrast = pd.read_csv(RESULTS / "deviant_contrast.csv")
    rules = pd.read_csv(RULES)
    stats = {n: json.loads((RESULTS / "stats" / f"{n}.json").read_text()) for n in
             ("02_fe", "02c_spec", "03_loco", "04_residuals", "08_concern")}
    fe, sp, lo, rs, cs = (stats[k] for k in ("02_fe", "02c_spec", "03_loco", "04_residuals", "08_concern"))

    years = list(range(YEAR_MIN, YEAR_MAX + 1))
    isos = resid["iso3"].tolist()

    # ---------------- meta: versions, the headline numbers, labels, the rules ----------------
    meta = {
        "scaffold": "v2.0",
        "data_version": fe["data_version"],
        "config_version": fe["config_version"],
        "results_run_at": fe["run_at"],
        "years": years,
        "recent_from": RECENT_FROM,
        "n_countries": len(isos),
        "outcomes": {k: {"label": v[0], "unit": v[1], "source": v[2]} for k, v in OUTCOMES.items()},
        "clusters": CLUSTERS,
        "subregions": SUBREGIONS,
        "stock_main": STOCK_MAIN,
        "kpis": [
            {"key": "main", "label": "One more policy on the books", "value": clean(fe["spec_A"]["coef"]),
             "unit": "pp of anaemia", "ci": [clean(v) for v in fe["spec_A"]["ci"]], "p": clean(fe["spec_A"]["p"]),
             "note": f"main model, {fe['spec_A']['n_obs']} country-years, {fe['spec_A']['n_countries']} countries",
             "reading": "The interval crosses zero: a null result, not a benefit."},
            {"key": "lead", "label": "Policies three years in the future", "value": clean(fe["lead_test"]["only"]["coef"]),
             "unit": "pp of anaemia", "ci": [clean(v) for v in fe["lead_test"]["only"]["ci"]], "p": clean(fe["lead_test"]["only"]["p"]),
             "note": f"lead test, {fe['lead_test']['only']['n']} country-years",
             "reading": "A future policy cannot cause a past outcome. Something else moves both."},
            {"key": "bounds", "label": "Effects we can rule out", "value": clean(fe["bounds"]["sesoi_pp_per_unit"]),
             "unit": "pp per policy or larger", "ci": None, "p": clean(fe["bounds"]["tost_p"]),
             "note": f"80% power to detect {fe['bounds']['mde80_pp_per_unit']:.2f} pp",
             "reading": "Precise enough to exclude a large effect, not to prove a zero one."},
            {"key": "loco", "label": "Countries where policy improves the forecast", "value": lo["countries_where_policy_helps"],
             "unit": f"of {lo['countries_total']}", "ci": None, "p": clean(lo["countries_where_policy_helps_binomial_p"]),
             "note": "leave-one-country-out prediction", "reading": "Indistinguishable from a coin toss."},
        ],
        "spec_summary": {
            "n": sp["n_specs"],
            "n_excludes_zero": int(round(sp["share_ci_excludes_zero"] * sp["n_specs"])),
            "n_negative_excludes_zero": int(round(sp["share_negative_and_excludes_zero"] * sp["n_specs"])),
            "n_positive_excludes_zero": int(round(sp["share_positive_and_excludes_zero"] * sp["n_specs"])),
            "median": clean(sp["median_pp_per_within_sd"]),
        },
        "context_model": {"r2": clean(rs["context_model"]["r2"]), "n": rs["context_model"]["n"], "countries": rs["context_model"]["countries"],
                          "formula": rs["context_model"]["formula"]},
        "income_model": {"r2": clean(rs["income_only"]["r2"]), "n": rs["income_only"]["n"], "note": "income plus year effects"},
        "concern": {"indicators": cs["indicators"], "draws": 500, "spearman_equal_vs_random": clean(cs["spearman_equal_vs_median_random_weights"])},
        "rules": [{"cluster": r.cluster, "pattern": r.pattern, "note": r.note} for r in rules.itertuples()],
        "cluster_coverage_2023": {
            c: {"countries_with_any": int((panel.loc[panel.year == YEAR_MAX, f"feat_gd_stock_{c}"] > 0).sum()),
                "mean_stock": clean(panel.loc[panel.year == YEAR_MAX, f"feat_gd_stock_{c}"].mean()),
                "max_stock": clean(panel.loc[panel.year == YEAR_MAX, f"feat_gd_stock_{c}"].max())}
            for c in CLUSTERS
        },
    }

    # ---------------- series: per country-year outcomes and per-cluster stocks ----------------
    series = {}
    for iso, g in panel.groupby("iso3"):
        g = g.set_index("year").reindex(years)
        series[iso] = {
            "out": {k: [clean(v) for v in g[k]] for k in OUTCOMES},
            "cl": {c: [clean(v) for v in g[f"feat_gd_stock_{c}"]] for c in CLUSTERS},
            "main": [clean(v) for v in g[STOCK_MAIN]],
        }

    # ---------------- countries: one record each ----------------
    def at(iso, col, year):
        r = panel[(panel.iso3 == iso) & (panel.year == year)]
        return float(r[col].iloc[0]) if len(r) and np.isfinite(r[col].iloc[0]) else np.nan

    countries = []
    for r in resid.itertuples():
        iso = r.iso3
        a15, a23 = at(iso, "out_anaemia_wra_fs_pct", RECENT_FROM), at(iso, "out_anaemia_wra_fs_pct", YEAR_MAX)
        s15, s23 = at(iso, STOCK_MAIN, RECENT_FROM), at(iso, STOCK_MAIN, YEAR_MAX)
        m1, m2 = float(loco.at[iso, "M1_income"]), float(loco.at[iso, "M2_income_policy"])
        countries.append({
            "iso3": iso, "country": r.country, "subregion": r.subregion,
            "m49": pycountry.countries.get(alpha_3=iso).numeric,
            "centroid": CENTROIDS.get(iso),
            "anaemia_2015": clean(a15), "anaemia_2023": clean(a23), "anaemia_change": clean(a23 - a15),
            "stock_2015": clean(s15), "stock_2023": clean(s23), "policies_added": clean(s23 - s15),
            "stock_mean_recent": clean(r.feat_gd_stock_anaemia_policies_mean_recent),
            "cluster_2023": {c: clean(at(iso, f"feat_gd_stock_{c}", YEAR_MAX)) for c in CLUSTERS},
            "resid_context": clean(r.resid_context_recent), "resid_income": clean(r.resid_income_recent),
            "country_effect_fe": clean(r.country_effect_fe),
            "rank_context": clean(r.rank_context), "rank_income": clean(r.rank_income), "rank_level": clean(r.rank_level_recent),
            "first_policy_year": clean(r.first_anaemia_policy_year),
            "mandate_year": clean(r.gfdx_wheat_mandate_year),
            "mandate_status": None if pd.isna(r.gfdx_wheat_mandate_status) else str(r.gfdx_wheat_mandate_status),
            "group": deviants.at[iso, "group"] if iso in deviants.index else None,
            "loco_m1": clean(m1), "loco_m2": clean(m2), "policy_helps": bool(m2 < m1),
            "concern": clean(concern.at[iso, "concern_equal_weights"]) if iso in concern.index else None,
            "concern_rank": clean(concern.at[iso, "rank_equal_weights"]) if iso in concern.index else None,
            "concern_stability": clean(concern.at[iso, "share_top10_random_weights"]) if iso in concern.index else None,
            "concern_parts": {k: clean(concern.at[iso, f"{k}_score"]) for k in cs["indicators"]} if iso in concern.index else None,
            "gdp_pc_2023": clean(r.gdp_pc_2023),
        })

    # ---------------- model: ladder, other doses, other outcomes, events, validation, contrast, spec ----------------
    def row(rec, block, label, unit="pp of anaemia per policy"):
        return {"key": getattr(rec, "variant", None) or getattr(rec, "spec", None), "block": block, "label": label, "unit": unit,
                "coef": clean(rec.coef), "lo": clean(rec.ci_low), "hi": clean(rec.ci_high), "p": clean(rec.p),
                "n": int(rec.n_obs), "countries": int(rec.n_countries), "years": str(getattr(rec, "years", "")),
                "p_bh": clean(getattr(rec, "p_bh", np.nan)), "p_wcb": clean(getattr(rec, "p_wcb", np.nan)),
                "note": None if pd.isna(getattr(rec, "note", np.nan)) else str(getattr(rec, "note"))}

    ladder = []
    seen = set()
    for rec in sens.itertuples():
        if rec.variant in LADDER and rec.term.startswith(("feat_gd_stock_anaemia_policies", "d1_feat", "d5_feat")) and rec.variant not in seen:
            seen.add(rec.variant)
            ladder.append(row(rec, *LADDER[rec.variant]))
    pol = coefs[coefs.term.str.startswith(("feat_gd_stock_anaemia_policies", "d1_feat", "d5_feat"))]
    for rec in pol.itertuples():
        if rec.spec in LADDER and rec.spec not in seen:
            seen.add(rec.spec)
            ladder.append(row(rec, *LADDER[rec.spec]))
    order = ["main", "lags", "guards", "lead", "trend", "bracket", "context", "sample"]
    ladder.sort(key=lambda d: (order.index(d["block"]), d["key"] != "A_main"))

    alt = [row(rec, "alt", ALT[rec.spec][0], ALT[rec.spec][1])
           for rec in coefs[coefs.spec.isin(ALT) & coefs.term.str.contains("feat_g")].itertuples()]
    other_out = [row(rec, "outcome", OUTCOMES[rec.outcome][0], f"{OUTCOMES[rec.outcome][1]} of {OUTCOMES[rec.outcome][0].lower()} per policy")
                 for rec in coefs[coefs.spec.str.startswith("outcome_") & coefs.term.str.startswith("feat_gd_stock")].itertuples()
                 if rec.outcome in OUTCOMES]
    for d in other_out:
        d["outcome"] = d["key"].replace("outcome_", "")
    # the main row also belongs in the other-outcome chart, as the reference
    main = next(d for d in ladder if d["key"] == "A_main")
    other_out.insert(0, {**main, "outcome": "out_anaemia_wra_fs_pct", "label": OUTCOMES["out_anaemia_wra_fs_pct"][0],
                         "unit": "% of anaemia, women 15–49 per policy"})

    events = {}
    for (e, est), g in ev.groupby(["event", "estimator"]):
        base = est.replace("_event", "")
        events.setdefault(e, {})[base] = [{"k": int(r.k), "coef": clean(r.coef), "lo": clean(r.ci_low), "hi": clean(r.ci_high), "p": clean(r.p)}
                                          for r in g.sort_values("k").itertuples()]
    atts = {}
    for r in att.itertuples():
        atts.setdefault(r.event, {})[r.estimator.replace("_static", "").replace("_att", "")] = {
            "att": clean(r.att), "lo": clean(r.ci_low), "hi": clean(r.ci_high), "p": clean(r.p), "n": int(r.n_obs)}

    model = {
        "ladder": ladder,
        "alt": alt,
        "other_outcomes": other_out,
        "blocks": {"main": "Main model", "lags": "Other lags", "guards": "Sample and income guards", "lead": "Lead test (policies in the future)",
                   "trend": "Country-specific trends", "bracket": "Difference and lagged-outcome brackets",
                   "context": "One extra control at a time", "sample": "Subsamples with an extra control"},
        "events": events, "att": atts, "event_labels": EVENTS, "estimator_labels": ESTIMATORS,
        "loco_rmse": [{"model": r.model, "rmse": clean(r.rmse), "mae": clean(r.mae), "r2": clean(r.r2_dev)} for r in loco_rmse.itertuples()],
        "loco_labels": {"naive_flat": "Flat line", "M0_year_effects": "Year effects only", "M1_income": "Income", "M2_income_policy": "Income + policy",
                        "M2t_income_team_composite": "Income + team composite", "M3_income_all_exposures": "Income + every exposure"},
        "contrast": [{"ranking": r.ranking, "composite": r.composite, "positive": clean(r.positive_deviant_mean), "under": clean(r.under_performer_mean),
                      "p": clean(r.mannwhitney_p)} for r in contrast.itertuples()],
        "spec": [{"c": clean(r.coef_per_within_sd), "lo": clean(r.ci_low), "hi": clean(r.ci_high), "z": bool(r.excludes_zero), "p": clean(r.p),
                  "e": r.exposure, "lag": int(r.lag), "inc": r.income, "ctl": r.controls, "est": r.estimator, "n": int(r.n_obs)}
                 for r in spec.sort_values("coef_per_within_sd").itertuples()],
        "spec_dims": {"exposure": sorted(spec.exposure.unique()), "lag": sorted(spec.lag.unique().tolist()), "income": sorted(spec.income.unique()),
                      "controls": sorted(spec.controls.unique()), "estimator": sorted(spec.estimator.unique())},
        "spec_labels": {"fe": "Fixed effects", "fe_trend": "FE + country trends", "fd": "First differences", "ldv": "Lagged outcome",
                        "constant": "Income in constant US$", "current": "Income in current US$", "context": "With context controls", "none": "No context controls",
                        **{k: v[0] for k, v in ALT.items()}, "feat_gd_stock_anaemia_policies": "Anaemia policies (main dose)",
                        "feat_gd_logstock_anaemia_policies": "log(1 + policies)", "feat_gd_stock_anaemia": "Anaemia records, all files",
                        "feat_gd_logstock_anaemia": "log(1 + records, all files)", "feat_gd_any_anaemia_policies": "Any anaemia policy ever",
                        "feat_gd_any_fortification": "Any fortification ever", "feat_gifna_anemia_programming_intensity": "Team composite"},
    }

    for name, payload in (("meta.json", meta), ("countries.json", countries), ("series.json", {"years": years, "by_iso": series}), ("model.json", model)):
        (out / name).write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
        print(f"{name:16s} {(out / name).stat().st_size / 1024:7.1f} KB")
    print(f"\n{len(countries)} countries · ladder {len(ladder)} rows · alt {len(alt)} · other outcomes {len(other_out)} · spec {len(model['spec'])} · rules {len(meta['rules'])}")
    print("context residual for", sum(c["resid_context"] is not None for c in countries), "countries; islands drawn as dots:", [c["iso3"] for c in countries if c["centroid"]])


if __name__ == "__main__":
    main()
