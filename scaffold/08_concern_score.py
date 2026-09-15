"""08 — sidebar (v2.0): the analytics member's "overall concern score", reproduced on the 49 countries from the panel.

Her method (skeleton doc, 12 Sep): for each of four women's indicators a country is flagged 0 if it improved over time,
1 if it started in the highest 25% and 2 if it worsened; the country's percentile on the indicator is added; the overall
score is a weighted average of the four indicator scores. Weights are equal here until she confirms hers; a
weight-perturbation check (Dirichlet draws) reports how stable the ranking is (OECD/JRC 2008 handbook, step 7).
Writes results/concern_score.csv and stats/08_concern.json. Not part of the report's hash chain.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import config as cfg
from util import load_frame, save_stats, window

INDICATORS = cfg.WOMEN_INDEX_COMPONENTS


def score_indicator(w: pd.DataFrame, col: str) -> pd.DataFrame:
    g = w.dropna(subset=[col]).sort_values("year").groupby("iso3")
    first = g[col].first()
    last = g[col].last()
    start_high = first >= first.quantile(0.75)
    worsened = last > first
    flag = pd.Series(0, index=first.index, dtype=float)
    flag[start_high & ~worsened] = 1  # started high (and did not worsen)
    flag[worsened] = 2
    pct = last.rank(pct=True)
    return pd.DataFrame(
        {f"{col}_first": first, f"{col}_last": last, f"{col}_flag": flag, f"{col}_pct": pct, f"{col}_score": flag + pct}
    )


def main() -> None:
    w = window(load_frame())
    parts = [score_indicator(w, c) for c in INDICATORS]
    S = pd.concat(parts, axis=1)
    S["country"] = w.drop_duplicates("iso3").set_index("iso3")["country"]
    scores = S[[f"{c}_score" for c in INDICATORS]]
    S["concern_equal_weights"] = scores.mean(axis=1)
    S["rank_equal_weights"] = S["concern_equal_weights"].rank(ascending=False)
    rng = np.random.default_rng(cfg.SEED)
    ranks = []
    for _ in range(500):
        wts = rng.dirichlet(np.ones(len(INDICATORS)))
        ranks.append((scores.to_numpy() @ wts).argsort()[::-1].argsort() + 1)
    ranks = np.array(ranks)
    S["rank_median_random_weights"] = np.median(ranks, axis=0)
    S["rank_p90_random_weights"] = np.percentile(ranks, 90, axis=0)
    S["share_top10_random_weights"] = (ranks <= 10).mean(axis=0)
    S = S.sort_values("concern_equal_weights", ascending=False).reset_index().rename(columns={"index": "iso3"})
    S.to_csv(cfg.RESULTS / "concern_score.csv", index=False)
    top = S.head(10)
    rho = float(pd.Series(S["rank_equal_weights"]).corr(pd.Series(S["rank_median_random_weights"]), method="spearman"))
    stats = dict(
        method="flag 0 improved / 1 started in top quartile / 2 worsened, plus the percentile of the latest level; equal weights over four women's indicators; 500 Dirichlet weight draws for stability",  # noqa: E501
        indicators=INDICATORS,
        window=[cfg.YEAR_MIN, cfg.YEAR_MAX],
        top10=[
            dict(
                iso3=r.iso3,
                country=r.country,
                score=round(float(r.concern_equal_weights), 3),
                share_top10_under_random_weights=round(float(r.share_top10_random_weights), 2),
            )
            for r in top.itertuples()
        ],
        spearman_equal_vs_median_random_weights=rho,
        note="reproduction pending the analytics member's exact weights; the global 194-country version in the skeleton doc uses the same logic on all countries",  # noqa: E501
    )
    save_stats("08_concern", stats)
    print(
        S[["iso3", "country", "concern_equal_weights", "rank_equal_weights", "share_top10_random_weights"]]
        .head(12)
        .round(3)
        .to_string()
    )
    print(f"Spearman(equal-weight rank, median rank under random weights) = {rho:.3f}")


if __name__ == "__main__":
    sys.exit(main())
