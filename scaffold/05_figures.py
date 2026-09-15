"""05 — figures for the deck (PNG, results/figures/), v2.0: the dose ladder incl. lead test, trend, bracket and context
rows; the event studies; the specification curve; LOCO bars; calibration; the context ranking and its comparison with the
income-only ranking; choropleth (optional); anaemia small multiples. Deck-ready chrome (figstyle): a short bold headline,
one subtitle carrying the reading, one source footer, all wrapped inside a roughly 16:9 canvas at 200 dpi. Titles state
what was measured, never a direction the checks do not support."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config as cfg
import figstyle as fs
from util import load_stats, save_stats

EVENT_SHORT = {
    "anaemia_policy": "First dated anaemia policy (GIFNA)",
    "wheat_mandate": "Mandatory wheat-flour fortification (GFDx)",
}
EST_LABEL = {"twfe_event": "two-way FE", "did2s_event": "two-stage DiD", "lpdid_event": "local-projections DiD"}
EST_COLOUR = {"twfe_event": fs.INK2, "did2s_event": fs.BLUE, "lpdid_event": fs.ORANGE}
OUT = (
    Path(os.environ["FIG_OUT"]) if os.environ.get("FIG_OUT") else cfg.FIGS
)  # FIG_OUT + FIG_DECK=1: title-less deck copies
SHORT_NAMES = {
    "Democratic Republic of the Congo": "DR Congo",
    "United Republic of Tanzania": "Tanzania",
    "Central African Republic": "Central Afr. Rep.",
    "Sao Tome and Principe": "São Tomé & Príncipe",
    "Equatorial Guinea": "Eq. Guinea",
}


def coef_plot(rows, labels, colours, xlabel, title, subtitle, footer, path, size=(11.0, 6.8)) -> None:
    fig, ax = fs.new_fig(*size)
    ax.grid(axis="y", visible=False)
    ax.axvline(0, color=fs.INK, lw=0.9, zorder=1)
    for i, (r, col) in enumerate(zip(rows.itertuples(), colours, strict=True)):
        ax.plot([r.ci_low, r.ci_high], [i, i], color=col, lw=3, solid_capstyle="round", zorder=2)
        ax.plot(r.coef, i, "o", color=col, ms=9, mec=fs.SURFACE, mew=1.5, zorder=3)
    xmax = float(rows["ci_high"].max())
    for i, r in enumerate(rows.itertuples()):
        ax.text(
            xmax + 0.05,
            i,
            f"{r.coef:+.2f}   n = {r.n_obs:,}",
            va="center",
            fontsize=10,
            color=fs.INK2,
            family="monospace",
        )
    ax.set_xlim(float(rows["ci_low"].min()) - 0.05, xmax + 0.42)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(labels, fontsize=10.5, color=fs.INK)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel(xlabel, fontsize=11, color=fs.INK2)
    fs.finish(fig, path, title, subtitle, footer)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sens = pd.read_csv(cfg.RESULTS / "fe_sensitivity.csv").set_index("variant")
    loco = pd.read_csv(cfg.RESULTS / "loco_rmse.csv")
    P = pd.read_csv(cfg.RESULTS / "loco_predictions.csv")
    R = pd.read_csv(cfg.RESULTS / "residuals_by_country.csv")
    ES = pd.read_csv(cfg.RESULTS / "event_study.csv")
    SC = pd.read_csv(cfg.RESULTS / "spec_curve.csv")
    frame = pd.read_csv(cfg.FRAME_CSV)
    f1, f2, f2b, f2c, f4 = (load_stats(n) for n in ("01_frame", "02_fe", "02b_event", "02c_spec", "04_residuals"))
    es = f1["estimation_sample"]
    sample = f"{es['countries']} countries, {es['years'][0]}–{es['years'][1]}"
    src = (
        "Sources: WHO 2025 anaemia estimates, women 15–49 (GHO 4552 via FAOSTAT FS); WHO GIFNA registry; GFDx; World Bank. "
        f"Scaffold {cfg.SCAFFOLD_VERSION}, {cfg.RUN_DATE}, data version {cfg.data_version()}. Association within countries, not causation."
    )
    written = {}

    # fig 1 — the dose ladder
    keep = [
        "A_main",
        "lag2",
        "lag5",
        "income_current_usd",
        "lead_test_only",
        "trend_main",
        "fd",
        f"longdiff{cfg.LONG_DIFF}",
        "ldv",
        "ctx_all",
        "team_unemployment",
        "impl_sth",
        "survey_anchored",
    ]
    names = {
        "A_main": f"Main: two-way FE, policy lagged {cfg.LAG} y",
        "lag2": "   policy lagged 2 y",
        "lag5": "   policy lagged 5 y",
        "income_current_usd": "   income in current US$",
        "lead_test_only": "Lead test: policy 3 y later",
        "trend_main": "Main + country trends",
        "fd": "First differences",
        f"longdiff{cfg.LONG_DIFF}": f"{cfg.LONG_DIFF}-year differences",
        "ldv": "Lagged outcome, no country FE",
        "ctx_all": "Main + malaria, fertility, urban",
        "team_unemployment": "Main + unemployment",
        "impl_sth": "Deworming coverage as exposure",
        "survey_anchored": "Survey-anchored years only",
    }
    keep = [k for k in keep if k in sens.index]
    s = sens.loc[keep].reset_index().iloc[::-1]
    col_by_block = {
        "main": fs.INK2,
        "lead_test": fs.DEEMPH,
        "trend": fs.DEEMPH,
        "bracket": fs.BLUE,
        "context": fs.AQUA,
        "team": fs.AQUA,
        "implementation": fs.AQUA,
        "anchor": fs.ORANGE,
    }
    b = f2["bounds"]
    coef_plot(
        s,
        [names[v] for v in s["variant"]],
        [col_by_block.get(bk, fs.INK2) for bk in s["block"]],
        "change in anaemia (percentage points) per active anaemia policy, with 95% interval",
        "Policy dose ladder: every row straddles zero",
        f"Anaemia in women 15–49 against anaemia-cluster policies in force three years earlier, {sample}. "
        f"Effects beyond {b['sesoi_pp_per_within_sd']:.0f} pp per within-country SD of the dose are ruled out (TOST p = {b['tost_p']:.3f}). "
        "Grey: dynamics checks · blue: fixed-effects vs lagged-outcome bracket · green: context and team controls · "
        "orange: survey-anchored rows only.",
        src,
        OUT / "fig_sensitivity.png",
    )
    written["fig_sensitivity"] = (
        "the dose ladder: main, lags, lead test, trends, bracket, context, team and survey-anchored rows"
    )

    # fig 2 — event studies
    ests = [e for e in EST_LABEL if e in set(ES["estimator"])]
    fig, axes = plt.subplots(1, len(cfg.EVENTS), figsize=(12.5, 6.4), sharey=True)
    fig.patch.set_facecolor(fs.SURFACE)
    axes = np.atleast_1d(axes)
    for ax, name in zip(axes, cfg.EVENTS, strict=True):
        fs.style_ax(ax)
        ax.axhline(0, color=fs.INK, lw=0.9)
        ax.axvline(-0.5, color=fs.BASE, lw=1, ls="--")
        for j, e in enumerate(ests):
            sub = ES[(ES["event"] == name) & (ES["estimator"] == e)].dropna(subset=["k"]).sort_values("k")
            if sub.empty:
                continue
            off = (j - (len(ests) - 1) / 2) * 0.2
            ax.errorbar(
                sub["k"] + off,
                sub["coef"],
                yerr=[sub["coef"] - sub["ci_low"], sub["ci_high"] - sub["coef"]],
                fmt="o",
                ms=5,
                color=EST_COLOUR[e],
                ecolor=EST_COLOUR[e],
                elinewidth=1.4,
                capsize=2.5,
                label=EST_LABEL[e],
            )
        info = f2b["events"][name]["info"]
        st = f2b["events"][name]["twfe_static"]
        ax.set_title(
            f"{EVENT_SHORT.get(name, name)}\n"
            f"{info['treated_countries']} adopters, {info['never_treated_countries']} never-adopters\n"
            f"static two-way FE ATT {st['att']:+.2f} pp (p {st['p']:.2f}) · {st['share_negative_weight']:.0%} negative weights",
            fontsize=10.5,
            color=fs.INK,
            loc="left",
            linespacing=1.4,
        )
        ax.set_xlabel("years since adoption (reference: the year before)", fontsize=11, color=fs.INK2)
        ax.set_xticks(range(-cfg.ES_PRE, cfg.ES_POST + 1))
        ax.legend(fontsize=10, frameon=False, loc="lower left")
    axes[0].set_ylabel("change in anaemia (percentage points)", fontsize=11, color=fs.INK2)
    rd = f2b["events"]
    ap, wm = rd.get("anaemia_policy", {}), rd.get("wheat_mandate", {})
    nan = float("nan")
    slope = ap.get("twfe_event_pretrend", {}).get("slope", nan)
    d2, lp = ap.get("did2s_static", {}).get("att", nan), ap.get("lpdid_att", {}).get("att", nan)
    wd = wm.get("did2s_static", {})
    fs.finish(
        fig,
        OUT / "fig_event_study.png",
        "Event studies around adoption: three estimators, no robust break",
        "Two-way FE shows a post-adoption decline after the first anaemia policy, but the pre-period slopes the same way "
        f"({slope:+.2f} pp per year) and the two estimators built for staggered adoption sit at zero "
        f"(two-stage DiD {d2:+.2f} pp, local projections {lp:+.2f} pp). The wheat-flour mandate shows no pre-trend and "
        f"no break (two-stage DiD {wd.get('att', nan):+.2f} pp, p {wd.get('p', nan):.2f}). "
        "Bins at the window ends; never- and not-yet-adopters are the comparison group.",
        src,
    )
    written["fig_event_study"] = (
        "event studies around the first anaemia policy and the wheat-flour mandate (three estimators)"
    )

    # fig 3 — specification curve
    fig, ax = fs.new_fig(11.0, 5.6)
    colours_e = {"fe": fs.INK2, "fe_trend": fs.DEEMPH, "fd": fs.BLUE, "ldv": fs.ORANGE}
    est_names = {
        "fe": "two-way FE",
        "fe_trend": "FE + country trends",
        "fd": "first differences",
        "ldv": "lagged outcome",
    }
    for e, col in colours_e.items():
        sub = SC[SC["estimator"] == e]
        ax.vlines(sub["spec_id"], sub["ci_low"], sub["ci_high"], color=col, lw=0.7, alpha=0.6)
        ax.plot(sub["spec_id"], sub["coef_per_within_sd"], "o", ms=3, color=col, label=est_names[e])
    ax.axhline(0, color=fs.INK, lw=0.9)
    ax.set_xlabel("specifications, sorted by estimate", fontsize=11, color=fs.INK2)
    ax.set_ylabel("pp of anaemia per within-country SD of exposure", fontsize=11, color=fs.INK2)
    ax.legend(fontsize=10, frameon=False, ncol=4, loc="upper left")
    be = f2c["by_estimator"]
    others = max((v["share_excludes_zero"] for k, v in be.items() if k != "fe_trend"), default=0.0)
    tail = "."
    if "fe_trend" in be:
        tail = f" (FE + country trends {be['fe_trend']['share_excludes_zero']:.0%}, all others at most {others:.0%})."
    fs.finish(
        fig,
        OUT / "fig_spec_curve.png",
        f"Specification curve: {f2c['n_specs']} specifications, median {f2c['median_pp_per_within_sd']:+.2f} pp",
        "Exposure construction × estimator × income measure × lag × control set, all pre-specified. The 95% interval "
        f"excludes zero in {f2c['share_ci_excludes_zero']:.0%} of specifications" + tail,
        src,
    )
    written["fig_spec_curve"] = "specification curve over exposure × estimator × income × lag × controls"

    # fig 4 — LOCO RMSE bars
    names3 = {
        "naive_flat": "flat at own mean",
        "M0_year_effects": "year effects only",
        "M1_income": "+ income",
        "M2_income_policy": "+ policy dose (main)",
        "M2t_income_team_composite": "+ team composite instead",
        "M3_income_all_exposures": "+ all exposures",
    }
    fig, ax = fs.new_fig(10.0, 5.0)
    yy = np.arange(len(loco))
    ax.barh(
        yy,
        loco["rmse"],
        color=[fs.BLUE if "policy" in m or "composite" in m or "exposures" in m else fs.DEEMPH for m in loco["model"]],
        height=0.6,
    )
    for i, r in enumerate(loco.itertuples()):
        ax.text(r.rmse + 0.03, i, f"{r.rmse:.2f}", va="center", fontsize=10.5, color=fs.INK2, family="monospace")
    ax.set_yticks(yy)
    ax.set_yticklabels([names3.get(m, m) for m in loco["model"]], fontsize=11, color=fs.INK)
    ax.invert_yaxis()
    ax.set_xlim(0, float(loco["rmse"].max()) * 1.15)
    ax.set_xlabel("leave-one-country-out RMSE of the within-country anaemia path (pp)", fontsize=11, color=fs.INK2)
    ax.grid(axis="y", visible=False)
    fs.finish(
        fig,
        OUT / "fig_loco.png",
        "Held-out prediction: adding the policy dose does not lower the error",
        "Each country is predicted by a model that never saw it (blue: models with an exposure). Common sample across models; "
        "year effects transferred from the training countries.",
        src,
    )
    written["fig_loco"] = "leave-one-country-out RMSE by nested model"

    # fig 5 — calibration
    m2 = P[P["model"] == "M2_income_policy"]
    fig, ax = fs.new_fig(7.2, 7.0)
    lim = float(np.nanmax(np.abs(np.concatenate([m2["obs_dev"], m2["pred_dev"]])))) * 1.05
    ax.plot([-lim, lim], [-lim, lim], color=fs.BASE, lw=1)
    ax.scatter(m2["pred_dev"], m2["obs_dev"], s=18, color=fs.BLUE, alpha=0.55, edgecolor=fs.SURFACE, linewidth=0.5)
    rr = float(np.corrcoef(m2["obs_dev"], m2["pred_dev"])[0, 1])
    ax.set_xlabel("predicted deviation from own mean (pp)", fontsize=11, color=fs.INK2)
    ax.set_ylabel("observed deviation from own mean (pp)", fontsize=11, color=fs.INK2)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    fs.finish(
        fig,
        OUT / "fig_calibration.png",
        f"Held-out vs observed deviations (r = {rr:.2f})",
        "Income + policy model, leave one country out; one point per country-year. The year effects do most of the work.",
        src,
    )
    written["fig_calibration"] = "LOCO calibration scatter for the income + policy model"

    # fig 6 — context ranking
    rl, cm = f4["ranking_vs_level"], f4["context_model"]
    r6 = R.dropna(subset=["resid_context_recent"]).sort_values("resid_context_recent")
    fig, ax = fs.new_fig(9.0, 11.5)
    yy = np.arange(len(r6))
    ax.axvline(0, color=fs.INK, lw=0.9)
    vals = r6["resid_context_recent"].to_numpy()
    ax.scatter(
        vals,
        yy,
        s=44,
        c=[fs.BLUE if v < 0 else fs.ORANGE for v in vals],
        edgecolor=fs.SURFACE,
        linewidth=1,
        zorder=3,
    )
    ax.hlines(yy, 0, vals, color=fs.GRID, lw=1.2, zorder=2)
    for y, v in zip(yy, vals, strict=True):
        ax.text(
            v + (0.35 if v >= 0 else -0.35),
            y,
            f"{v:+.1f}",
            va="center",
            ha="left" if v >= 0 else "right",
            fontsize=8.5,
            color=fs.INK2,
        )
    ax.set_yticks(yy)
    ax.set_yticklabels(r6["country"], fontsize=9.5, color=fs.INK)
    ax.set_ylim(-0.8, len(r6) - 0.2)
    lim6 = float(np.abs(vals).max()) * 1.25
    ax.set_xlim(-lim6, lim6)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(
        f"anaemia minus the context-predicted level, mean {cfg.RECENT_FROM}–{cfg.YEAR_MAX} (percentage points)",
        fontsize=11,
        color=fs.INK2,
    )
    fs.finish(
        fig,
        OUT / "fig_residuals.png",
        f"Who beats their context (R² {cm['r2']:.2f}, {cm['countries']} countries ranked)",
        "Blue: anaemia lower than income, malaria, fertility, urbanisation, sanitation, sub-region and terrain predict; "
        f"orange: higher. Cross-country model with year effects; countries with fewer than {cfg.MIN_YEARS_RECENT} window years "
        "or a missing series are not ranked. A screening device, not a verdict.",
        src,
    )
    written["fig_residuals"] = "context ranking (residual from the context model), recent window"

    # fig 7 — income-only vs context ranking
    both = R.dropna(subset=["resid_income_recent", "resid_context_recent"])
    fig, ax = fs.new_fig(8.5, 6.8)
    ax.axhline(0, color=fs.INK, lw=0.9)
    ax.axvline(0, color=fs.INK, lw=0.9)
    ax.scatter(
        both["resid_income_recent"],
        both["resid_context_recent"],
        s=34,
        color=fs.BLUE,
        edgecolor=fs.SURFACE,
        linewidth=0.6,
        zorder=3,
    )
    for r in both.itertuples():
        ax.text(r.resid_income_recent + 0.3, r.resid_context_recent, r.iso3, fontsize=8.5, color=fs.INK2, va="center")
    ax.set_xlabel("residual from the income-only model (pp)", fontsize=11, color=fs.INK2)
    ax.set_ylabel("residual from the context model (pp)", fontsize=11, color=fs.INK2)
    fs.finish(
        fig,
        OUT / "fig_rankings_compare.png",
        f"Income-only vs context ranking: loose agreement (Spearman {rl['spearman_context_vs_income']:.2f})",
        f"Residual anaemia, mean {cfg.RECENT_FROM}–{cfg.YEAR_MAX}, one point per country. Income alone explains "
        f"{f4['income_only']['r2']:.0%} of the level differences, the context model {cm['r2']:.0%}.",
        src,
    )
    written["fig_rankings_compare"] = "income-only vs context residuals, one point per country"

    # fig 8 — choropleth (optional)
    map_path = OUT / "fig_map.png"
    map_path.unlink(missing_ok=True)
    try:
        import plotly.express as px
    except ImportError as e:
        print("choropleth skipped (plotly missing):", e)
    else:
        try:
            m = R.dropna(subset=["resid_context_recent"])
            v = float(m["resid_context_recent"].abs().max())
            fig8 = px.choropleth(
                m,
                locations="iso3",
                color="resid_context_recent",
                scope="africa",
                color_continuous_scale=[[0, fs.BLUE], [0.5, fs.ABSENT], [1, fs.ORANGE]],
                range_color=[-v, v],
                hover_name="country",
                labels={"resid_context_recent": "pp vs predicted"},
            )
            fig8.update_layout(
                title=dict(
                    text=("" if fs.DECK else "<b>Anaemia vs the context-predicted level</b><br>")
                    + f"<sup>mean {cfg.RECENT_FROM}–{cfg.YEAR_MAX}, percentage points; "
                    "blue = lower than predicted, grey = not ranked</sup>",
                    font=dict(size=22, color=fs.INK, family="Helvetica Neue, Arial"),
                    x=0.02,
                ),
                font=dict(family="Helvetica Neue, Arial", size=14, color=fs.INK2),
                paper_bgcolor=fs.SURFACE,
                geo=dict(bgcolor=fs.SURFACE, showframe=False, lakecolor=fs.SURFACE, landcolor=fs.ABSENT, showland=True),
                margin=dict(l=10, r=10, t=90, b=40),
                width=1200,
                height=1000,
                coloraxis_colorbar=dict(title="pp", thickness=14, len=0.6),
                annotations=[
                    dict(
                        text=src.replace(" Scaffold", "<br>Scaffold"),
                        x=0.0,
                        y=-0.03,
                        xref="paper",
                        yref="paper",
                        showarrow=False,
                        xanchor="left",
                        font=dict(size=10, color=fs.MUTED),
                    )
                ],
            )
            fig8.write_image(str(map_path), width=1200, height=1000, scale=2)
            written["fig_map"] = "choropleth of the context ranking (plotly/kaleido)"
            print("figure →", map_path)
        except Exception as e:
            print("choropleth skipped:", type(e).__name__, e)

    # fig 9 — anaemia small multiples
    w = frame[(frame["year"] >= cfg.YEAR_MIN) & (frame["year"] <= cfg.YEAR_MAX)].pivot(
        index="year", columns="iso3", values=cfg.OUTCOME
    )
    names7 = frame.drop_duplicates("iso3").set_index("iso3")["country"]
    cols7 = sorted(w.columns, key=lambda c: -w[c].iloc[-1] if pd.notna(w[c].iloc[-1]) else 0)
    n, nc = len(cols7), 10
    nr = int(np.ceil(n / nc))
    fig, axes = plt.subplots(nr, nc, figsize=(14.0, 1.55 * nr + 1.6), sharex=True, sharey=True)
    fig.patch.set_facecolor(fs.SURFACE)
    for ax, c in zip(axes.flat, cols7, strict=False):
        fs.style_ax(ax)
        ax.plot(w.index, w[c], color=fs.BLUE, lw=1.7)
        label = SHORT_NAMES.get(names7[c], names7[c])
        ax.text(0.05, 0.88, label[:18], transform=ax.transAxes, fontsize=8.5, color=fs.INK, va="center")
        ax.text(
            0.95,
            0.72,
            f"{w[c].iloc[-1]:.0f}%",
            transform=ax.transAxes,
            fontsize=8.5,
            color=fs.INK2,
            ha="right",
            va="center",
        )
        ax.set_xticks([cfg.YEAR_MIN, cfg.YEAR_MAX])
        ax.set_ylim(8, 78)
        ax.set_yticks([20, 40, 60])
        ax.tick_params(labelsize=7.5)
    for ax in list(axes.flat)[n:]:
        ax.axis("off")
    fs.finish(
        fig,
        OUT / "fig_trends_anaemia.png",
        f"Anaemia in women 15–49, {cfg.YEAR_MIN}–{cfg.YEAR_MAX}, all {n} countries",
        f"One panel per country, sorted by the {cfg.YEAR_MAX} level; the number is the {cfg.YEAR_MAX} prevalence in %. "
        "Shared axes: the y-axis is the same in every panel.",
        src,
    )
    written["fig_trends_anaemia"] = f"anaemia small multiples, {n} countries"
    if OUT == cfg.FIGS:
        save_stats("05_figures", dict(figures=written))


if __name__ == "__main__":
    sys.exit(main())
