"""02 — the dose ladder (v2.0): two-way fixed-effects rows, the dynamics rows (lead test, country trends), the bracket
(first difference, long difference, lagged outcome), context and team-control rows, alternative exposures, outcome swaps
with a false-discovery adjustment, the survey-anchored row, the sub-sample block, wild-cluster-bootstrap p-values for
the headline rows, and the equivalence bounds (minimum detectable effect, TOST against a pre-specified smallest effect).
Writes results/fe_coefficients.csv, fe_sensitivity.csv, fe_subsample.csv and stats/02_fe.json.
"""

from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import norm

import config as cfg
from util import (
    bh_adjust,
    cluster_groups,
    fe_fit,
    fe_fit_trends,
    load_frame,
    ols_rows,
    res_rows,
    save_stats,
    wild_cluster_bootstrap_p,
    window,
)


def lagged(f: str, k: int) -> str:
    return f"{f}_lag{k}"


def standardize(d: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    d = d.copy()
    for c in cols:
        d[c + "_z"] = (d[c] - d[c].mean()) / d[c].std()
    return d


def ols_cluster(d: pd.DataFrame, formula: str):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return smf.ols(formula, data=d).fit(cov_type="cluster", cov_kwds={"groups": cluster_groups(d)})


class Ladder:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.sens: list[dict] = []

    def _record(self, name: str, block: str, rows: list[dict], note: str) -> None:
        self.rows.extend(rows)
        self.inputs = getattr(self, "inputs", {})
        self.sens.append(
            {"variant": name, "block": block, **{k: v for k, v in rows[0].items() if k != "spec"}, "note": note}
        )

    def variant(self, name: str, block: str, d: pd.DataFrame, y: str, xs: list[str], note: str):
        r, dd = fe_fit(d, y, xs)
        self._record(name, block, res_rows(r, name, y, dd), note)
        self.inputs[name] = (d, y, xs, xs[0], ("iso3", "year"))
        return r, dd

    def variant_trends(self, name: str, block: str, d: pd.DataFrame, y: str, xs: list[str], note: str):
        m, dd, r2w = fe_fit_trends(d, y, xs)
        self._record(name, block, ols_rows(m, name, y, dd, xs, r2w), note)
        return m, dd

    def variant_ols(self, name: str, block: str, d: pd.DataFrame, y: str, formula: str, terms: list[str], note: str):
        """A statsmodels OLS row (first differences, long differences, lagged outcome), SE clustered by country."""
        needed = [c for c in terms if c in d.columns]
        dd = d.dropna(subset=[y] + needed).copy()
        m = ols_cluster(dd, formula)
        self._record(name, block, ols_rows(m, name, y, dd, terms, float(m.rsquared)), note)
        self.inputs[name] = (dd, y, terms, terms[0], ("year",))
        return m, dd


def differences(df: pd.DataFrame, cols: list[str], k: int, prefix: str) -> pd.DataFrame:
    d = df.sort_values(["iso3", "year"]).copy()
    g = d.groupby("iso3", sort=False)
    for c in cols:
        d[f"{prefix}{c}"] = g[c].diff(k)
    return d


def main() -> None:
    df = window(load_frame())
    y = cfg.OUTCOME
    main_x, lead_x = lagged(cfg.POLICY_MAIN, cfg.LAG), f"{cfg.POLICY_MAIN}_lead{cfg.LEAD}"
    inc, inc_alt = cfg.LOG_INCOME, cfg.LOG_INCOME_ALT
    lad = Ladder()

    # ---- spec A (levels, two-way FE) and its standardized twin ----
    rA, dA = lad.variant(
        "A_main",
        "main",
        df,
        y,
        [main_x, inc],
        f"main spec: {cfg.POLICY_LABELS[cfg.POLICY_MAIN]} lagged {cfg.LAG} y + log GDP pc (constant 2015 US$); country + year FE; SE clustered by country",  # noqa: E501
    )
    est = df.dropna(subset=[y, main_x, inc])
    rAz, dAz = fe_fit(standardize(est, [main_x, inc]), y, [main_x + "_z", inc + "_z"])
    lad.rows += res_rows(rAz, "A_main_std_overall", y, dAz)
    sd_overall = float(est[main_x].std())
    sd_within = float(est.groupby("iso3")[main_x].transform(lambda s: s - s.mean()).std())

    # ---- main-block sensitivity ----
    for k in cfg.LAGS_SENS:
        if k != cfg.LAG:
            lad.variant(
                f"lag{k}",
                "main",
                df,
                y,
                [lagged(cfg.POLICY_MAIN, k), inc],
                f"policy lagged {k} years instead of {cfg.LAG}",
            )
    lad.variant(
        "drop_thin",
        "main",
        df[~df["iso3"].isin(cfg.THIN)],
        y,
        [main_x, inc],
        f"without {', '.join(cfg.THIN)} (thinnest income coverage)",
    )
    lad.variant(
        "income_current_usd",
        "main",
        df,
        y,
        [main_x, inc_alt],
        "log GDP pc in current US$ (team file) instead of constant 2015 US$",
    )

    # ---- dynamics: lead test (the old 'placebo') and country-specific trends (one sensitivity, not the verdict) ----
    lad.variant(
        "lead_test_only",
        "lead_test",
        df,
        y,
        [lead_x, inc],
        f"policy {cfg.LEAD} years LATER instead of earlier — a lead that predicts today's anaemia signals pre-existing trend or targeting",
    )
    lad.variant(
        "lead_test_with_lag",
        "lead_test",
        df,
        y,
        [lead_x, main_x, inc],
        "lead and lag together — the lead is the reported term",
    )
    lad.variant_trends(
        "trend_main",
        "trend",
        df,
        y,
        [main_x, inc],
        "main spec plus a linear trend per country (absorbs slowly phasing-in effects too — Wolfers 2006)",
    )
    lad.variant_trends("trend_lead", "trend", df, y, [lead_x, inc], "lead test plus a linear trend per country")

    # ---- the bracket: first difference, long difference, lagged outcome (Ding & Li 2019) ----
    dfd = differences(df, [y, main_x, inc], 1, "d1_")
    lad.variant_ols(
        "fd",
        "bracket",
        dfd,
        f"d1_{y}",
        f"d1_{y} ~ C(year) + d1_{main_x} + d1_{inc}",
        [f"d1_{main_x}", f"d1_{inc}"],
        "first differences (Δ outcome on Δ lagged policy and Δ log income, year effects)",
    )
    dld = differences(df, [y, main_x, inc], cfg.LONG_DIFF, f"d{cfg.LONG_DIFF}_")
    ld = f"d{cfg.LONG_DIFF}_"
    lad.variant_ols(
        f"longdiff{cfg.LONG_DIFF}",
        "bracket",
        dld,
        f"{ld}{y}",
        f"{ld}{y} ~ C(year) + {ld}{main_x} + {ld}{inc}",
        [f"{ld}{main_x}", f"{ld}{inc}"],
        f"{cfg.LONG_DIFF}-year differences",
    )
    yl1 = f"{y}_l1"
    m_ldv, d_ldv = lad.variant_ols(
        "ldv",
        "bracket",
        df,
        y,
        f"{y} ~ C(year) + {yl1} + {main_x} + {inc}",
        [main_x, yl1, inc],
        "lagged outcome instead of country effects (year effects kept); with FE this brackets the effect",
    )
    rho = float(m_ldv.params[yl1])
    ldv_long_run = float(m_ldv.params[main_x] / (1 - rho)) if rho < 1 else float("nan")

    # ---- context block (anaemia-literature drivers) and the team's confounders ----
    lad.variant(
        "ctx_all",
        "context",
        df,
        y,
        [main_x, inc] + cfg.CONTEXT,
        "main spec + malaria incidence + fertility + urbanisation (complete World Bank series)",
    )
    for c in cfg.CONTEXT + cfg.CONTEXT_EXTRA:
        short = c.replace("feat_", "").split("_")[0]
        lad.variant(f"ctx_{short}", "context", df, y, [main_x, inc, c], f"main spec + {cfg.CONTROL_LABELS[c]}")
    for c in cfg.TEAM_CONTROLS:
        short = c.replace("feat_", "").split("_")[0]
        lad.variant(
            f"team_{short}", "team", df, y, [main_x, inc, c], f"main spec + {cfg.CONTROL_LABELS[c]} (the team's ask)"
        )

    # ---- implementation block (13 Sep): delivered deworming coverage as the exposure, next to the paper record ----
    for f in cfg.IMPLEMENTATION:
        short = f.replace("feat_", "").split("_")[0]
        lad.variant(
            f"impl_{short}",
            "implementation",
            df,
            y,
            [lagged(f, cfg.LAG), inc],
            f"{cfg.CONTROL_LABELS[f]} lagged {cfg.LAG} y as the exposure (implementation, not policy on paper)",
        )
        lad.variant(
            f"impl_{short}_with_policy",
            "implementation",
            df,
            y,
            [lagged(f, cfg.LAG), main_x, inc],
            "the same with the policy dose alongside; the reported term is the coverage",
        )

    # ---- alternative exposures ----
    for f in [f for f in cfg.POLICY_ALL if f != cfg.POLICY_MAIN]:
        short = f.replace("feat_gd_", "").replace("feat_gifna_", "team_")
        lad.variant(
            f"alt_{short}",
            "alt_policy",
            df,
            y,
            [lagged(f, cfg.LAG), inc],
            f"{cfg.POLICY_LABELS[f]} lagged {cfg.LAG} y instead of the main dose",
        )
        if f in (cfg.POLICY_TEAM, "feat_gd_any_anaemia_policies", "feat_gd_any_fortification"):
            lad.variant_trends(
                f"alt_{short}_trend",
                "alt_policy",
                df,
                y,
                [lagged(f, cfg.LAG), inc],
                f"{cfg.POLICY_LABELS[f]} lagged {cfg.LAG} y plus a linear trend per country",
            )

    # ---- outcome swaps with a false-discovery adjustment across the secondary outcomes ----
    swap_p = {}
    for y2, lab in cfg.SECONDARY.items():
        r2, _ = lad.variant(f"outcome_{y2}", "outcome_swap", df, y2, [main_x, inc], f"outcome swapped: {lab}")
        swap_p[y2] = float(r2.pvalues[main_x])
    p_bh = dict(zip(swap_p, bh_adjust(list(swap_p.values())), strict=True))

    # ---- survey-anchored row: only country-years with a DHS haemoglobin survey ----
    anchored = df[df[cfg.SURVEY_FLAG] == 1]
    anchor = None
    try:
        rS, dS = lad.variant(
            "survey_anchored",
            "anchor",
            anchored,
            y,
            [main_x, inc],
            "only country-years with a DHS survey that measured women's haemoglobin (the estimates are anchored there)",
        )
        anchor = dict(
            coef=float(rS.params[main_x]),
            se=float(rS.std_errors[main_x]),
            p=float(rS.pvalues[main_x]),
            n_obs=int(rS.nobs),
            n_countries=int(dS.index.get_level_values(0).nunique()),
        )
    except Exception as e:  # too few rows for two-way effects in a thin sample must not stop the run
        anchor = dict(error=f"{type(e).__name__}: {e}"[:200], n_obs=int(len(anchored)))

    lad.variant(
        "income_only",
        "reference",
        df,
        y,
        [inc],
        "log GDP pc only — the reported term is the INCOME coefficient (reference row)",
    )

    # ---- sub-sample block: each control on its own rows, next to the base spec on the same rows ----
    sub_rows = []
    for f, y0 in cfg.SUBPERIOD.items():
        ds = df[df["year"] >= y0].dropna(subset=[y, main_x, inc, f])
        if ds["iso3"].nunique() < 10:
            continue
        r_base, d_base = fe_fit(ds, y, [main_x, inc])
        r_ctrl, d_ctrl = fe_fit(ds, y, [main_x, inc, f])
        for label, r, d in [("base_same_rows", r_base, d_base), ("with_control", r_ctrl, d_ctrl)]:
            row = res_rows(r, f"sub_{f}_{label}", y, d)[0]
            sub_rows.append(
                {"control": f, "from_year": y0, "model": label, **{k: v for k, v in row.items() if k != "spec"}}
            )
        lad.rows += res_rows(r_ctrl, f"sub_{f}", y, d_ctrl)

    # ---- wild cluster bootstrap p-values (Rademacher, null imposed) for every row whose fit is a plain FE regression;
    #      the country-trend rows are left blank (the bootstrap would have to re-estimate 49 trend slopes per draw) ----
    wcb = {}
    for name, (dd_, y_, xs_, term_, fe_) in lad.inputs.items():
        try:
            wcb[name] = wild_cluster_bootstrap_p(dd_, y_, xs_, term_, B=cfg.WCB_B, seed=cfg.SEED, fe=fe_)
        except Exception as e:  # a thin sample (survey-anchored row) may not support the residualization
            wcb[name] = {"p_wcb": float("nan"), "error": f"{type(e).__name__}: {e}"[:120]}

    coefs, sens, subs = pd.DataFrame(lad.rows), pd.DataFrame(lad.sens), pd.DataFrame(sub_rows)
    sens["p_bh"] = sens["variant"].map(lambda v: p_bh.get(v.replace("outcome_", ""), np.nan))
    sens["p_wcb"] = sens["variant"].map(lambda v: wcb[v]["p_wcb"] if v in wcb else np.nan)
    coefs.to_csv(cfg.RESULTS / "fe_coefficients.csv", index=False)
    sens.to_csv(cfg.RESULTS / "fe_sensitivity.csv", index=False)
    subs.to_csv(cfg.RESULTS / "fe_subsample.csv", index=False)

    # ---- bounds: minimum detectable effect and equivalence test against the pre-specified smallest effect ----
    b, se = float(rA.params[main_x]), float(rA.std_errors[main_x])
    mde = (norm.ppf(0.975) + norm.ppf(0.80)) * se
    sesoi_unit = cfg.SESOI_PP_PER_WITHIN_SD / sd_within  # pp per unit of the dose
    p_lower = 1 - norm.cdf((b + sesoi_unit) / se)  # H0: beta <= -sesoi (a beneficial effect at least this large)
    p_upper = norm.cdf((b - sesoi_unit) / se)  # H0: beta >= +sesoi
    lo90, hi90 = b - norm.ppf(0.95) * se, b + norm.ppf(0.95) * se
    bounds = dict(
        sesoi_pp_per_within_sd=cfg.SESOI_PP_PER_WITHIN_SD,
        sesoi_pp_per_unit=sesoi_unit,
        mde80_pp_per_unit=mde,
        mde80_pp_per_within_sd=mde * sd_within,
        mde80_pp_per_overall_sd=mde * sd_overall,
        ci90_per_unit=[lo90, hi90],
        ci90_per_within_sd=[lo90 * sd_within, hi90 * sd_within],
        tost_p_lower=float(p_lower),
        tost_p_upper=float(p_upper),
        tost_p=float(max(p_lower, p_upper)),
        equivalent_at_5pct=bool(max(p_lower, p_upper) < 0.05),
        largest_beneficial_effect_not_ruled_out_pp_per_within_sd=float(lo90 * sd_within),
    )

    tr = sens.set_index("variant")

    def row(v: str) -> dict:
        r = tr.loc[v]
        return dict(
            term=r["term"],
            coef=float(r["coef"]),
            ci=[float(r["ci_low"]), float(r["ci_high"])],
            p=float(r["p"]),
            n=int(r["n_obs"]),
        )

    ciA = rA.conf_int()
    stats = dict(
        spec_A=dict(
            coef=b,
            se=se,
            ci=[float(ciA.loc[main_x, "lower"]), float(ciA.loc[main_x, "upper"])],
            p=float(rA.pvalues[main_x]),
            n_obs=int(rA.nobs),
            n_countries=int(dA.index.get_level_values(0).nunique()),
            r2_within=float(rA.rsquared),
            r2_within_note="two-way within R² after both fixed effects (= fixest wr2)",
            income_coef=float(rA.params[inc]),
            income_se=float(rA.std_errors[inc]),
            income_p=float(rA.pvalues[inc]),
            unit=f"pp of anaemia per {cfg.POLICY_UNIT}",
        ),
        spec_A_std=dict(
            coef_per_overall_sd=float(rAz.params[main_x + "_z"]),
            se_per_overall_sd=float(rAz.std_errors[main_x + "_z"]),
            sd_overall=sd_overall,
            coef_per_within_sd=float(b * sd_within),
            se_per_within_sd=float(se * sd_within),
            sd_within=sd_within,
            income_coef_per_overall_sd=float(rAz.params[inc + "_z"]),
        ),
        lead_test=dict(only=row("lead_test_only"), with_lag=row("lead_test_with_lag")),
        trend=dict(main=row("trend_main"), lead=row("trend_lead")),
        bracket=dict(
            fd=row("fd"),
            longdiff=row(f"longdiff{cfg.LONG_DIFF}"),
            ldv={**row("ldv"), "rho": rho, "long_run_coef": ldv_long_run},
        ),
        context={v: row(v) for v in sens.loc[sens["block"] == "context", "variant"]},
        team={v: row(v) for v in sens.loc[sens["block"] == "team", "variant"]},
        alt_policy={v: row(v) for v in sens.loc[sens["block"] == "alt_policy", "variant"]},
        outcome_swaps={
            y2: {**row(f"outcome_{y2}"), "p_bh": p_bh[y2], "label": cfg.SECONDARY[y2]} for y2 in cfg.SECONDARY
        },
        survey_anchored=anchor,
        bounds=bounds,
        wild_cluster_bootstrap=wcb,
        sensitivity={
            r["variant"]: dict(
                block=r["block"], term=r["term"], coef=r["coef"], ci=[r["ci_low"], r["ci_high"]], p=r["p"], n=r["n_obs"]
            )
            for r in lad.sens
        },
        subsample=[
            {k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) for k, v in r.items()} for r in sub_rows
        ],
    )
    save_stats("02_fe", stats)
    print(sens[["variant", "block", "term", "coef", "ci_low", "ci_high", "p", "p_wcb", "n_obs"]].round(3).to_string())
    print(
        f"\nper within-country SD {stats['spec_A_std']['coef_per_within_sd']:+.2f} (SD {sd_within:.2f}); MDE80 {bounds['mde80_pp_per_within_sd']:.2f} pp per within-SD; "  # noqa: E501
        f"90% CI per within-SD [{bounds['ci90_per_within_sd'][0]:+.2f}, {bounds['ci90_per_within_sd'][1]:+.2f}]; TOST p {bounds['tost_p']:.3f}; "
        f"wild-bootstrap p (A_main) {wcb['A_main']['p_wcb']:.3f}"
    )


if __name__ == "__main__":
    sys.exit(main())
