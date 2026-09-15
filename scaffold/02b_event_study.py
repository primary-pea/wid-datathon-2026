"""02b — event studies (v2.0) around dated events: the first anaemia-cluster policy in the GIFNA policies file and the
year mandatory wheat-flour fortification was legislated (GFDx). Estimators: a binned two-way-FE event study, Gardner's
two-stage DiD and the local-projections DiD of Dube et al. (both via pyfixest), a static TWFE row with the
de Chaisemartin–D'Haultfœuille negative-weight diagnostic, and a pre-trend slope adjustment as a transparent
sensitivity. Countries treated before the window has two pre-years are dropped from the event sample (reported);
never-treated countries are the comparison group together with the not-yet-treated.
Writes results/event_study.csv, event_att.csv and stats/02b_event.json.
"""

from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

import config as cfg
from util import load_frame, save_stats, two_way_residualize, window

warnings.filterwarnings("ignore")


def rel_bins() -> list[int]:
    return [k for k in range(-cfg.ES_PRE, cfg.ES_POST + 1) if k != cfg.ES_REF]


def dname(k: int) -> str:
    return f"D_m{abs(k)}" if k < 0 else f"D_p{k}"


def event_frame(df: pd.DataFrame, events: pd.DataFrame, col: str) -> tuple[pd.DataFrame, dict]:
    g = events.set_index("iso3")[col]
    d = df.copy()
    d["g"] = d["iso3"].map(g)
    already = sorted(d.loc[d["g"] < cfg.YEAR_MIN + 2, "iso3"].unique())  # no usable pre-period
    d = d[~d["iso3"].isin(already)].copy()
    d.loc[d["g"] > cfg.YEAR_MAX, "g"] = np.nan  # legislated after the window: never treated within it
    d["never"] = d["g"].isna().astype(int)
    d["rel"] = d["year"] - d["g"]
    d["post"] = ((d["rel"] >= 0) & d["g"].notna()).astype(int)
    for k in rel_bins():
        if k == -cfg.ES_PRE:
            d[dname(k)] = ((d["rel"] <= k) & d["g"].notna()).astype(int)
        elif k == cfg.ES_POST:
            d[dname(k)] = ((d["rel"] >= k) & d["g"].notna()).astype(int)
        else:
            d[dname(k)] = (d["rel"] == k).astype(int)
    d["gname"] = d["g"].fillna(0).astype(int)  # pyfixest lpdid: 0 = never treated
    info = dict(
        dropped_already_treated=already,
        treated_countries=int(d.loc[d["g"].notna(), "iso3"].nunique()),
        never_treated_countries=int(d.loc[d["g"].isna(), "iso3"].nunique()),
        cohorts={
            int(k): int(v)
            for k, v in d.drop_duplicates("iso3")["g"].dropna().astype(int).value_counts().sort_index().items()
        },
    )
    return d, info


def tidy_rows(tidy: pd.DataFrame, event: str, estimator: str, n: int) -> list[dict]:
    rows = []
    for term, r in tidy.iterrows():
        rows.append(
            dict(
                event=event,
                estimator=estimator,
                term=str(term),
                coef=float(r["Estimate"]),
                se=float(r["Std. Error"]),
                ci_low=float(r["2.5%"]),
                ci_high=float(r["97.5%"]),
                p=float(r["Pr(>|t|)"]),
                n_obs=n,
            )
        )
    return rows


def k_of(term: str) -> float:
    if term.startswith("D_m"):
        return -int(term[3:])
    if term.startswith("D_p"):
        return int(term[3:])
    return np.nan


