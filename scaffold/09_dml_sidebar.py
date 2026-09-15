"""09 — sidebar (v2.0): double/debiased machine learning (Chernozhukov et al. 2018) for the partially linear model
anaemia = theta * dose(t-3) + g(controls) + country + year effects. The fixed effects are removed first (two-way
residualization); the nuisance functions g and m are random forests fitted with cross-fitting over country folds; theta
comes from the orthogonalized score with standard errors clustered by country. With 49 units and four controls this
adds no identification; it is the "modern check" the team asked about, and it must give the same sign as the ladder.
Writes stats/09_dml.json. Not part of the report's hash chain.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import config as cfg
from util import load_frame, save_stats, two_way_residualize, window


def main() -> None:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import GroupKFold

    df = window(load_frame())
    y, x = cfg.OUTCOME, f"{cfg.POLICY_MAIN}_lag{cfg.LAG}"
    controls = [cfg.LOG_INCOME] + cfg.CONTEXT
    d = df.dropna(subset=[y, x] + controls).copy()
    d = two_way_residualize(d, [y, x] + controls)
    Y, D = d[y + "_dm"].to_numpy(), d[x + "_dm"].to_numpy()
    W = d[[c + "_dm" for c in controls]].to_numpy()
    groups = pd.factorize(d["iso3"])[0]
    yhat, dhat = np.zeros(len(d)), np.zeros(len(d))
    for train, test in GroupKFold(n_splits=5).split(W, Y, groups):
        rf_y = RandomForestRegressor(n_estimators=300, min_samples_leaf=20, random_state=cfg.SEED).fit(
            W[train], Y[train]
        )
        rf_d = RandomForestRegressor(n_estimators=300, min_samples_leaf=20, random_state=cfg.SEED).fit(
            W[train], D[train]
        )
        yhat[test], dhat[test] = rf_y.predict(W[test]), rf_d.predict(W[test])
    v, u = D - dhat, Y - yhat
    theta = float((v * u).sum() / (v * v).sum())
    psi = v * (u - theta * v)
    J = float((v * v).mean())
    G = int(groups.max()) + 1
    cluster_sum = np.array([psi[groups == g].sum() for g in range(G)])
    var = float((cluster_sum**2).sum() / (J**2 * len(d) ** 2) * G / (G - 1))
    se = float(np.sqrt(var))
    from scipy.stats import norm

    sd_w = float(d.groupby("iso3")[x].transform(lambda s: s - s.mean()).std())
    out = dict(
        theta=theta,
        se=se,
        ci=[theta - 1.96 * se, theta + 1.96 * se],
        p=float(2 * (1 - norm.cdf(abs(theta) / se))),
        theta_per_within_sd=theta * sd_w,
        n_obs=int(len(d)),
        n_countries=G,
        controls=controls,
        nuisance="random forests (300 trees, min leaf 20), 5 country-grouped folds, cross-fitted",
        note="same sign as the ladder is the only claim this sidebar supports",
    )
    save_stats("09_dml", out)
    print(
        f"DML theta = {theta:+.3f} pp per {cfg.POLICY_UNIT} (SE {se:.3f}, p {out['p']:.3f}); per within-SD {out['theta_per_within_sd']:+.2f}; n {len(d)}, {G} countries"  # noqa: E501
    )


if __name__ == "__main__":
    sys.exit(main())
