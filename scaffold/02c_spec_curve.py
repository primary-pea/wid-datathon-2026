"""02c — specification curve (v2.0, Simonsohn, Simmons & Nelson 2020): every pre-specified combination of exposure
construction × estimator × income measure × lag × control set, each coefficient expressed in percentage points of
anaemia per within-country standard deviation of the exposure. Writes results/spec_curve.csv and stats/02c_spec.json."""

from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

import config as cfg
from util import cluster_groups, load_frame, save_stats, window

warnings.filterwarnings("ignore")

EXPOSURES = [f for f in cfg.POLICY_ALL if f != "feat_gifna_policy_count_active"]
ESTIMATORS = ["fe", "fe_trend", "fd", "ldv"]
INCOMES = {"constant": cfg.LOG_INCOME, "current": cfg.LOG_INCOME_ALT}
CONTROLS = {"none": [], "context": cfg.CONTEXT}


def fit(d: pd.DataFrame, y: str, x: str, inc: str, ctrl: list[str], estimator: str) -> dict | None:
    cols = [y, x, inc] + ctrl
    dd = d.dropna(subset=cols).sort_values(["iso3", "year"]).copy()
    if estimator in ("fd",):
        g = dd.groupby("iso3", sort=False)
        for c in cols:
            dd["d_" + c] = g[c].diff()
        dd = dd.dropna(subset=["d_" + c for c in cols])
        rhs = " + ".join(["d_" + x, "d_" + inc] + ["d_" + c for c in ctrl])
        fml, term = f"d_{y} ~ C(year) + {rhs}", "d_" + x
    elif estimator == "ldv":
        dd = dd.dropna(subset=[f"{y}_l1"])
        rhs = " + ".join([f"{y}_l1", x, inc] + ctrl)
        fml, term = f"{y} ~ C(year) + {rhs}", x
    elif estimator == "fe_trend":
        rhs = " + ".join([x, inc] + ctrl)
        fml, term = f"{y} ~ C(iso3) + C(year) + C(iso3):year + {rhs}", x
    else:
        rhs = " + ".join([x, inc] + ctrl)
        fml, term = f"{y} ~ C(iso3) + C(year) + {rhs}", x
    if dd[x].std() == 0 or len(dd) < 100:
        return None
    m = smf.ols(fml, data=dd).fit(cov_type="cluster", cov_kwds={"groups": cluster_groups(dd)})
    sd_w = float(dd.groupby("iso3")[x].transform(lambda s: s - s.mean()).std())
    if not np.isfinite(sd_w) or sd_w == 0:
        return None
    ci = m.conf_int().loc[term]
    return dict(
        coef_per_within_sd=float(m.params[term] * sd_w),
        ci_low=float(ci[0] * sd_w),
        ci_high=float(ci[1] * sd_w),
        p=float(m.pvalues[term]),
        n_obs=int(m.nobs),
        sd_within=sd_w,
    )


def main() -> None:
    df = window(load_frame())
    y = cfg.OUTCOME
    rows = []
    for f in EXPOSURES:
        for k in cfg.LAGS_SENS:
            x = f"{f}_lag{k}"
            for inc_name, inc in INCOMES.items():
                for ctrl_name, ctrl in CONTROLS.items():
                    for est in ESTIMATORS:
                        r = fit(df, y, x, inc, ctrl, est)
                        if r is None:
                            continue
                        rows.append(dict(exposure=f, lag=k, income=inc_name, controls=ctrl_name, estimator=est, **r))
    S = pd.DataFrame(rows).sort_values("coef_per_within_sd").reset_index(drop=True)
    S["spec_id"] = np.arange(1, len(S) + 1)
    S["excludes_zero"] = (S["ci_high"] < 0) | (S["ci_low"] > 0)
    S.to_csv(cfg.RESULTS / "spec_curve.csv", index=False)
    summ = dict(
        n_specs=int(len(S)),
        share_ci_excludes_zero=float(S["excludes_zero"].mean()),
        share_negative_and_excludes_zero=float((S["ci_high"] < 0).mean()),
        share_positive_and_excludes_zero=float((S["ci_low"] > 0).mean()),
        median_pp_per_within_sd=float(S["coef_per_within_sd"].median()),
        iqr_pp_per_within_sd=[
            float(S["coef_per_within_sd"].quantile(0.25)),
            float(S["coef_per_within_sd"].quantile(0.75)),
        ],
        min_max=[float(S["coef_per_within_sd"].min()), float(S["coef_per_within_sd"].max())],
        by_estimator={
            e: dict(
                n=int((S["estimator"] == e).sum()),
                median=float(S.loc[S["estimator"] == e, "coef_per_within_sd"].median()),
                share_excludes_zero=float(S.loc[S["estimator"] == e, "excludes_zero"].mean()),
            )
            for e in ESTIMATORS
        },
        by_exposure={
            f: dict(
                median=float(S.loc[S["exposure"] == f, "coef_per_within_sd"].median()),
                share_excludes_zero=float(S.loc[S["exposure"] == f, "excludes_zero"].mean()),
            )
            for f in EXPOSURES
        },
        grid=dict(
            exposures=EXPOSURES,
            estimators=ESTIMATORS,
            incomes=list(INCOMES),
            lags=cfg.LAGS_SENS,
            controls=list(CONTROLS),
        ),
    )
    save_stats("02c_spec", summ)
    print(
        f"{summ['n_specs']} specifications; median {summ['median_pp_per_within_sd']:+.2f} pp per within-SD; "
        f"CI excludes zero in {summ['share_ci_excludes_zero']:.0%} (negative {summ['share_negative_and_excludes_zero']:.0%}, positive {summ['share_positive_and_excludes_zero']:.0%})"  # noqa: E501
    )
    print(pd.DataFrame(summ["by_estimator"]).T.round(3).to_string())


if __name__ == "__main__":
    sys.exit(main())
