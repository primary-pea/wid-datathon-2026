"""v2.0 guarantees: the events table, the survey flag, the bounds, the specification curve, the event studies."""

import pandas as pd
import pytest

import config as cfg
from util import load_stats


@pytest.fixture(scope="module")
def events():
    return pd.read_csv(cfg.EVENTS_CSV)


def test_events_one_row_per_country(events):
    assert len(events) == 49 and events["iso3"].is_unique and set(events["iso3"]) == set(cfg.SSA_ISO3)
    fy = events["first_anaemia_policy_year"].dropna()
    assert ((fy >= 1950) & (fy <= 2026)).all()
    wm = events["gfdx_wheat_mandate_year"].dropna()
    assert ((wm >= 1990) & (wm <= 2026)).all()


def test_survey_flag_is_binary_and_sparse():
    p = pd.read_csv(cfg.PANEL_CSV)
    assert set(p[cfg.SURVEY_FLAG].dropna().unique()) <= {0, 1}
    assert 40 <= p[cfg.SURVEY_FLAG].sum() <= 200


def test_bounds_and_bootstrap_present():
    s = load_stats("02_fe")
    b = s["bounds"]
    assert b["mde80_pp_per_unit"] > 0 and b["ci90_per_unit"][0] < b["ci90_per_unit"][1]
    assert 0 <= b["tost_p"] <= 1
    assert 0 < s["wild_cluster_bootstrap"]["A_main"]["p_wcb"] <= 1
    for y2, v in s["outcome_swaps"].items():
        assert v["p_bh"] >= v["p"] - 1e-12, y2


def test_spec_curve_size():
    sc = pd.read_csv(cfg.RESULTS / "spec_curve.csv")
    s = load_stats("02c_spec")
    assert len(sc) == s["n_specs"] >= 200
    assert sc["coef_per_within_sd"].is_monotonic_increasing


def test_event_studies_ran():
    att = pd.read_csv(cfg.RESULTS / "event_att.csv")
    for ev in cfg.EVENTS:
        assert (att[(att["event"] == ev) & (att["estimator"] == "twfe_static")].shape[0]) == 1
    s = load_stats("02b_event")
    for ev in cfg.EVENTS:
        assert 0 <= s["events"][ev]["twfe_static"]["share_negative_weight"] <= 1


def test_deworming_coverage_column():
    p = pd.read_csv(cfg.PANEL_CSV)
    v = p["feat_sth_pc_coverage_sac_pct"].dropna()
    assert len(v) > 200 and (v >= 0).all() and (v <= 150).all()
    assert p.loc[p["feat_sth_pc_coverage_sac_pct"].notna(), "iso3"].nunique() >= 25
