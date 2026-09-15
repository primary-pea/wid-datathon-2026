"""04 — cross-country rankings (v2.0) and the positive-deviance profiles.

(a) Income-only level model (year effects + log GDP, no country effects) — the v1.2 ranking, kept for continuity.
(b) Context model: year effects + log GDP + malaria + fertility + urbanisation + basic sanitation + UNICEF sub-region + terrain (Nunn–Puga),
    the ranking the team's Decided Flow asked for ("control for context"); residuals averaged over the recent window.
(c) The fixed-effects country effect net of income and policy, for comparison.
(d) Policy record of the two tails of the context ranking: means with Mann-Whitney tests, GFDx status, and the dated
    stock of anaemia policies at five points in time (the "what do they do differently" beat).
Writes residuals_by_country.csv, deviants_policy_stock.csv, deviant_contrast.csv, deviants_timeline.csv, stats/04_residuals.json.
"""

from __future__ import annotations

import re
import sys

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import mannwhitneyu

import config as cfg
from util import cluster_groups, load_frame, save_stats, window

TIMELINE_YEARS = [2005, 2010, 2015, 2020, 2023]


def country_effects(dA: pd.DataFrame, y: str, main_x: str) -> pd.Series:
    fe = smf.ols(f"{y} ~ C(iso3) + C(year) + {main_x} + {cfg.LOG_INCOME}", data=dA).fit()
    eff = {}
    for name, val in fe.params.items():
        m = re.fullmatch(r"C\(iso3\)\[T\.(\w+)\]", name)
        if m:
            eff[m.group(1)] = float(val)
    eff[sorted(dA["iso3"].unique())[0]] = 0.0
    s = pd.Series(eff)
    return (s - s.mean()).rename("country_effect_fe")


def recent_residual(d: pd.DataFrame, resid_col: str, y: str, name: str) -> pd.DataFrame:
    recent = d[d["year"].between(cfg.RECENT_FROM, cfg.YEAR_MAX)]
    rec = recent.groupby("iso3").agg(**{name: (resid_col, "mean"), f"n_years_{name}": (resid_col, "size")})
    rec.loc[rec[f"n_years_{name}"] < cfg.MIN_YEARS_RECENT, name] = np.nan
    return rec


def contrast(pos: pd.DataFrame, und: pd.DataFrame, label: str) -> list[dict]:
    out = []
    for c in cfg.POLICY_ALL:
        col = c + "_mean_recent"
        a, b = pos[col].dropna(), und[col].dropna()
        p = float(mannwhitneyu(a, b).pvalue) if a.nunique() + b.nunique() > 2 else None
        out.append(
            dict(
                ranking=label,
                composite=c,
                positive_deviant_mean=float(a.mean()),
                under_performer_mean=float(b.mean()),
                n_positive=int(len(a)),
                n_under=int(len(b)),
                mannwhitney_p=p,
            )
        )
    return out


