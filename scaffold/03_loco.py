"""03 — leave-one-country-out validation on the within-country path.

For each country, fit the two-way FE model on the other 48 and predict the held-out country's deviations from its
own mean; nested models naive < year effects < + income < + policy < + all exposures, on one common sample; a context ladder on
its own sample and a bootstrap interval on the policy term's RMSE change (v2.0).
Writes results/loco_rmse.csv, loco_per_country.csv, loco_predictions.csv and stats/03_loco.json.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import binomtest

import config as cfg
from util import load_frame, save_stats, window


def design(dd: pd.DataFrame, xs: list[str], countries: list[str], years: list[int]) -> pd.DataFrame:
    cols = {f"c_{c}": (dd["iso3"] == c).astype(float).values for c in countries[1:]}
    cols.update({f"y_{yr}": (dd["year"] == yr).astype(float).values for yr in years[1:]})
    for x in xs:
        cols[x] = dd[x].values
    cols["const"] = np.ones(len(dd))
    return pd.DataFrame(cols, index=dd.index)


def loco(d: pd.DataFrame, y: str, xs: list[str], name: str, countries: list[str], years: list[int]) -> pd.DataFrame:
    out = []
    for k in countries:
        tr, te = d[d["iso3"] != k], d[d["iso3"] == k]
        X = design(tr, xs, sorted(tr["iso3"].unique()), years)
        b = dict(zip(X.columns, sm.OLS(tr[y].values, X.values).fit().params, strict=True))
        gam = np.array([b.get(f"y_{yr}", 0.0) for yr in te["year"]])
        xb = np.zeros(len(te))
        for x in xs:
            xb += b[x] * (te[x].values - te[x].values.mean())
        pred = xb + (gam - gam.mean())
        obs = te[y].values - te[y].values.mean()
        out.append(pd.DataFrame(dict(model=name, iso3=k, year=te["year"].values, obs_dev=obs, pred_dev=pred)))
    return pd.concat(out, ignore_index=True)


def main() -> None:
    df = window(load_frame())
    y = cfg.OUTCOME
    main_x = f"{cfg.POLICY_MAIN}_lag{cfg.LAG}"
    allx = [f"{f}_lag{cfg.LAG}" for f in cfg.POLICY_ALL]
    models = {
        "M0_year_effects": [],
        "M1_income": [cfg.LOG_INCOME],
        "M2_income_policy": [cfg.LOG_INCOME, main_x],
        "M2t_income_team_composite": [cfg.LOG_INCOME, f"{cfg.POLICY_TEAM}_lag{cfg.LAG}"],
        "M3_income_all_exposures": [cfg.LOG_INCOME] + allx,
    }
    d = df.dropna(subset=[y, cfg.LOG_INCOME] + allx).copy()  # one common sample so the RMSEs are comparable
    countries, years = sorted(d["iso3"].unique()), sorted(int(v) for v in d["year"].unique())

    # context ladder on its own (smaller) sample: countries without a malaria series drop out
    dc = df.dropna(subset=[y, cfg.LOG_INCOME, main_x] + cfg.CONTEXT).copy()
    cc, cy = sorted(dc["iso3"].unique()), sorted(int(v) for v in dc["year"].unique())
    ctx_models = {
        "C1_income": [cfg.LOG_INCOME],
        "C2_income_context": [cfg.LOG_INCOME] + cfg.CONTEXT,
        "C3_income_context_policy": [cfg.LOG_INCOME] + cfg.CONTEXT + [main_x],
    }
    PC = pd.concat([loco(dc, y, xs, name, cc, cy) for name, xs in ctx_models.items()], ignore_index=True)
    PC["err"] = PC["obs_dev"] - PC["pred_dev"]
    ctx_rmse = {m: float(np.sqrt((PC.loc[PC["model"] == m, "err"] ** 2).mean())) for m in ctx_models}

    P = pd.concat([loco(d, y, xs, name, countries, years) for name, xs in models.items()], ignore_index=True)
    naive = P[P["model"] == "M0_year_effects"].assign(model="naive_flat", pred_dev=0.0)
    P = pd.concat([naive, P], ignore_index=True)
    P["err"] = P["obs_dev"] - P["pred_dev"]
    order = ["naive_flat"] + list(models)
    agg = (
        P.assign(e2=P["err"] ** 2, o2=P["obs_dev"] ** 2)
        .groupby("model")
        .agg(sse=("e2", "sum"), sst=("o2", "sum"), mae=("err", lambda s: float(s.abs().mean())), n=("err", "size"))
    )
    summ = agg.reindex(order).reset_index()
    summ["rmse"] = np.sqrt(summ["sse"] / summ["n"])
    summ["r2_dev"] = 1 - summ["sse"] / summ["sst"]
    summ = summ[["model", "rmse", "mae", "n", "r2_dev"]]
    per = P.assign(e2=P["err"] ** 2).groupby(["model", "iso3"])["e2"].mean().pow(0.5).unstack(0)[order].reset_index()
    summ.to_csv(cfg.RESULTS / "loco_rmse.csv", index=False)
    per.to_csv(cfg.RESULTS / "loco_per_country.csv", index=False)
    P.to_csv(cfg.RESULTS / "loco_predictions.csv", index=False)

    m2 = P[P["model"] == "M2_income_policy"]
    r = float(np.corrcoef(m2["obs_dev"], m2["pred_dev"])[0, 1])
    helps = int((per["M1_income"] - per["M2_income_policy"] > 0).sum())
    s = summ.set_index("model")
    # country-resampled bootstrap interval on the RMSE difference M2 - M1 (v2.0)
    sse = P.assign(e2=P["err"] ** 2).groupby(["model", "iso3"])["e2"].agg(["sum", "size"]).unstack(0)
    rng = np.random.default_rng(cfg.SEED)
    diffs = []
    for _ in range(500):
        pick = rng.choice(countries, size=len(countries), replace=True)
        s1 = sse["sum"]["M1_income"].loc[pick].sum() / sse["size"]["M1_income"].loc[pick].sum()
        s2 = sse["sum"]["M2_income_policy"].loc[pick].sum() / sse["size"]["M2_income_policy"].loc[pick].sum()
        diffs.append(np.sqrt(s2) - np.sqrt(s1))
    boot_ci = [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]
    stats = dict(
        sample=dict(rows=int(len(d)), countries=len(countries), years=[years[0], years[-1]]),
        rmse={
            row.model: dict(rmse=float(row.rmse), mae=float(row.mae), r2_dev=float(row.r2_dev), n=int(row.n))
            for row in summ.itertuples()
        },
        m2_vs_m1_rmse_change_pct=float((s.loc["M2_income_policy", "rmse"] / s.loc["M1_income", "rmse"] - 1) * 100),
        m2_calibration_r=r,
        countries_where_policy_helps=helps,
        countries_total=int(len(per)),
        countries_where_policy_helps_binomial_p=float(binomtest(helps, int(len(per)), 0.5).pvalue),
        m2_vs_m1_rmse_diff_pp=float(s.loc["M2_income_policy", "rmse"] - s.loc["M1_income", "rmse"]),
        m2_vs_m1_rmse_diff_boot95=boot_ci,
        context_ladder=dict(sample=dict(rows=int(len(dc)), countries=len(cc)), rmse=ctx_rmse),
        method="within-country deviations from own mean; year effects transferred from the training set; common estimation sample",
    )
    save_stats("03_loco", stats)
    print(summ.round(3).to_string())
    print(
        f"M2 calibration r: {r:.3f} | policy helps in {helps} of {len(per)} countries "
        f"(binomial p vs chance = {stats['countries_where_policy_helps_binomial_p']:.2f})"
    )


if __name__ == "__main__":
    sys.exit(main())