def pretrend_adjust(rows: pd.DataFrame) -> dict:
    """Fit a line through the interior pre-period coefficients and subtract its extrapolation from the post period."""
    pre = rows[(rows["k"] < cfg.ES_REF) & (rows["k"] > -cfg.ES_PRE)]
    post = rows[(rows["k"] >= 0) & (rows["k"] < cfg.ES_POST)]
    if len(pre) < 2 or post.empty:
        return dict(
            slope=np.nan, post_mean=float(post["coef"].mean()) if not post.empty else np.nan, post_mean_adjusted=np.nan
        )
    slope = float(np.polyfit(pre["k"], pre["coef"], 1)[0])
    adj = post["coef"] - slope * (post["k"] - cfg.ES_REF)
    return dict(slope=slope, post_mean=float(post["coef"].mean()), post_mean_adjusted=float(adj.mean()))


def negative_weights(d: pd.DataFrame) -> dict:
    """de Chaisemartin & D'Haultfœuille (2020) weights of the static TWFE coefficient on a binary treatment."""
    dd = two_way_residualize(d.dropna(subset=[cfg.OUTCOME, cfg.LOG_INCOME]), ["post"])
    eps = dd["post_dm"].to_numpy()
    w = dd["post"].to_numpy() * eps
    if w.sum() == 0:
        return dict(share_negative_weight=np.nan, n_negative=0, n_treated_cells=int(dd["post"].sum()))
    w = w / w.sum()
    return dict(
        share_negative_weight=float(-w[w < 0].sum()),
        n_negative=int((w < 0).sum()),
        n_treated_cells=int(dd["post"].sum()),
    )


def did2s_manual(d: pd.DataFrame, y: str, inc: str, dums: list[str], B: int = 299, seed: int = 1):
    """Two-stage DiD (Gardner 2022; Borusyak, Jaravel & Spiess 2024 imputation logic) with a country cluster bootstrap."""

    def two_stage(dd: pd.DataFrame) -> tuple[dict, float]:
        un = (dd["post"] == 0).to_numpy()
        keep_c, keep_y = set(dd.loc[un, "iso3"]), set(dd.loc[un, "year"])
        dd = dd[dd["iso3"].isin(keep_c) & dd["year"].isin(keep_y)].reset_index(
            drop=True
        )  # units/years never untreated cannot be imputed
        un = (dd["post"] == 0).to_numpy()
        Xc = pd.get_dummies(dd["iso3"]).astype(float).to_numpy()
        Xy = pd.get_dummies(dd["year"].astype(int), drop_first=True).astype(float).to_numpy()
        X1 = np.column_stack([Xc, Xy, dd[inc].to_numpy(dtype=float)])
        b1 = np.linalg.lstsq(X1[un], dd.loc[un, y].to_numpy(dtype=float), rcond=None)[0]
        ytil = dd[y].to_numpy(dtype=float) - X1 @ b1
        X = np.column_stack([np.ones(len(dd))] + [dd[c].to_numpy(dtype=float) for c in dums])
        b = np.linalg.lstsq(X, ytil, rcond=None)[0]
        Xs = np.column_stack([np.ones(len(dd)), dd["post"].to_numpy(dtype=float)])
        bs = np.linalg.lstsq(Xs, ytil, rcond=None)[0]
        return dict(zip(dums, b[1:], strict=True)), float(bs[1])

    coef, static = two_stage(d)
    rng = np.random.default_rng(seed)
    countries = sorted(d["iso3"].unique())
    draws_es, draws_st = {k: [] for k in dums}, []
    for _ in range(B):
        pick = rng.choice(countries, size=len(countries), replace=True)
        boot = pd.concat([d[d["iso3"] == c].assign(iso3=f"{c}_{i}") for i, c in enumerate(pick)], ignore_index=True)
        try:
            ce, cs = two_stage(boot)
        except Exception:
            continue
        for k in dums:
            draws_es[k].append(ce[k])
        draws_st.append(cs)
    ci = {k: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) for k, v in draws_es.items()}
    st_se = float(np.std(draws_st, ddof=1))
    st_ci = (float(np.percentile(draws_st, 2.5)), float(np.percentile(draws_st, 97.5)))
    from scipy.stats import norm

    st_p = float(2 * (1 - norm.cdf(abs(static) / st_se))) if st_se > 0 else np.nan
    return coef, ci, static, st_ci, st_se, st_p


