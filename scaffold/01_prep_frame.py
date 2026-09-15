"""01 — modelling frame: log incomes, lagged/lead policy features, the FIES gender gap, the survey-anchor flag, the
women's-nutrition summary index and the lagged outcome (v2.0). Reads the panel, writes results/frame.csv."""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import config as cfg
from util import check_panel_grid, load_panel, save_stats


def prep_frame(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Add derived columns and positional lags/leads (valid only because the panel is a complete grid — checked)."""
    check_panel_grid(panel)
    p = panel.sort_values(["iso3", "year"]).reset_index(drop=True).copy()
    for c in cfg.GIFNA_NAN_IS_ZERO:
        p[c] = p[c].fillna(0.0)  # NaN in these = no active record that year (all 49 countries are in GIFNA)
    for inc, log_inc in [(cfg.INCOME, cfg.LOG_INCOME), (cfg.INCOME_ALT, cfg.LOG_INCOME_ALT)]:
        bad = int((p[inc] <= 0).sum())
        if bad:
            raise ValueError(f"{inc}: {bad} non-positive values; log is undefined")
        p[log_inc] = np.log(p[inc])
    p["feat_fies_gap_fm_3yr"] = p["feat_fies_severe_female_pct_3yr"] - p["feat_fies_severe_male_pct_3yr"]
    p[cfg.SURVEY_FLAG] = p[cfg.SURVEY_FLAG].fillna(0).astype(int)
    p["subregion"] = p["iso3"].map(cfg.SUBREGION)

    # women's nutrition summary index: mean z-score of the four women's indicators (standardized on the window rows;
    # higher = worse); requires all four components, so it ends where the NCD-RisC series ends
    win = p["year"].between(cfg.YEAR_MIN, cfg.YEAR_MAX)
    z = {}
    for c in cfg.WOMEN_INDEX_COMPONENTS:
        mu, sd = p.loc[win, c].mean(), p.loc[win, c].std()
        z[c] = (p[c] - mu) / sd
    Z = pd.DataFrame(z)
    p["out_women_index"] = Z.mean(axis=1).where(Z.notna().all(axis=1))

    g = p.groupby("iso3", sort=False)
    lags = sorted(set(cfg.LAGS_SENS) | {cfg.LAG})
    new = {f"{cfg.OUTCOME}_l1": g[cfg.OUTCOME].shift(1)}
    for f in cfg.POLICY_ALL + cfg.IMPLEMENTATION:
        for k in lags:
            new[f"{f}_lag{k}"] = g[f].shift(k)
        if f in cfg.POLICY_ALL:
            new[f"{f}_lead{cfg.LEAD}"] = g[f].shift(-cfg.LEAD)
    p = pd.concat([p, pd.DataFrame(new, index=p.index)], axis=1)
    keep = (
        ["iso3", "country", "subregion", "year", cfg.OUTCOME, f"{cfg.OUTCOME}_l1"]
        + list(cfg.SECONDARY)
        + [cfg.INCOME, cfg.LOG_INCOME, cfg.INCOME_ALT, cfg.LOG_INCOME_ALT]
        + cfg.CONTEXT
        + cfg.CONTEXT_EXTRA
        + cfg.TEAM_CONTROLS
        + list(cfg.SUBPERIOD)
        + [cfg.SURVEY_FLAG]
        + cfg.POLICY_ALL
        + cfg.IMPLEMENTATION
        + [f"{f}_lag{k}" for f in cfg.POLICY_ALL + cfg.IMPLEMENTATION for k in lags]
        + [f"{f}_lead{cfg.LEAD}" for f in cfg.POLICY_ALL]
    )
    keep = list(dict.fromkeys(keep))
    info = {
        "women_index_components": cfg.WOMEN_INDEX_COMPONENTS,
        "women_index_rows_in_window": int(p.loc[win, "out_women_index"].notna().sum()),
        "survey_anchor_country_years_in_window": int(p.loc[win, cfg.SURVEY_FLAG].sum()),
        "survey_anchor_countries": int(p.loc[win & (p[cfg.SURVEY_FLAG] == 1), "iso3"].nunique()),
    }
    return p[keep], info


def main() -> None:
    panel = load_panel()
    frame, info = prep_frame(panel)
    cfg.RESULTS.mkdir(parents=True, exist_ok=True)
    frame.to_csv(cfg.FRAME_CSV, index=False)
    win = frame[(frame["year"] >= cfg.YEAR_MIN) & (frame["year"] <= cfg.YEAR_MAX)]
    main_x = f"{cfg.POLICY_MAIN}_lag{cfg.LAG}"
    est = win.dropna(subset=[cfg.OUTCOME, cfg.LOG_INCOME, main_x])
    allx = [f"{f}_lag{cfg.LAG}" for f in cfg.POLICY_ALL]
    corr = est[allx].corr().round(2)
    within_sd = est.groupby("iso3")[main_x].transform(lambda s: s - s.mean()).std()
    varying = est.groupby("iso3")[main_x].std().fillna(0)
    stats = dict(
        panel_rows=int(len(panel)),
        frame_rows=int(len(frame)),
        window=[cfg.YEAR_MIN, cfg.YEAR_MAX],
        estimation_sample=dict(
            rows=int(len(est)),
            countries=int(est["iso3"].nunique()),
            years=[int(est["year"].min()), int(est["year"].max())],
            outcome=cfg.OUTCOME,
            policy_main=main_x,
            income=cfg.LOG_INCOME,
        ),
        identified_from_countries=int((varying > 0).sum()),
        constant_within_country=sorted(varying[varying == 0].index),
        outcome_sd_within=float(est.groupby("iso3")[cfg.OUTCOME].transform(lambda s: s - s.mean()).std()),
        outcome_sd_overall=float(est[cfg.OUTCOME].std()),
        outcome_mean=float(est[cfg.OUTCOME].mean()),
        policy_main_sd=float(est[main_x].std()),
        policy_main_mean=float(est[main_x].mean()),
        policy_main_sd_within=float(within_sd),
        policy_unit=cfg.POLICY_UNIT,
        gifna_nan_filled_zero=cfg.GIFNA_NAN_IS_ZERO,
        income_alt_sample_rows=int(win.dropna(subset=[cfg.OUTCOME, cfg.LOG_INCOME_ALT, main_x]).shape[0]),
        corr_lag3_exposures=corr.to_dict(),
        max_abs_corr_between_exposures=float(np.abs(corr.values - np.eye(len(allx))).max()),
        context_coverage={c: int(win[c].notna().sum()) for c in cfg.CONTEXT + cfg.CONTEXT_EXTRA + cfg.TEAM_CONTROLS},
        **info,
    )
    save_stats("01_frame", stats)
    print(
        f"frame {frame.shape} → estimation sample {len(est)} rows, {est['iso3'].nunique()} countries, {est['year'].min()}–{est['year'].max()}"
    )
    print(
        f"policy main lag{cfg.LAG}: mean {stats['policy_main_mean']:.2f} sd {stats['policy_main_sd']:.2f} "
        f"within-sd {stats['policy_main_sd_within']:.2f}; identified from {stats['identified_from_countries']} countries "
        f"(constant: {stats['constant_within_country']}); women index rows {info['women_index_rows_in_window']}; "
        f"survey-anchored country-years {info['survey_anchor_country_years_in_window']} in {info['survey_anchor_countries']} countries"
    )


if __name__ == "__main__":
    sys.exit(main())
