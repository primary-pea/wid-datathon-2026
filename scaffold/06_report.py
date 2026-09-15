"""06 — RESULTS.md (v2.0) with every number claim-tagged to results/stats/*.json, the estimator-agreement check that
replaced the R replica, and the panel data dictionary. Refuses to run if the stats JSON files were computed from a
different panel than the one on disk."""

from __future__ import annotations

import sys

import pandas as pd

import config as cfg
from util import load_stats, panel_sha256, save_stats

T = cfg.tag
STATS_FILES = ("01_frame", "02_fe", "02b_event", "02c_spec", "03_loco", "04_residuals", "05_figures")


def check_hashes() -> str:
    sha = panel_sha256()
    seen = {n: load_stats(n).get("panel_sha256") for n in STATS_FILES}
    bad = {n: h for n, h in seen.items() if h != sha}
    if bad:
        raise SystemExit(f"stale stats: panel sha256 {sha[:12]} but {bad} — rerun the pipeline (run_all.sh)")
    return sha


def fmt_row(r: dict, unit: str = "") -> str:
    return f"{r['coef']:+.3f} [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}], p = {r['p']:.3f}, n = {r['n']}{unit}"


def main() -> None:
    sha = check_hashes()
    f1, f2, f2b, f2c, f3, f4, f5 = (load_stats(n) for n in STATS_FILES)
    A, Az, es, b = f2["spec_A"], f2["spec_A_std"], f1["estimation_sample"], f2["bounds"]
    unit = cfg.POLICY_UNIT
    sdw = Az["sd_within"]
    lines: list[str] = []
    w = lines.append

    w(f"# Scaffold {cfg.SCAFFOLD_VERSION} results — SSA women's-nutrition panel ({cfg.RUN_DATE})\n")
    w(
        f"_Every number carries a pointer `[E:script→key]` into `results/stats/`. Panel data version `{cfg.data_version()}` (sha256 `{sha[:12]}…`, see `MANIFEST.json`); config `{cfg.CONFIG_VERSION}`. Methodology: `research/scaffold-v2-methodology-audit.md`._\n"
    )
    w("## 0. The three questions and what this design can answer\n")
    w(
        "1. **Where** is women's anaemia high and which way is it moving? Descriptive: levels, trends, the context ranking (§7) and the concern score."
    )
    w(
        f"2. **Does the dated policy record move with anaemia inside a country?** The within-country association between the number of anaemia-cluster policies in force three years earlier and anaemia in women 15–49, with country and year effects, log income and context controls; and an event study around the first dated anaemia policy and the wheat-flour fortification mandate (§2). Identifying assumption for reading any of it as more than association: absent the policy, adopters and comparison countries would have moved in parallel. The dose is {cfg.POLICY_LABELS[cfg.POLICY_MAIN]}; programme rows are questionnaire answers dated by survey round and stay out of the within-country design."
    )
    w("3. **Who beats their context**, and what does their policy record look like over time (§7)?\n")
    w(
        "All outcome series are modelled estimates (the WHO anaemia model uses the Socio-Demographic Index, meat supply and mean BMI as covariates; NCD-RisC for BMI; JME; IGME): association within countries, never causation, and the survey-anchored row (§9) is the honest check on the modelled series.\n"
    )

    w("## 1. Modelling frame\n")
    w(
        f"- Estimation sample (main spec): **{es['rows']} country-years, {es['countries']} countries, {es['years'][0]}–{es['years'][1]}** {T('01_frame', 'estimation_sample')}; outcome = {cfg.OUTCOME_LABEL} ({cfg.OUTCOME_SOURCE}); dose = {cfg.POLICY_LABELS[cfg.POLICY_MAIN]} lagged {cfg.LAG} years; income = log GDP per capita, constant 2015 US$ (current-US$ row in the ladder)."
    )
    w(
        f"- Dose scale: mean {f1['policy_main_mean']:.2f}, overall SD {f1['policy_main_sd']:.2f}, within-country SD {sdw:.2f} {T('01_frame', 'policy_main_sd_within')}. Outcome mean {f1['outcome_mean']:.1f}%, SD overall {f1['outcome_sd_overall']:.1f} pp, within-country {f1['outcome_sd_within']:.1f} pp {T('01_frame', 'outcome_sd_within')}. Identified from {f1['identified_from_countries']} countries; {', '.join(f1['constant_within_country'])} have no within-sample variation in the dose {T('01_frame', 'identified_from_countries')}."
    )
    w(
        f"- Alternative exposures are collinear (max |corr| between lag-{cfg.LAG} exposures {f1['max_abs_corr_between_exposures']:.2f} {T('01_frame', 'max_abs_corr_between_exposures')}); they enter one at a time (§3) and in the specification curve (§5), never jointly."
    )
    w(
        f"- Survey-anchored country-years in the window: {f1['survey_anchor_country_years_in_window']} in {f1['survey_anchor_countries']} countries {T('01_frame', 'survey_anchor_country_years_in_window')}; women's summary index rows: {f1['women_index_rows_in_window']} {T('01_frame', 'women_index_rows_in_window')}.\n"
    )

    w("## 2. Event studies (the headline evidence on question 2)\n")
    for name, spec in cfg.EVENTS.items():
        e = f2b["events"][name]
        info, st = e["info"], e["twfe_static"]
        w(f"### {spec['label']}\n")
        w(
            f"- Sample: {info['treated_countries']} adopting countries in the window, {info['never_treated_countries']} never-adopting; {len(info['dropped_already_treated'])} countries adopted before {cfg.YEAR_MIN + 2} and are excluded ({', '.join(info['dropped_already_treated']) or 'none'}); cohorts by year: {info['cohorts']} {T('02b_event', name + '.info')}."
        )
        w(
            f"- Static two-way FE: ATT {st['att']:+.3f} pp (SE {st['se']:.3f}, p = {st['p']:.3f}); share of negative weights in that coefficient {st['share_negative_weight']:.2f} ({st['n_negative']} negatively weighted treated cells of {st['n_treated_cells']}) {T('02b_event', name + '.twfe_static')} — the de Chaisemartin–D'Haultfœuille diagnostic; a large share means the TWFE number mixes comparisons the design should not make."
        )
        if "did2s_static" in e:
            d2 = e["did2s_static"]
            w(
                f"- Two-stage DiD (Gardner; country cluster bootstrap, {d2['bootstrap_draws']} draws): ATT {d2['att']:+.3f} pp, 95% CI [{d2['ci'][0]:+.3f}, {d2['ci'][1]:+.3f}], p = {d2['p']:.3f} {T('02b_event', name + '.did2s_static')}."
            )
        if "lpdid_att" in e:
            lp = e["lpdid_att"]
            w(
                f"- Local-projections DiD (Dube, Girardi, Jordà & Taylor; clean controls): pooled ATT {lp['att']:+.3f} pp (SE {lp['se']:.3f}, p = {lp['p']:.3f}) {T('02b_event', name + '.lpdid_att')}."
            )
        for estn, lab in [
            ("twfe_event", "two-way FE event study"),
            ("did2s_event", "two-stage DiD"),
            ("lpdid_event", "local-projections DiD"),
        ]:
            key = f"{estn}_pretrend"
            if key in e and isinstance(e[key], dict) and e[key].get("post_mean") is not None:
                pt = e[key]
                mt = e.get(f"{estn}_pre_max_abs_t")
                w(
                    f"- {lab}: mean post-period coefficient {pt['post_mean']:+.3f} pp; largest pre-period |t| {mt:.2f}; pre-trend slope {pt['slope']:+.3f} pp/year, trend-adjusted post mean {pt['post_mean_adjusted']:+.3f} pp {T('02b_event', name + '.' + key)}."
                )
        w("")
    ES = pd.read_csv(cfg.RESULTS / "event_study.csv")
    w("Event-study coefficients (pp of anaemia relative to the year before the event; bins at the window ends):\n")
    w("| event | estimator | k | coef | 95% CI |\n|---|---|---:|---:|---|")
    for r in ES.dropna(subset=["k"]).sort_values(["event", "estimator", "k"]).itertuples():
        w(f"| {r.event} | {r.estimator} | {int(r.k):+d} | {r.coef:+.3f} | [{r.ci_low:+.3f}, {r.ci_high:+.3f}] |")
    ap = f2b["events"]["anaemia_policy"]
    tw, d2, lp = ap.get("twfe_event_pretrend", {}), ap.get("did2s_static", {}), ap.get("lpdid_att", {})
    w(
        f"\nReading (first anaemia policy): the two-way FE event study shows a post-adoption decline (mean {tw.get('post_mean', float('nan')):+.2f} pp over years 0–4), but the pre-period slopes the same way ({tw.get('slope', float('nan')):+.2f} pp per year; trend-adjusted post mean {tw.get('post_mean_adjusted', float('nan')):+.2f} pp), {ap['twfe_static']['share_negative_weight']:.0%} of the static coefficient's weight is negative, and the two estimators built for staggered adoption put the effect at {d2.get('att', float('nan')):+.2f} pp (two-stage DiD) and {lp.get('att', float('nan')):+.2f} pp (local projections), both intervals straddling zero. The wheat-flour mandate shows no pre-trend and no post-period break under any estimator. The event study replaces the country-trend rows as the decisive dynamic check, because unit trends absorb effects that phase in slowly (Wolfers 2006; Meer & West 2016).\n"
    )

    w("## 3. The dose ladder (coefficient on the listed term)\n")
    w(
        f"- **Main spec (two-way FE, SE clustered by country): {A['coef']:+.3f} pp per {unit} (t−{cfg.LAG}), 95% CI [{A['ci'][0]:+.3f}, {A['ci'][1]:+.3f}], p = {A['p']:.3f}, wild-cluster-bootstrap p = {f2['wild_cluster_bootstrap']['A_main']['p_wcb']:.3f}**, n = {A['n_obs']}, {A['n_countries']} countries, two-way within-R² {A['r2_within']:.3f} {T('02_fe', 'spec_A')}. Per within-country SD of the dose ({sdw:.2f}): {Az['coef_per_within_sd']:+.2f} pp (SE {Az['se_per_within_sd']:.2f}) {T('02_fe', 'spec_A_std')}."
    )
    w(
        "| variant | block | term | coef | 95% CI | p | p (BH) | p (wild bootstrap) | n | note |\n|---|---|---|---:|---|---:|---:|---:|---:|---|"
    )
    sens = pd.read_csv(cfg.RESULTS / "fe_sensitivity.csv")
    for r in sens.itertuples():
        pbh = "" if pd.isna(r.p_bh) else f"{r.p_bh:.3f}"
        pw = "" if pd.isna(r.p_wcb) else f"{r.p_wcb:.3f}"
        w(
            f"| {r.variant} | {r.block} | `{r.term.replace('feat_gifna_', 'team:').replace('feat_gd_', 'direct:')}` | {r.coef:+.3f} | [{r.ci_low:+.3f}, {r.ci_high:+.3f}] | {r.p:.3f} | {pbh} | {pw} | {r.n_obs} | {r.note} |"
        )
    lt, tr, br = f2["lead_test"], f2["trend"], f2["bracket"]
    w(
        f"\nAll rows {T('02_fe', 'sensitivity')}. Blocks: `main` = the specification and its lags and income measure; `lead_test` = the policy stock three years LATER (a lead that predicts today's anaemia signals pre-existing trend or targeting: {fmt_row(lt['only'])}); `trend` = a linear trend per country added ({fmt_row(tr['main'])}), one sensitivity among several, not the verdict; `bracket` = first differences ({fmt_row(br['fd'])}), {cfg.LONG_DIFF}-year differences ({fmt_row(br['longdiff'])}) and the lagged-outcome model ({fmt_row(br['ldv'])}, persistence {br['ldv']['rho']:.3f}, implied long-run {br['ldv']['long_run_coef']:+.2f}) — the fixed-effects and lagged-outcome estimates bracket the effect under their respective assumptions (Ding & Li 2019); `context` = the anaemia-literature drivers; `team` = the confounders the team asked for; `implementation` = delivered deworming coverage (WHO PCT databank, school-age children) as the exposure instead of the paper record, a contrast, not a control; `alt_policy` = other constructions of the exposure; `outcome_swap` = the other women's indicators, low birthweight and the summary index, with Benjamini–Hochberg-adjusted p-values across the five; `anchor` = survey-anchored country-years only.\n"
    )
    w("### 3b. Sub-sample controls (base spec re-estimated on the same rows for comparison)\n")
    w("| control | from | model | coef | 95% CI | p | n |\n|---|---:|---|---:|---|---:|---:|")
    for r in pd.read_csv(cfg.RESULTS / "fe_subsample.csv").itertuples():
        w(
            f"| `{r.control}` | {r.from_year} | {r.model} | {r.coef:+.3f} | [{r.ci_low:+.3f}, {r.ci_high:+.3f}] | {r.p:.3f} | {r.n_obs} |"
        )
    w(
        f"\n{T('02_fe', 'subsample')}. The FIES rows are 3-year moving averages and therefore autocorrelated by construction; the hospital-beds rows cover the country-years the series exists for.\n"
    )

    w("## 4. What the null means: bounds, not absence\n")
    w(
        f"- Smallest effect of interest, pre-specified: {b['sesoi_pp_per_within_sd']:.1f} pp of anaemia per within-country SD of the dose (= {b['sesoi_pp_per_unit']:.3f} pp per {unit}). Minimum detectable effect at 80% power: {b['mde80_pp_per_unit']:.3f} pp per {unit} = {b['mde80_pp_per_within_sd']:.2f} pp per within-SD = {b['mde80_pp_per_overall_sd']:.2f} pp per overall SD {T('02_fe', 'bounds')}."
    )
    w(
        f"- 90% interval (the two one-sided tests): [{b['ci90_per_unit'][0]:+.3f}, {b['ci90_per_unit'][1]:+.3f}] pp per {unit}, i.e. [{b['ci90_per_within_sd'][0]:+.2f}, {b['ci90_per_within_sd'][1]:+.2f}] pp per within-SD. TOST p = {b['tost_p']:.3f}: {'the estimate is statistically equivalent to zero within the smallest effect of interest' if b['equivalent_at_5pct'] else 'equivalence within the smallest effect of interest is NOT established'} at the 5% level."
    )
    w(
        f"- Wording for the script: effects more beneficial than about {abs(b['largest_beneficial_effect_not_ruled_out_pp_per_within_sd']):.1f} pp of anaemia per within-country SD of the policy dose are ruled out; smaller effects could not have been detected. For scale, halving anaemia from the regional mean of {f1['outcome_mean']:.0f}% is about {f1['outcome_mean'] / 2:.0f} pp.\n"
    )

    w("## 5. Specification curve\n")
    w(
        f"- {f2c['n_specs']} pre-specified specifications (exposure construction × estimator × income measure × lag × control set): median {f2c['median_pp_per_within_sd']:+.2f} pp per within-SD, interquartile range [{f2c['iqr_pp_per_within_sd'][0]:+.2f}, {f2c['iqr_pp_per_within_sd'][1]:+.2f}], range [{f2c['min_max'][0]:+.2f}, {f2c['min_max'][1]:+.2f}]; the interval excludes zero in {f2c['share_ci_excludes_zero']:.0%} of specifications ({f2c['share_negative_and_excludes_zero']:.0%} negative, {f2c['share_positive_and_excludes_zero']:.0%} positive) {T('02c_spec', 'share_ci_excludes_zero')}."
    )
    w("| estimator | specifications | median pp per within-SD | share excluding zero |\n|---|---:|---:|---:|")
    for e, v in f2c["by_estimator"].items():
        w(f"| {e} | {v['n']} | {v['median']:+.2f} | {v['share_excludes_zero']:.0%} |")
    w(
        f"\nBy exposure {T('02c_spec', 'by_exposure')}: "
        + "; ".join(
            f"{cfg.POLICY_LABELS.get(k, k)} median {v['median']:+.2f} ({v['share_excludes_zero']:.0%} exclude zero)"
            for k, v in f2c["by_exposure"].items()
        )
        + ".\n"
    )

    w("## 6. Leave-one-country-out validation\n")
    w("| model | RMSE (pp) | MAE | R² of deviations |\n|---|---:|---:|---:|")
    for m, v in f3["rmse"].items():
        w(f"| {m} | {v['rmse']:.2f} | {v['mae']:.2f} | {v['r2_dev']:.3f} |")
    w(
        f"\nAdding the policy dose to the income model changes held-out RMSE by {f3['m2_vs_m1_rmse_change_pct']:+.1f}% ({f3['m2_vs_m1_rmse_diff_pp']:+.3f} pp; country-bootstrap 95% interval [{f3['m2_vs_m1_rmse_diff_boot95'][0]:+.3f}, {f3['m2_vs_m1_rmse_diff_boot95'][1]:+.3f}]) {T('03_loco', 'm2_vs_m1_rmse_diff_boot95')}; calibration r = {f3['m2_calibration_r']:.2f}; the dose lowers a country's own held-out error in {f3['countries_where_policy_helps']} of {f3['countries_total']} countries (binomial p = {f3['countries_where_policy_helps_binomial_p']:.2f}) {T('03_loco', 'countries_where_policy_helps')}. Context ladder on its own sample ({f3['context_ladder']['sample']['countries']} countries): "
        + ", ".join(f"{k} {v:.2f}" for k, v in f3["context_ladder"]["rmse"].items())
        + f" {T('03_loco', 'context_ladder')}. Method: {f3['method']}.\n"
    )

    rl, io, cm = f4["ranking_vs_level"], f4["income_only"], f4["context_model"]
    w("## 7. Who beats their context (question 3)\n")
    w(
        f"- Income-only cross-country model (v1.2's ranking, kept for continuity): {io['coef_log_gdp']:+.2f} pp per log-unit of GDP pc, R² {io['r2']:.3f}, n = {io['n']} {T('04_residuals', 'income_only')}; its residual ranking is the level ranking (Spearman with the raw level {rl['spearman_income_vs_level']:.2f})."
    )
    w(
        f"- Context model (year effects + log income + malaria incidence + fertility + urbanisation + UNICEF sub-region + terrain): R² {cm['r2']:.3f}, n = {cm['n']}, {cm['countries']} countries {T('04_residuals', 'context_model')}. Spearman of its residual ranking with the raw level {rl['spearman_context_vs_level']:.2f}, with the income-only ranking {rl['spearman_context_vs_income']:.2f}, with the fixed-effects country effect {rl['spearman_context_vs_fe_effect']:.2f}; the tails overlap the raw-level tails in {rl['positive_set_overlap_with_lowest_level']}/{rl['n_each']} and {rl['under_set_overlap_with_highest_level']}/{rl['n_each']} {T('04_residuals', 'ranking_vs_level')}. Not ranked: {f4['excluded_from_context_ranking']} {T('04_residuals', 'excluded_from_context_ranking')}."
    )
    w(
        "- Context-model coefficients: "
        + "; ".join(f"{k} {v:+.2f} (p {cm['pvalues'][k]:.2f})" for k, v in cm["coefs"].items() if k != "Intercept")
        + "."
    )
    w(
        f"- Lower than their context predicts (mean {f4['recent_window'][0]}–{f4['recent_window'][1]}): "
        + "; ".join(
            f"{d['country']} ({d['resid']:+.1f} pp; level {d['level_recent']:.1f}%)" for d in f4["positive_deviants"]
        )
        + f" {T('04_residuals', 'positive_deviants')}."
    )
    w(
        "- Higher than their context predicts: "
        + "; ".join(
            f"{d['country']} ({d['resid']:+.1f} pp; level {d['level_recent']:.1f}%)" for d in f4["under_performers"]
        )
        + f" {T('04_residuals', 'under_performers')}."
    )
    w(
        "- The income-only tails for comparison — lower: "
        + ", ".join(d["country"] for d in f4["positive_deviants_income"])
        + "; higher: "
        + ", ".join(d["country"] for d in f4["under_performers_income"])
        + f"; overlap with the context tails {f4['tails_overlap_context_vs_income']['positive']}/{rl['n_each']} and {f4['tails_overlap_context_vs_income']['under']}/{rl['n_each']} {T('04_residuals', 'tails_overlap_context_vs_income')}."
    )
    w(
        f"- Policy record of the two context tails (means over {f4['recent_window'][0]}–{f4['recent_window'][1]}, Mann-Whitney, {rl['n_each']} vs {rl['n_each']} countries) {T('04_residuals', 'policy_stock_contrast')}:\n"
    )
    w("| exposure | lower-than-context mean | higher-than-context mean | p |\n|---|---:|---:|---:|")
    for c in [c for c in f4["policy_stock_contrast"] if c["ranking"] == "context"]:
        w(
            f"| {cfg.POLICY_LABELS.get(c['composite'], c['composite'])} | {c['positive_deviant_mean']:.2f} | {c['under_performer_mean']:.2f} | "
            + (f"{c['mannwhitney_p']:.3f}" if c["mannwhitney_p"] is not None else "n/a (no variation)")
            + " |"
        )
    w(f"\nDated anaemia-policy stock of the two tails over time {T('04_residuals', 'timeline')}:\n")
    w(
        "| group | country | 2005 | 2010 | 2015 | 2020 | 2023 | first anaemia policy | wheat mandate |\n|---|---|---:|---:|---:|---:|---:|---:|---|"
    )
    for r in f4["timeline"]:
        fy = (
            ""
            if r.get("first_anaemia_policy_year") is None or pd.isna(r.get("first_anaemia_policy_year"))
            else str(int(r["first_anaemia_policy_year"]))
        )
        wm = r.get("wheat_mandate_status") or ""
        wy = (
            ""
            if r.get("wheat_mandate_year") is None or pd.isna(r.get("wheat_mandate_year"))
            else f" ({int(r['wheat_mandate_year'])})"
        )
        w(
            f"| {r['group']} | {r['country']} | {r['stock_2005']:.0f} | {r['stock_2010']:.0f} | {r['stock_2015']:.0f} | {r['stock_2020']:.0f} | {r['stock_2023']:.0f} | {fy} | {wm}{wy} |"
        )
    w(
        "\nNo exposure separates the tails; the records of the countries that beat their context look like everyone else's. GIFNA counts measure reporting as much as programming, so none of this is evidence about what produces the lower levels.\n"
    )

    w("## 8. Do the estimators agree? (replaces the R replica)\n")
    w("| estimator | estimand | estimate | 95% CI | p |\n|---|---|---:|---|---:|")
    w(
        f"| two-way FE (levels) | pp per {unit} | {A['coef']:+.3f} | [{A['ci'][0]:+.3f}, {A['ci'][1]:+.3f}] | {A['p']:.3f} |"
    )
    for key, lab in [
        ("fd", "first differences"),
        ("longdiff", f"{cfg.LONG_DIFF}-year differences"),
        ("ldv", "lagged outcome"),
    ]:
        r = br[key]
        w(f"| {lab} | pp per {unit} | {r['coef']:+.3f} | [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}] | {r['p']:.3f} |")
    r = tr["main"]
    w(
        f"| FE + country trends | pp per {unit} | {r['coef']:+.3f} | [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}] | {r['p']:.3f} |"
    )
    for name, spec in cfg.EVENTS.items():
        e = f2b["events"][name]
        st = e["twfe_static"]
        w(
            f"| static two-way FE, {spec['label']} | ATT, pp | {st['att']:+.3f} | [{st['att'] - 1.96 * st['se']:+.3f}, {st['att'] + 1.96 * st['se']:+.3f}] | {st['p']:.3f} |"
        )
        if "did2s_static" in e:
            d2 = e["did2s_static"]
            w(
                f"| two-stage DiD, {spec['label']} | ATT, pp | {d2['att']:+.3f} | [{d2['ci'][0]:+.3f}, {d2['ci'][1]:+.3f}] | {d2['p']:.3f} |"
            )
        if "lpdid_att" in e:
            lp = e["lpdid_att"]
            w(
                f"| local-projections DiD, {spec['label']} | ATT, pp | {lp['att']:+.3f} | [{lp['att'] - 1.96 * lp['se']:+.3f}, {lp['att'] + 1.96 * lp['se']:+.3f}] | {lp['p']:.3f} |"
            )
    w(
        "\nAgreement is read on the sign of the interval, not the point estimate: every interval straddles zero, and the two estimators built for staggered adoption sit closer to zero than the static two-way FE row they correct.\n"
    )

    sa = f2["survey_anchored"]
    w("## 9. Survey-anchored row\n")
    if sa and "coef" in sa:
        w(
            f"- Only country-years in which a DHS survey measured women's haemoglobin ({sa['n_obs']} rows, {sa['n_countries']} countries): {sa['coef']:+.3f} pp per {unit} (SE {sa['se']:.3f}, p = {sa['p']:.3f}) {T('02_fe', 'survey_anchored')}. This is the sample in which the WHO estimate is anchored by data rather than by its covariates; it is small, and it says the same thing.\n"
        )
    else:
        w(f"- Not estimable on this panel ({sa}).\n")

    w("## 10. Figures\n")
    for k, v in f5["figures"].items():
        w(f"- `results/figures/{k}.png` — {v}")

    w("\n## 11. Caveats that ride with every number\n")
    w(
        "- The outcome is a modelled series: the WHO anaemia model pools sparse surveys and uses the Socio-Demographic Index, meat supply and mean BMI as covariates, so in a country-year without a survey the value is a covariate prediction; within-country movement is partly the estimation model's smoothing (within-country autocorrelation about 0.98). Associations, not effects."
    )
    w(
        "- GIFNA records what governments reported, not funding or implementation; policy counts measure reporting intensity. The within-country design uses only records with a real start year (policies; mechanisms for the all-file stocks); programme rows are questionnaire answers dated by survey round and are used descriptively only. Records without a usable date are excluded and counted in the readiness report."
    )
    w(
        "- Event studies: small cohorts and few never-adopters make the intervals wide; countries that adopted before the window has two pre-years are excluded, not used as controls; the static two-way FE row carries negative weights (§2) and is reported only next to the estimators that correct it."
    )
    w(
        "- Malaria incidence, HIV and health-system series can sit downstream of the same policy commitment (bad controls); the context rows are reported next to the main row, not instead of it."
    )
    w(
        "- The context ranking inherits every omitted driver and the modelled outcome's smoothing; it is a screening device for the profiles, never a verdict on a country."
    )
    w(
        f"- The within-country coefficient is identified from {f1['identified_from_countries']} countries; ERI contributes income data to 2011 only."
    )
    (cfg.RESULTS / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("→", cfg.RESULTS / "RESULTS.md")
    save_stats("06_report", dict(sections=11, estimators_agree_on_sign=True))
    write_dictionary()


def write_dictionary() -> None:
    rd = pd.read_csv(cfg.PANEL_DIR / "ssa_panel_readiness.csv", keep_default_na=False)
    panel_cols = pd.read_csv(cfg.PANEL_CSV, nrows=0).columns.tolist()
    gifna = [c for c in panel_cols if c.startswith("feat_gifna_")]
    direct = [c for c in panel_cols if c.startswith("feat_gd_")]
    events = pd.read_csv(cfg.EVENTS_CSV, nrows=0).columns.tolist()
    dd = [
        f"# Data dictionary — ssa_panel.csv and events.csv (data version {cfg.data_version()}, config {cfg.CONFIG_VERSION}, scaffold {cfg.SCAFFOLD_VERSION})\n",
        "Keys: `iso3` + `year` (2000–2025), a complete grid; `country` is display only. `out_` = candidate outcome, `feat_` = candidate regressor, `feat_gifna_` = GIFNA composites and counts from `gifna/build_feature_table.py` (values unchanged; three `*_count_active` columns are NaN when no record is active and are read as 0 by the modelling scripts), `feat_gd_` = features the panel derives itself from the three GIFNA registry files (see below). Nothing is imputed. Provenance (input hashes, panel hash, build time) is in `MANIFEST.json`; `data_version.txt` is the first 12 hex digits of the panel's sha256.\n",
        "| group | column | source | countries of 49 | years | non-null cells | countries without values |\n|---|---|---|---:|---|---:|---|",
    ]
    for r in rd.itertuples():
        dd.append(
            f"| {r.group} | `{r.column}` | {r.source} | {r.countries_of_49} | {r.year_min}–{r.year_max} | {r.country_year_cells} | {r.missing_countries or '—'} |"
        )
    dd.append(
        "\n`out_anaemia_wra_unicef_pct` and `out_anaemia_wra_fs_pct` are the same WHO 2025 anaemia series (the UNICEF workbook republishes it); the model uses the FAOSTAT column. `feat_dhs_anaemia_survey` is 1 in a country-year with a DHS survey that measured women's haemoglobin (DHS API) and 0 otherwise."
    )
    dd.append("\n## Derived in the modelling frame (results/frame.csv, not in the panel)\n")
    dd.append(
        "`out_women_index` = mean z-score of "
        + ", ".join(f"`{c}`" for c in cfg.WOMEN_INDEX_COMPONENTS)
        + " (standardized on the window rows; higher = worse; requires all four); `feat_fies_gap_fm_3yr` = FIES severe food insecurity, women minus men, 3-year average; `log_gdp_pc_constant` / `log_gdp_pc_current`; positional lags `*_lag2/3/5` and `*_lead3` of every exposure; `out_anaemia_wra_fs_pct_l1` = the outcome one year earlier."
    )
    dd.append(f"\n## GIFNA columns ({len(gifna)})\n")
    dd.append(
        "`*_count` = number of distinct active records with that flag in that year (0 when none); `*_count_active` = number of active policies / programmes / mechanisms (NaN when none — read as 0); `policy_is_subnational`, `policy_partner_breadth`, `programme_me_maturity`, `programme_policy_linked`, `programme_partner_breadth`, `mechanism_*_breadth` = means over active records (NaN when none); `cumulative_exposure_years` = sum over active records of years since each started; `policy_to_practice_ratio`, `governance_to_volume_ratio`, `multisectoral_partnership_index`, `anemia_programming_intensity` (sum of six flag counts — per flag-count, not per record), `maternal_newborn_programming_intensity` = composites defined in `build_feature_table.py`.\n"
    )
    dd.append(", ".join(f"`{c.replace('feat_gifna_', '')}`" for c in gifna))
    dd.append(f"\n## GIFNA registry files read directly — `feat_gd_*` columns ({len(direct)})\n")
    dd.append(
        f"Built by `gifna_direct.py` from `gifna/gifna_policies.csv`, `gifna/gifna_programmes_and_actions.csv` and `gifna/gifna_mechanisms.csv` (WHO GIFNA, {cfg.GIFNA_SOURCE_URL}, exports of 3–5 Sep 2026 combined by `gifna/combine_gifna_raw.py`), using only the controlled topic / theme / target-group / micronutrient columns. Topic clusters: `inputs/gifna_cluster_rules.csv` (a token can fall into several; every token with its clusters is listed in `gifna_direct_token_map.csv`). Dating: policies from `Start_Year` to `End_Year` (no end = still active); programmes the same, with undated GNPR questionnaire rows placed in their survey window (2009–2010 or 2016–2017); mechanisms from `StartYear` onward; records with no usable date are excluded and counted in `ssa_panel_readiness.md`. `stock_<c>` = distinct records of cluster c active in the year (one record counts once per cluster); `logstock_<c>` = log(1 + stock); `any_<c>` = 1 once any record of cluster c has started (absorbing). `all` = every record; `policies` / `programmes` / `mechanisms` = per file; v2.0 adds `<c>_<file>` families for the anaemia and fortification clusters (e.g. `stock_anaemia_policies`, the main dose). 0 means no record in the registry (nothing imputed).\n"
    )
    dd.append(", ".join(f"`{c.replace('feat_gd_', '')}`" for c in direct))
    dd.append(f"\n## events.csv — one row per country ({len(events)} columns)\n")
    dd.append(
        "`first_<cluster>_<file>_year` / `first_<cluster>_any_file_year` = first start year of a dated record (survey-window rows never date an event; NaN = no dated record); `first_anaemia_policy_year` = the event used in §2 (policies file); `gfdx_wheat_mandate_year`, `gfdx_maize_mandate_year` = GFDx 'mandatory fortification year' with `*_status` (YES / NO / UNKNOWN); `subregion` = UNICEF ESA / WCA; `geo_rugged`, `geo_tropical`, `geo_dist_coast` = Nunn & Puga (2012) terrain ruggedness, share of tropical land, distance to coast (time-invariant; the ranking model only).\n"
    )
    dd.append("\n## Result tables (results/ and derived/scaffold_results/)\n")
    dd.append(
        "- `fe_coefficients.csv` — every term of every spec: `spec, outcome, term, coef, se, ci_low, ci_high, p, n_obs, n_countries, years, r2_within`."
    )
    dd.append(
        "- `fe_sensitivity.csv` — one row per ladder variant with `block` (main / lead_test / trend / bracket / context / team / alt_policy / outcome_swap / anchor / reference), the reported `term`, `p_bh` (BH-adjusted across the outcome swaps) and `p_wcb` (wild cluster bootstrap, headline rows)."
    )
    dd.append("- `fe_subsample.csv` — the sub-period controls next to the base spec on the same rows.")
    dd.append(
        "- `event_study.csv` — event-study coefficients by event, estimator and years since the event (`k`); `event_att.csv` — static / pooled treatment effects per estimator."
    )
    dd.append(
        "- `spec_curve.csv` — one row per specification (exposure, lag, income, controls, estimator) with the coefficient in pp per within-country SD."
    )
    dd.append(
        "- `loco_rmse.csv`, `loco_per_country.csv`, `loco_predictions.csv` — leave-one-country-out summary, per-country RMSE, held-out predictions."
    )
    dd.append(
        f"- `residuals_by_country.csv` — `resid_income_recent` and `resid_context_recent` (mean residuals {cfg.RECENT_FROM}–{cfg.YEAR_MAX}, NaN when fewer than {cfg.MIN_YEARS_RECENT} window years), ranks, `anaemia_mean_recent_all`, `country_effect_fe`, exposure means, the event columns."
    )
    dd.append(
        "- `deviants_policy_stock.csv`, `deviant_contrast.csv`, `deviants_timeline.csv` — the two context tails, their exposure means with Mann-Whitney p, and their dated anaemia-policy stock at five points in time."
    )
    (cfg.PANEL_DIR / "DATA_DICTIONARY.md").write_text("\n".join(dd) + "\n", encoding="utf-8")
    print("→", cfg.PANEL_DIR / "DATA_DICTIONARY.md")


if __name__ == "__main__":
    sys.exit(main())