def main() -> None:
    df = window(load_frame())
    y, main_x = cfg.OUTCOME, f"{cfg.POLICY_MAIN}_lag{cfg.LAG}"
    events = pd.read_csv(cfg.EVENTS_CSV)
    geo = events.set_index("iso3")[[c for c in cfg.GEOGRAPHY if c in events.columns]]
    d = df.dropna(subset=[y, cfg.LOG_INCOME]).copy()

    # (a) income-only
    inc = smf.ols(f"{y} ~ C(year) + {cfg.LOG_INCOME}", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": cluster_groups(d)}
    )
    d["resid_income"] = inc.resid
    rec_inc = recent_residual(d, "resid_income", y, "resid_income_recent")

    # (b) context model
    dc = df.merge(geo, left_on="iso3", right_index=True, how="left")
    ctx_cols = [cfg.LOG_INCOME] + cfg.CONTEXT + cfg.RANKING_EXTRA + [c for c in cfg.GEOGRAPHY if c in dc.columns]
    dc = dc.dropna(subset=[y] + ctx_cols).copy()
    fml = f"{y} ~ C(year) + C(subregion) + " + " + ".join(ctx_cols)
    ctx = smf.ols(fml, data=dc).fit(cov_type="cluster", cov_kwds={"groups": cluster_groups(dc)})
    dc["resid_context"] = ctx.resid
    rec_ctx = recent_residual(dc, "resid_context", y, "resid_context_recent")

    level_all = (
        df[df["year"].between(cfg.RECENT_FROM, cfg.YEAR_MAX)]
        .groupby("iso3")[y]
        .mean()
        .rename("anaemia_mean_recent_all")
    )
    dA = df.dropna(subset=[y, cfg.LOG_INCOME, main_x]).copy()
    ce = country_effects(dA, y, main_x)
    latest = (
        df[df["year"] == cfg.YEAR_MAX]
        .set_index("iso3")[["country", y, cfg.INCOME]]
        .rename(columns={y: f"anaemia_{cfg.YEAR_MAX}", cfg.INCOME: f"gdp_pc_{cfg.YEAR_MAX}"})
    )
    pol = (
        df[df["year"].between(cfg.RECENT_FROM, cfg.YEAR_MAX)]
        .groupby("iso3")[cfg.POLICY_ALL]
        .mean()
        .add_suffix("_mean_recent")
    )
    full = d.groupby("iso3")["resid_income"].mean().rename("resid_income_full")
    R = latest.join([rec_inc, rec_ctx, full, level_all, ce, pol]).reset_index()
    R = R.rename(
        columns={"n_years_resid_income_recent": "n_years_recent", "n_years_resid_context_recent": "n_years_context"}
    )
    R["rank_income"] = R["resid_income_recent"].rank()
    R["rank_context"] = R["resid_context_recent"].rank()
    R["rank_level_recent"] = R["anaemia_mean_recent_all"].rank()
    ev_cols = ["first_anaemia_policy_year", "gfdx_wheat_mandate_year", "gfdx_wheat_mandate_status", "subregion"]
    R = R.merge(
        events[["iso3"] + [c for c in ev_cols if c in events.columns]], on="iso3", how="left", validate="one_to_one"
    )
    R = R.sort_values("resid_context_recent")
    R.to_csv(cfg.RESULTS / "residuals_by_country.csv", index=False)

    tails = {}
    contrasts = []
    for label, col in [("context", "resid_context_recent"), ("income", "resid_income_recent")]:
        ranked = R.dropna(subset=[col]).sort_values(col)
        pos = ranked.head(cfg.N_DEVIANTS).assign(group=f"positive deviant (below {label}-predicted level)")
        und = ranked.tail(cfg.N_DEVIANTS).assign(group=f"under-performer (above {label}-predicted level)")
        tails[label] = (ranked, pos, und)
        contrasts += contrast(pos, und, label)
    ranked, pos, und = tails["context"]
    pd.concat([pos, und]).assign(ranking="context").to_csv(cfg.RESULTS / "deviants_policy_stock.csv", index=False)
    pd.DataFrame(contrasts).to_csv(cfg.RESULTS / "deviant_contrast.csv", index=False)

    # (d) timelines: dated anaemia-policy stock of the two context tails at five points in time
    tl_rows = []
    for grp, block in [("positive deviant", pos), ("under-performer", und)]:
        for iso in block["iso3"]:
            s = df[df["iso3"] == iso].set_index("year")[cfg.POLICY_MAIN]
            row = dict(
                group=grp,
                iso3=iso,
                country=block.set_index("iso3").loc[iso, "country"],
                **{f"stock_{t}": float(s.get(t, np.nan)) for t in TIMELINE_YEARS},
            )
            ev = events.set_index("iso3").loc[iso]
            row.update(
                first_anaemia_policy_year=ev.get("first_anaemia_policy_year"),
                wheat_mandate_year=ev.get("gfdx_wheat_mandate_year"),
                wheat_mandate_status=ev.get("gfdx_wheat_mandate_status"),
            )
            tl_rows.append(row)
    TL = pd.DataFrame(tl_rows)
    TL.to_csv(cfg.RESULTS / "deviants_timeline.csv", index=False)

    rho_ctx_level = float(
        ranked[["resid_context_recent", "anaemia_mean_recent_all"]].corr(method="spearman").iloc[0, 1]
    )
    both = R.dropna(subset=["resid_context_recent", "resid_income_recent"])
    rho_ctx_inc = float(both[["resid_context_recent", "resid_income_recent"]].corr(method="spearman").iloc[0, 1])
    rho_ctx_fe = float(both[["resid_context_recent", "country_effect_fe"]].corr(method="spearman").iloc[0, 1])
    inc_ranked = tails["income"][0]
    rho_inc_level = float(
        inc_ranked[["resid_income_recent", "anaemia_mean_recent_all"]].corr(method="spearman").iloc[0, 1]
    )
    by_level = ranked.sort_values("anaemia_mean_recent_all")
    overlap_low = len(set(by_level.head(cfg.N_DEVIANTS)["iso3"]) & set(pos["iso3"]))
    overlap_high = len(set(by_level.tail(cfg.N_DEVIANTS)["iso3"]) & set(und["iso3"]))
    inc_pos, inc_und = tails["income"][1], tails["income"][2]
    excluded = R[R["resid_context_recent"].isna()][["iso3", "n_years_context"]]

    def listing(block: pd.DataFrame, col: str) -> list[dict]:
        return [
            dict(
                iso3=r.iso3,
                country=r.country,
                resid=round(float(getattr(r, col)), 1),
                level_recent=round(float(r.anaemia_mean_recent_all), 1),
                anaemia_latest=float(getattr(r, f"anaemia_{cfg.YEAR_MAX}")),
            )
            for r in block.itertuples()
        ]

    stats = dict(
        income_only=dict(
            coef_log_gdp=float(inc.params[cfg.LOG_INCOME]),
            se=float(inc.bse[cfg.LOG_INCOME]),
            r2=float(inc.rsquared),
            n=int(inc.nobs),
        ),
        context_model=dict(
            formula=fml,
            r2=float(ctx.rsquared),
            n=int(ctx.nobs),
            countries=int(dc["iso3"].nunique()),
            coefs={k: float(v) for k, v in ctx.params.items() if not k.startswith("C(year)")},
            pvalues={k: float(v) for k, v in ctx.pvalues.items() if not k.startswith("C(year)")},
        ),
        recent_window=[cfg.RECENT_FROM, cfg.YEAR_MAX],
        min_years_recent=cfg.MIN_YEARS_RECENT,
        n_ranked_context=int(len(ranked)),
        n_ranked_income=int(len(inc_ranked)),
        excluded_from_context_ranking={
            r.iso3: (None if pd.isna(r.n_years_context) else int(r.n_years_context)) for r in excluded.itertuples()
        },
        ranking_vs_level=dict(
            spearman_context_vs_level=rho_ctx_level,
            spearman_income_vs_level=rho_inc_level,
            spearman_context_vs_income=rho_ctx_inc,
            spearman_context_vs_fe_effect=rho_ctx_fe,
            positive_set_overlap_with_lowest_level=overlap_low,
            under_set_overlap_with_highest_level=overlap_high,
            n_each=cfg.N_DEVIANTS,
        ),
        positive_deviants=listing(pos, "resid_context_recent"),
        under_performers=listing(und, "resid_context_recent"),
        positive_deviants_income=listing(inc_pos, "resid_income_recent"),
        under_performers_income=listing(inc_und, "resid_income_recent"),
        tails_overlap_context_vs_income=dict(
            positive=len(set(pos["iso3"]) & set(inc_pos["iso3"])), under=len(set(und["iso3"]) & set(inc_und["iso3"]))
        ),
        policy_stock_contrast=contrasts,
        timeline=TL.to_dict("records"),
        latest_year=cfg.YEAR_MAX,
    )
    save_stats("04_residuals", stats)
    print(
        R[
            [
                "iso3",
                "country",
                f"anaemia_{cfg.YEAR_MAX}",
                "anaemia_mean_recent_all",
                "resid_income_recent",
                "resid_context_recent",
                "n_years_context",
            ]
        ]
        .round(1)
        .to_string()
    )
    print(
        f"\ncontext model R² {ctx.rsquared:.3f} (n {int(ctx.nobs)}, {dc['iso3'].nunique()} countries); Spearman(context resid, level) {rho_ctx_level:.3f}; "  # noqa: E501
        f"Spearman(context, income) {rho_ctx_inc:.3f}; tails overlap by level {overlap_low}/{cfg.N_DEVIANTS} and {overlap_high}/{cfg.N_DEVIANTS}"
    )
    print(pd.DataFrame(contrasts).round(3).to_string())


if __name__ == "__main__":
    sys.exit(main())
