"""07 — build the team notebook (presentation layer, standalone, Colab-friendly), execute it once on a fresh kernel,
cross-check its main coefficient against the pipeline's stats JSON, and save it with outputs stripped."""

from __future__ import annotations

import json
import sys

import nbformat as nbf
from nbclient import NotebookClient

import config as cfg
from util import load_stats

NOTEBOOK = cfg.SCAF / "90_team_notebook.ipynb"
CHECK = cfg.RESULTS / "notebook_check.json"


def build() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    cells = [
        md(f"""# SSA maternal-nutrition panel — fixed-effects scaffold ({cfg.SCAFFOLD_VERSION}, {cfg.RUN_DATE})

One notebook, one table. Reads `ssa_panel.csv`, builds the modelling frame, fits the two-way fixed-effects model, runs the placebo, lag and **country-trend** checks, a compact leave-one-country-out validation, and the level ranking. Cells marked **SWAP HERE** are the only ones you need to touch to change the outcome, the policy feature or the lag.

Runs from the repo (`scaffold/`, reads `../derived/ssa_panel.csv`), from a folder holding `panel/ssa_panel.csv`, or in Colab (mount Drive; `DRIVE_PATH` below). No credentials, no API calls. Numbers here are association within countries, not causation — every outcome series is modelled."""),
        code("""import importlib.util, subprocess, sys
for pkg in ("linearmodels", "statsmodels"):
    if importlib.util.find_spec(pkg) is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)
import json, os, warnings
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from linearmodels.panel import PanelOLS
import statsmodels.formula.api as smf
pd.set_option("display.width", 160)"""),
        md("## Parameters — SWAP HERE"),
        code(f"""OUTCOME = "{cfg.OUTCOME}"          # try: {", ".join(repr(k) for k in cfg.SECONDARY)}
POLICY  = "{cfg.POLICY_MAIN}"   # v2.0 main dose: anaemia-cluster policies active (dated); any feat_gd_* or feat_gifna_* column works
INCOME  = "{cfg.INCOME}"        # constant 2015 US$ (v2.0 main); "{cfg.INCOME_ALT}" = current US$ team file
LAG, LEAD = {cfg.LAG}, {cfg.LEAD}
YEAR_MIN, YEAR_MAX = {cfg.YEAR_MIN}, {cfg.YEAR_MAX}
RECENT_FROM, MIN_YEARS_RECENT, N_TAIL = {cfg.RECENT_FROM}, {cfg.MIN_YEARS_RECENT}, {cfg.N_DEVIANTS}
DRIVE_PATH = "/content/drive/MyDrive/[Primary Pea] WiD Datathon 2026/scaffold/ssa_panel.csv"   # Colab
CANDIDATES = ["panel/ssa_panel.csv", "../derived/ssa_panel.csv", "derived/ssa_panel.csv", DRIVE_PATH]"""),
        code("""path = next((p for p in CANDIDATES if os.path.exists(p)), None)
if path is None and os.path.exists("/content"):
    from google.colab import drive
    drive.mount("/content/drive")
    path = DRIVE_PATH if os.path.exists(DRIVE_PATH) else None
if path is None:
    raise FileNotFoundError(f"ssa_panel.csv not found; tried {CANDIDATES}")
panel = pd.read_csv(path).sort_values(["iso3", "year"]).reset_index(drop=True)
assert not panel.duplicated(["iso3", "year"]).any() and len(panel) == panel.iso3.nunique() * panel.year.nunique(), "panel must be a complete iso3 x year grid (lags are positional)"
print(path, "|", panel.shape, "| countries:", panel.iso3.nunique(), "| years:", panel.year.min(), "-", panel.year.max())"""),
        md(
            "## Prep: log income, lags and leads (GIFNA `*_count_active` columns are NaN in the source when no record is active and read as 0 here)"
        ),
        code("""for c in ["feat_gifna_policy_count_active", "feat_gifna_programme_count_active", "feat_gifna_mechanism_count_active"]:
    panel[c] = panel[c].fillna(0.0)
assert (panel[INCOME].dropna() > 0).all()
panel["log_gdp_pc"] = np.log(panel[INCOME])
g = panel.groupby("iso3", sort=False)
for k in (2, 3, 5):
    panel[f"pol_lag{k}"] = g[POLICY].shift(k)
panel[f"pol_lead{LEAD}"] = g[POLICY].shift(-LEAD)
frame = panel[(panel.year >= YEAR_MIN) & (panel.year <= YEAR_MAX)]
main = f"pol_lag{LAG}"

def fe(d, y, xs):
    d = d.dropna(subset=[y] + xs).set_index(["iso3", "year"])
    return PanelOLS(d[y], d[xs], entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True, group_debias=True), d

def fe_trends(d, y, xs):
    d = d.dropna(subset=[y] + xs).copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")   # C(iso3):year is rank-deficient by one column (harmless; fixest iso3[year] agrees)
        return smf.ols(f"{y} ~ C(iso3) + C(year) + C(iso3):year + {' + '.join(xs)}", data=d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.iso3)[0]}), d

def show(res, d, title):
    ci = res.conf_int()
    t = pd.DataFrame({"coef": res.params, "se": res.std_errors, "ci_low": ci["lower"], "ci_high": ci["upper"], "p": res.pvalues}).round(3)
    print(f"{title}: n={res.nobs}, countries={d.index.get_level_values(0).nunique()}, two-way within-R2={res.rsquared:.3f}")
    display(t)
    return t"""),
        md("## Main spec: country + year fixed effects, policy lagged, log income, SE clustered by country"),
        code("""resA, dA = fe(frame, OUTCOME, [main, "log_gdp_pc"])
tabA = show(resA, dA, "spec A")"""),
        md(
            "## The two honesty checks: placebo lead (must be null) and country-specific trends (the coefficient must survive them)"
        ),
        code("""rows = []
for name, xs in {"lag2": ["pol_lag2", "log_gdp_pc"], "lag3 (main)": ["pol_lag3", "log_gdp_pc"], "lag5": ["pol_lag5", "log_gdp_pc"],
                 f"placebo lead{LEAD}": [f"pol_lead{LEAD}", "log_gdp_pc"], f"lead{LEAD} + lag{LAG}": [f"pol_lead{LEAD}", main, "log_gdp_pc"]}.items():
    r, d = fe(frame, OUTCOME, xs); ci = r.conf_int(); t = xs[0]
    rows.append(dict(variant=name, term=t, coef=r.params[t], ci_low=ci.loc[t, "lower"], ci_high=ci.loc[t, "upper"], p=r.pvalues[t], n=r.nobs))
for name, xs in {"main + country trends": [main, "log_gdp_pc"], "placebo + country trends": [f"pol_lead{LEAD}", "log_gdp_pc"]}.items():
    m, d = fe_trends(frame, OUTCOME, xs); ci = m.conf_int(); t = xs[0]
    rows.append(dict(variant=name, term=t, coef=m.params[t], ci_low=ci.loc[t, 0], ci_high=ci.loc[t, 1], p=m.pvalues[t], n=int(m.nobs)))
ladder = pd.DataFrame(rows)
display(ladder.round(3))"""),
        md("## Leave-one-country-out: predict each country's within-country path with a model that never saw it"),
        code("""import statsmodels.api as sm
d = frame.dropna(subset=[OUTCOME, "log_gdp_pc", main]).copy()   # pipeline uses the same rows (all composites are complete where the main one is)
countries, years = sorted(d.iso3.unique()), sorted(d.year.unique())
def design(dd, xs, cs):
    cols = {f"c_{c}": (dd.iso3 == c).astype(float).values for c in cs[1:]}
    cols.update({f"y_{y}": (dd.year == y).astype(float).values for y in years[1:]})
    for x in xs: cols[x] = dd[x].values
    cols["const"] = np.ones(len(dd)); return pd.DataFrame(cols, index=dd.index)
def loco(xs):
    errs = []
    for k in countries:
        tr, te = d[d.iso3 != k], d[d.iso3 == k]
        X = design(tr, xs, sorted(tr.iso3.unique())); b = dict(zip(X.columns, sm.OLS(tr[OUTCOME].values, X.values).fit().params))
        gam = np.array([b.get(f"y_{y}", 0.0) for y in te.year]); xb = np.zeros(len(te))
        for x in xs: xb += b[x] * (te[x].values - te[x].values.mean())
        pred = xb + (gam - gam.mean()); obs = te[OUTCOME].values - te[OUTCOME].values.mean(); errs.append(obs - pred)
    e = np.concatenate(errs); return float(np.sqrt((e ** 2).mean()))
print("held-out RMSE of the within-country path (pp):")
for name, xs in {"year effects only": [], "+ income": ["log_gdp_pc"], "+ income + policy": ["log_gdp_pc", main]}.items():
    print(f"  {name:22s} {loco(xs):.2f}")"""),
        md(
            "## Level ranking: anaemia relative to what income predicts (income explains ~5% of the level variance, so this is the level ranking; screening only)"
        ),
        code("""di = frame.dropna(subset=[OUTCOME, "log_gdp_pc"]).copy()
inc = smf.ols(f"{OUTCOME} ~ C(year) + log_gdp_pc", data=di).fit()
di["resid"] = inc.resid
rec = di[di.year >= RECENT_FROM].groupby(["iso3", "country"]).agg(resid=("resid", "mean"), n_years=("resid", "size"), level=(OUTCOME, "mean")).reset_index()
rec.loc[rec.n_years < MIN_YEARS_RECENT, "resid"] = np.nan
rank = rec.dropna(subset=["resid"]).sort_values("resid").reset_index(drop=True)
print(f"income-only R2 = {inc.rsquared:.3f}; Spearman(residual, raw level) = {rank[['resid', 'level']].corr(method='spearman').iloc[0, 1]:.3f}; ranked {len(rank)} of {rec.shape[0]} countries")
print("lowest relative to income:"); display(rank.head(N_TAIL).round(1))
print("highest relative to income:"); display(rank.tail(N_TAIL).round(1))"""),
        md("## Two figures: the level ranking and the coefficient across specs"),
        code("""fig, ax = plt.subplots(figsize=(7, 9), dpi=110)
r = rank; ax.axvline(0, color="#c3c2b7", lw=0.8)
ax.hlines(r.index, 0, r.resid, color="#e1e0d9", lw=1); ax.scatter(r.resid, r.index, s=30, c=["#2a78d6" if v < 0 else "#eb6834" for v in r.resid], zorder=3)
ax.set_yticks(r.index); ax.set_yticklabels(r.country, fontsize=7.5); ax.set_xlabel(f"anaemia minus income-predicted anaemia, mean {RECENT_FROM}–{YEAR_MAX} (pp)")
for s in ("top", "right"): ax.spines[s].set_visible(False)
plt.title("Level ranking, income-adjusted (screening device, not a verdict)", loc="left"); plt.tight_layout(); plt.show()
s = ladder.reset_index(drop=True)
fig, ax = plt.subplots(figsize=(7, 3.6), dpi=110); ax.axvline(0, color="#c3c2b7", lw=0.8)
for i, x in s.iterrows():
    col = "#2a78d6" if "trend" in x.variant else ("#898781" if "placebo" in x.variant or "lead" in x.variant else "#52514e")
    ax.plot([x.ci_low, x.ci_high], [i, i], color=col, lw=2); ax.plot(x.coef, i, "o", color=col)
ax.set_yticks(s.index); ax.set_yticklabels(s.variant); ax.set_xlabel("coefficient on the policy feature (pp of outcome per flag-count)")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
plt.title("Coefficient across lags; grey = placebo leads; blue = with country-specific trends", loc="left"); plt.tight_layout(); plt.show()"""),
        md("## Cross-check against the pipeline (runs only where `results/stats/02_fe.json` exists, i.e. in the repo)"),
        code(f"""stats_path = next((p for p in ["results/stats/02_fe.json", "../scaffold/results/stats/02_fe.json"] if os.path.exists(p)), None)
if stats_path and OUTCOME == "{cfg.OUTCOME}" and POLICY == "{cfg.POLICY_MAIN}" and INCOME == "{cfg.INCOME}" and LAG == {cfg.LAG}:
    ref = json.load(open(stats_path))["spec_A"]
    diff = abs(float(resA.params[main]) - ref["coef"])
    print(f"notebook {{float(resA.params[main]):+.6f}} vs pipeline {{ref['coef']:+.6f}} (|diff| {{diff:.1e}}) —", "MATCH" if diff < 1e-9 else "MISMATCH")
    os.makedirs("results", exist_ok=True)
    json.dump({{"coef": float(resA.params[main]), "n": int(resA.nobs), "match": bool(diff < 1e-9)}}, open("results/notebook_check.json", "w"))
else:
    print("pipeline stats not found or parameters changed — cross-check skipped")"""),
        md("""## Caveats
Modelled outcomes (smooth by construction) → association within countries only, and the country-trend rows show that association is shared trend. GIFNA = reported policy, not implementation; the main composite double-counts records carrying several flags. The level ranking inherits every omitted driver. Nothing here is quotable until it is recomputed in the numbered scripts and carries an `[E]` tag."""),
    ]
    nb["cells"] = cells
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    return nb


def main() -> None:
    nb = build()
    if "--no-exec" not in sys.argv:
        CHECK.unlink(missing_ok=True)
        NotebookClient(
            nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": str(cfg.SCAF)}}
        ).execute()
        chk = json.loads(CHECK.read_text(encoding="utf-8"))
        ref = load_stats("02_fe")["spec_A"]["coef"]
        if not chk["match"] or abs(chk["coef"] - ref) >= 1e-9:
            raise SystemExit(f"notebook spec A {chk['coef']} differs from pipeline {ref}")
        print(f"notebook executed on a fresh kernel; spec A matches the pipeline ({chk['coef']:+.6f})")
    for c in nb.cells:
        if c.cell_type == "code":
            c.outputs = []
            c.execution_count = None
    nbf.write(nb, NOTEBOOK)
    print("→", NOTEBOOK)


if __name__ == "__main__":
    sys.exit(main())
