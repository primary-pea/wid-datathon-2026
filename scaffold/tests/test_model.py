"""Model-level guarantees: stats JSON reproduce from the frame, hashes agree, R and Python agree."""

import pandas as pd
import pytest

import config as cfg
from util import fe_fit, fe_fit_trends, load_frame, load_stats, panel_sha256, window

MAIN = f"{cfg.POLICY_MAIN}_lag{cfg.LAG}"


@pytest.fixture(scope="module")
def df():
    if not cfg.FRAME_CSV.exists():
        pytest.skip("results/frame.csv not built yet — run run_all.sh first")
    return window(load_frame())


def test_stats_share_the_panel_hash():
    sha = panel_sha256()
    for n in ("01_frame", "02_fe", "02b_event", "02c_spec", "03_loco", "04_residuals", "05_figures", "06_report"):
        assert load_stats(n)["panel_sha256"] == sha, n


def test_spec_a_reproduces(df):
    s = load_stats("02_fe")["spec_A"]
    r, d = fe_fit(df, cfg.OUTCOME, [MAIN, cfg.LOG_INCOME])
    assert abs(float(r.params[MAIN]) - s["coef"]) < 1e-9
    assert abs(float(r.std_errors[MAIN]) - s["se"]) < 1e-9
    assert int(r.nobs) == s["n_obs"]
    assert abs(float(r.rsquared) - s["r2_within"]) < 1e-9  # two-way within R², not rsquared_within


def test_trend_variant_reproduces(df):
    t = load_stats("02_fe")["trend"]["main"]
    m, _, _ = fe_fit_trends(df, cfg.OUTCOME, [MAIN, cfg.LOG_INCOME])
    assert abs(float(m.params[MAIN]) - t["coef"]) < 1e-9


def test_r_replica_agrees_if_present():
    rp = cfg.RESULTS / "r_fe_coefficients.csv"
    if not rp.exists():
        pytest.skip("R replica not run")
    r = pd.read_csv(rp)
    ra = r[(r["spec"] == "A_main") & (r["term"] == "pol_lag3")].iloc[0]
    s = load_stats("02_fe")["spec_A"]
    assert abs(ra["coef"] - s["coef"]) < 1e-6 and abs(ra["se"] - s["se"]) < 1e-6
    rt = r[(r["spec"] == "trend_main") & (r["term"] == "pol_lag3")].iloc[0]
    assert abs(rt["coef"] - load_stats("02_fe")["trend"]["main"]["coef"]) < 1e-6


def test_ranking_rules():
    s = load_stats("04_residuals")
    assert s["n_ranked_context"] + len(s["excluded_from_context_ranking"]) == 49
    assert len(s["positive_deviants"]) == cfg.N_DEVIANTS == len(s["under_performers"])


def test_sensitivity_terms_are_named():
    sens = pd.read_csv(cfg.RESULTS / "fe_sensitivity.csv")
    assert {"term", "block"} <= set(sens.columns)
    assert sens.loc[sens["variant"] == "income_only", "term"].item() == cfg.LOG_INCOME
