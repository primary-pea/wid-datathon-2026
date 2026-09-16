"""Shared helpers for the scaffold: provenance hashing, stats persistence, panel guards, fixed-effects fits."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg


# ---- provenance -------------------------------------------------------------
def sha256_of(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def panel_sha256() -> str:
    return sha256_of(cfg.PANEL_CSV)


# ---- stats JSON ---------------------------------------------------------------
def _jsonable(o):
    """Recursively convert numpy scalars/arrays and NaN/inf to JSON-safe values (NaN -> None)."""
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return [_jsonable(v) for v in o.tolist()]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if math.isnan(o) or math.isinf(o) else float(o)
    if isinstance(o, (np.bool_, bool)):
        return bool(o)
    if isinstance(o, (str, int)) or o is None:
        return o
    return str(o)


def save_stats(name: str, payload: dict) -> None:
    """Write results/stats/<name>.json with run provenance stamped first. Refuses NaN tokens (invalid JSON)."""
    cfg.STATS.mkdir(parents=True, exist_ok=True)
    stamped = {
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "config_version": cfg.CONFIG_VERSION,
        "panel_sha256": panel_sha256(),
        "data_version": cfg.data_version(),
        **payload,
    }
    out = cfg.STATS / f"{name}.json"
    out.write_text(json.dumps(_jsonable(stamped), indent=2, allow_nan=False), encoding="utf-8")
    print(f"stats → {out}")


def load_stats(name: str) -> dict:
    return json.loads((cfg.STATS / f"{name}.json").read_text(encoding="utf-8"))


# ---- panel guards -------------------------------------------------------------
def check_panel_grid(panel: pd.DataFrame, years=None) -> None:
    """Raise unless (iso3, year) is unique and the panel is a complete iso3 x year grid (lags are positional)."""
    years = list(cfg.YEARS if years is None else years)
    dup = int(panel.duplicated(["iso3", "year"]).sum())
    if dup:
        raise ValueError(f"panel has {dup} duplicate (iso3, year) keys")
    expected = panel["iso3"].nunique() * len(years)
    if len(panel) != expected or set(panel["year"]) != set(years):
        raise ValueError(f"panel is not a complete iso3 x year grid: {len(panel)} rows, expected {expected}")


def load_panel() -> pd.DataFrame:
    p = pd.read_csv(cfg.PANEL_CSV)
    check_panel_grid(p)
    return p.sort_values(["iso3", "year"]).reset_index(drop=True)


def load_frame() -> pd.DataFrame:
    df = pd.read_csv(cfg.FRAME_CSV)
    check_panel_grid(df)
    return df


def window(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["year"] >= cfg.YEAR_MIN) & (df["year"] <= cfg.YEAR_MAX)]


def cluster_groups(d: pd.DataFrame) -> np.ndarray:
    return pd.factorize(d["iso3"])[0]


# ---- fixed-effects fits -------------------------------------------------------
def fe_fit(df: pd.DataFrame, y: str, xs: list[str]):
    """Two-way fixed effects (country + year), SE clustered by country.

    ``group_debias=True`` makes linearmodels' small-sample convention identical to fixest's
    ``ssc(adj=TRUE, fixef.K="full", cluster.adj=TRUE)`` used in fe_model.R, so the two SEs must agree exactly.
    """
    from linearmodels.panel import PanelOLS

    d = df.dropna(subset=[y] + xs).set_index(["iso3", "year"])
    res = PanelOLS(d[y], d[xs], entity_effects=True, time_effects=True).fit(
        cov_type="clustered", cluster_entity=True, group_debias=True
    )
    return res, d


def fe_fit_trends(df: pd.DataFrame, y: str, xs: list[str]):
    """Two-way FE plus country-specific linear trends (statsmodels OLS with dummies, SE clustered by country).

    statsmodels warns that ``C(iso3):year`` is rank-deficient by one column (the common trend is already spanned by
    the year dummies); the pinv solution leaves the coefficients on ``xs`` unaffected and fixest's ``iso3[year]``
    gives the identical point estimate. Returns (results, data, within_r2) where within_r2 = 1 - SSR/SSR(FE+trends).
    """
    import warnings

    import statsmodels.formula.api as smf

    d = df.dropna(subset=[y] + xs).copy()
    base = f"{y} ~ C(iso3) + C(year) + C(iso3):year"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = smf.ols(f"{base} + {' + '.join(xs)}", data=d).fit(
            cov_type="cluster", cov_kwds={"groups": cluster_groups(d)}
        )
        m0 = smf.ols(base, data=d).fit()
    within_r2 = float(1 - m.ssr / m0.ssr)
    return m, d, within_r2


def linkify_markdown(path: Path, roots: list[Path]) -> int:
    """Rewrite a generated markdown file so every backticked repo path becomes a relative link.

    A backticked span is a path when it contains a slash or a known extension and resolves under one of ``roots``
    (tried in order: the repo root, the scaffold folder, the file's own folder). Code fences and spans that are
    already links are left alone. Returns the number of spans linked."""
    import os
    import re
    import urllib.parse

    tick = re.compile(r"`([^`\n]+)`")
    ext = re.compile(r"\.(py|md|csv|json|ipynb|Rmd|Rproj|pdf|sh|txt|xlsx|toml|png)$")
    text = path.read_text(encoding="utf-8")
    out, fence, n = [], False, 0
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            fence = not fence
            out.append(line)
            continue
        if fence:
            out.append(line)
            continue

        def sub(m, line=line):
            nonlocal n
            t = m.group(1).strip()
            if m.start() > 0 and line[m.start() - 1] == "[" or line[m.end() : m.end() + 2] == "](":
                return m.group(0)
            if not re.fullmatch(r"[A-Za-z0-9_./ -]+", t) or ("/" not in t and not ext.search(t)) or t.startswith("."):
                return m.group(0)
            for base in roots:
                cand = (base / t).resolve()
                if cand.exists():
                    rel = os.path.relpath(cand, path.parent)
                    if cand.is_dir() and not rel.endswith("/"):
                        rel += "/"
                    n += 1
                    return f"[`{m.group(1)}`]({urllib.parse.quote(rel)})"
            return m.group(0)

        out.append(tick.sub(sub, line))
    if n:
        path.write_text("".join(out), encoding="utf-8")
    return n


def res_rows(res, spec: str, y: str, d: pd.DataFrame) -> list[dict]:
    """Tidy rows from a linearmodels PanelOLS result. ``r2_within`` is the two-way within R² (= fixest wr2)."""
    ci = res.conf_int()
    countries = int(d.index.get_level_values(0).nunique())
    years = f"{int(d.index.get_level_values(1).min())}-{int(d.index.get_level_values(1).max())}"
    return [
        {
            "spec": spec,
            "outcome": y,
            "term": term,
            "coef": float(res.params[term]),
            "se": float(res.std_errors[term]),
            "ci_low": float(ci.loc[term, "lower"]),
            "ci_high": float(ci.loc[term, "upper"]),
            "p": float(res.pvalues[term]),
            "n_obs": int(res.nobs),
            "n_countries": countries,
            "years": years,
            "r2_within": float(res.rsquared),
        }
        for term in res.params.index
    ]


def ols_rows(m, spec: str, y: str, d: pd.DataFrame, terms: list[str], r2_within: float) -> list[dict]:
    """Tidy rows for the named terms of a statsmodels OLS result (used for the country-trend variants)."""
    ci = m.conf_int()
    return [
        {
            "spec": spec,
            "outcome": y,
            "term": t,
            "coef": float(m.params[t]),
            "se": float(m.bse[t]),
            "ci_low": float(ci.loc[t, 0]),
            "ci_high": float(ci.loc[t, 1]),
            "p": float(m.pvalues[t]),
            "n_obs": int(m.nobs),
            "n_countries": int(d["iso3"].nunique()),
            "years": f"{int(d['year'].min())}-{int(d['year'].max())}",
            "r2_within": float(r2_within),
        }
        for t in terms
    ]


# ---- v2.0 helpers ---------------------------------------------------------------
def bh_adjust(pvals: list[float]) -> list[float]:
    """Benjamini–Hochberg adjusted p-values (monotone), same order as the input."""
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(p)
    ranked = p[order] * m / (np.arange(m) + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(adj, 1.0)
    return [float(v) for v in out]


def two_way_residualize(d: pd.DataFrame, cols: list[str], fe: tuple[str, ...] = ("iso3", "year")) -> pd.DataFrame:
    """Residualize the listed columns on the fixed-effect dummies (FWL), returning a copy with `<col>_dm` columns."""
    import statsmodels.formula.api as smf

    out = d.copy()
    rhs = " + ".join(f"C({f})" for f in fe)
    for c in cols:
        out[c + "_dm"] = smf.ols(f"{c} ~ {rhs}", data=out).fit().resid.values
    return out


def wild_cluster_bootstrap_p(
    d: pd.DataFrame,
    y: str,
    xs: list[str],
    term: str,
    B: int = 999,
    seed: int = 1,
    fe: tuple[str, ...] = ("iso3", "year"),
) -> dict:
    """Restricted (null-imposed) wild cluster bootstrap-t p-value for one coefficient of a two-way FE regression,
    Rademacher weights by country, on the FWL-residualized regression (Cameron, Gelbach & Miller 2008)."""
    dd = d.dropna(subset=[y] + xs).copy()
    dd = two_way_residualize(dd, [y] + xs, fe=fe)
    Y = dd[y + "_dm"].to_numpy()
    X = dd[[x + "_dm" for x in xs]].to_numpy()
    g = pd.factorize(dd["iso3"])[0]
    G = int(g.max()) + 1
    j = xs.index(term)

    def fit_t(Yv: np.ndarray) -> tuple[float, float]:
        XtX_inv = np.linalg.pinv(X.T @ X)
        b = XtX_inv @ X.T @ Yv
        e = Yv - X @ b
        meat = np.zeros((X.shape[1], X.shape[1]))
        for k in range(G):
            m = g == k
            s = X[m].T @ e[m]
            meat += np.outer(s, s)
        V = XtX_inv @ meat @ XtX_inv * (G / (G - 1))
        return float(b[j]), float(b[j] / np.sqrt(V[j, j]))

    b_obs, t_obs = fit_t(Y)
    Xr = np.delete(X, j, axis=1)  # restricted model (term excluded)
    br = np.linalg.pinv(Xr.T @ Xr) @ Xr.T @ Y
    fit_r, e_r = Xr @ br, Y - Xr @ br
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=G)[g]
        _, t_b = fit_t(fit_r + e_r * w)
        count += abs(t_b) >= abs(t_obs)
    return {"coef": b_obs, "t": t_obs, "p_wcb": float((count + 1) / (B + 1)), "B": B, "clusters": G}