def main() -> None:
    import pyfixest as pf

    df = window(load_frame())
    events = pd.read_csv(cfg.EVENTS_CSV)
    y, inc = cfg.OUTCOME, cfg.LOG_INCOME
    all_rows, att_rows, stats = [], [], {}
    for name, spec in cfg.EVENTS.items():
        d, info = event_frame(df, events, spec["column"])
        d = d.dropna(subset=[y, inc]).copy()
        n = int(len(d))
        dums = [dname(k) for k in rel_bins()]
        est: dict = dict(info=info, n_obs=n, n_countries=int(d["iso3"].nunique()))

        # 1. binned TWFE event study
        fml = f"{y} ~ {' + '.join(dums)} + {inc} | iso3 + year"
        f_twfe = pf.feols(fml, data=d, vcov={"CRV1": "iso3"})
        rows = tidy_rows(f_twfe.tidy().loc[dums], name, "twfe_event", n)
        all_rows += rows
        # 2. static TWFE + negative-weight diagnostic
        f_static = pf.feols(f"{y} ~ post + {inc} | iso3 + year", data=d, vcov={"CRV1": "iso3"})
        st = f_static.tidy().loc["post"]
        att_rows.append(
            dict(
                event=name,
                estimator="twfe_static",
                att=float(st["Estimate"]),
                se=float(st["Std. Error"]),
                ci_low=float(st["2.5%"]),
                ci_high=float(st["97.5%"]),
                p=float(st["Pr(>|t|)"]),
                n_obs=n,
            )
        )
        est["twfe_static"] = dict(
            att=float(st["Estimate"]), se=float(st["Std. Error"]), p=float(st["Pr(>|t|)"]), **negative_weights(d)
        )

        # 3. Gardner two-stage DiD, implemented directly: stage 1 fits country and year effects (and log income) on the
        #    untreated observations only; stage 2 regresses the residualized outcome on the event dummies. Standard errors
        #    from a cluster bootstrap by country (both stages re-estimated in every draw), which carries the first-stage
        #    uncertainty that a naive second-stage SE would drop.
        try:
            es_coef, es_ci, st_coef, st_ci, st_se, st_p = did2s_manual(d, y, inc, dums, B=299, seed=cfg.SEED)
            for k_name, c in es_coef.items():
                all_rows.append(
                    dict(
                        event=name,
                        estimator="did2s_event",
                        term=k_name,
                        coef=c,
                        se=float((es_ci[k_name][1] - es_ci[k_name][0]) / (2 * 1.96)),
                        ci_low=es_ci[k_name][0],
                        ci_high=es_ci[k_name][1],
                        p=np.nan,
                        n_obs=n,
                    )
                )
            att_rows.append(
                dict(
                    event=name,
                    estimator="did2s_static",
                    att=st_coef,
                    se=st_se,
                    ci_low=st_ci[0],
                    ci_high=st_ci[1],
                    p=st_p,
                    n_obs=n,
                )
            )
            est["did2s_static"] = dict(att=st_coef, se=st_se, p=st_p, ci=list(st_ci), bootstrap_draws=299)
        except Exception as e:
            est["did2s_error"] = f"{type(e).__name__}: {e}"[:300]
            print("did2s failed:", est["did2s_error"])

        # 4. local-projections DiD (Dube, Girardi, Jordà & Taylor), clean controls, never-treated = 0
        try:
            d_lp = d.copy()
            d_lp["iso_id"] = pd.factorize(d_lp["iso3"])[0]
            f_lp = pf.lpdid(
                data=d_lp,
                yname=y,
                idname="iso_id",
                tname="year",
                gname="gname",
                vcov={"CRV1": "iso_id"},
                pre_window=-cfg.ES_PRE,
                post_window=cfg.ES_POST,
                never_treated=0,
                att=False,
                xfml=inc,
            )
            tl = f_lp.tidy()
            est["lpdid_terms"] = [str(i) for i in tl.index][:20]
            for term, r in tl.iterrows():
                k = (
                    int(float(str(term).replace("time_to_treatment::", "").replace("rel_year::", "")))
                    if any(ch.isdigit() for ch in str(term))
                    else np.nan
                )
                all_rows.append(
                    dict(
                        event=name,
                        estimator="lpdid_event",
                        term=str(term),
                        coef=float(r["Estimate"]),
                        se=float(r["Std. Error"]),
                        ci_low=float(r["2.5%"]),
                        ci_high=float(r["97.5%"]),
                        p=float(r["Pr(>|t|)"]),
                        n_obs=int(r["N"]) if "N" in r else n,
                        k=k,
                    )
                )
            f_lpa = pf.lpdid(
                data=d_lp,
                yname=y,
                idname="iso_id",
                tname="year",
                gname="gname",
                vcov={"CRV1": "iso_id"},
                pre_window=-cfg.ES_PRE,
                post_window=cfg.ES_POST,
                never_treated=0,
                att=True,
                xfml=inc,
            )
            ta = f_lpa.tidy().iloc[0]
            att_rows.append(
                dict(
                    event=name,
                    estimator="lpdid_att",
                    att=float(ta["Estimate"]),
                    se=float(ta["Std. Error"]),
                    ci_low=float(ta["2.5%"]),
                    ci_high=float(ta["97.5%"]),
                    p=float(ta["Pr(>|t|)"]),
                    n_obs=n,
                )
            )
            est["lpdid_att"] = dict(att=float(ta["Estimate"]), se=float(ta["Std. Error"]), p=float(ta["Pr(>|t|)"]))
        except Exception as e:
            est["lpdid_error"] = f"{type(e).__name__}: {e}"[:300]
            print("lpdid failed:", est["lpdid_error"])

        # 5. pre-trend slope adjustment on the TWFE and did2s event-study rows; post-period means
        ev = pd.DataFrame([r for r in all_rows if r["event"] == name])
        ev["k"] = ev.apply(lambda r: r["k"] if "k" in r and pd.notna(r.get("k", np.nan)) else k_of(r["term"]), axis=1)
        for estname in sorted(ev["estimator"].unique()):
            sub = ev[ev["estimator"] == estname]
            est[f"{estname}_pretrend"] = pretrend_adjust(sub)
            pre = sub[(sub["k"] < cfg.ES_REF)]
            est[f"{estname}_pre_max_abs_t"] = float((pre["coef"].abs() / pre["se"]).max()) if len(pre) else np.nan
        stats[name] = est
        print(
            f"{name}: {info['treated_countries']} treated, {info['never_treated_countries']} never, dropped {info['dropped_already_treated']}; "
            f"static TWFE {est['twfe_static']['att']:+.3f} (p {est['twfe_static']['p']:.3f}, negative-weight share {est['twfe_static']['share_negative_weight']:.2f})"  # noqa: E501
        )

    ES = pd.DataFrame(all_rows)
    ES["k"] = ES.apply(
        lambda r: r["k"] if "k" in ES.columns and pd.notna(r.get("k", np.nan)) else k_of(r["term"]), axis=1
    )
    ES.to_csv(cfg.RESULTS / "event_study.csv", index=False)
    pd.DataFrame(att_rows).to_csv(cfg.RESULTS / "event_att.csv", index=False)
    save_stats("02b_event", dict(events=stats, window=dict(pre=cfg.ES_PRE, post=cfg.ES_POST, ref=cfg.ES_REF)))
    print(pd.DataFrame(att_rows).round(3).to_string())


if __name__ == "__main__":
    sys.exit(main())
