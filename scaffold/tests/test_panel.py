"""Panel-level guarantees: grid, keys, provenance, coverage, sanity of the raw inputs."""

import json

import pandas as pd
import pytest

import config as cfg
from util import check_panel_grid, sha256_of


@pytest.fixture(scope="module")
def panel():
    return pd.read_csv(cfg.PANEL_CSV)


def test_complete_grid_and_unique_keys(panel):
    check_panel_grid(panel)
    assert set(panel["iso3"]) == set(cfg.SSA_ISO3)


def test_manifest_matches_panel(panel):
    m = json.loads(cfg.MANIFEST.read_text(encoding="utf-8"))
    assert m["panel"]["sha256"] == sha256_of(cfg.PANEL_CSV)
    assert cfg.data_version() == m["panel"]["sha256"][:12] == m["data_version"]
    assert m["panel"]["rows"] == len(panel) and m["panel"]["columns"] == panel.shape[1]


def test_country_codes_lookup():
    c = pd.read_csv(cfg.COUNTRY_CODES_CSV, keep_default_na=False, na_values=[""], dtype=str)
    assert len(c) == 49 and set(c["iso3"]) == set(cfg.SSA_ISO3)
    assert c.loc[c["iso3"] == "NAM", "iso2"].item() == "NA"  # the default NA parsing would erase Namibia
    assert c["faostat_area_code"].is_unique and c["iso2"].is_unique


def test_expected_coverage_gaps(panel):
    rd = pd.read_csv(cfg.PANEL_DIR / "ssa_panel_readiness.csv", keep_default_na=False)
    for r in rd.itertuples():
        if r.column.startswith(("feat_gifna_*", "feat_gd_*")):
            continue
        missing = set(r.missing_countries.split()) if r.missing_countries else set()
        observed = set(cfg.SSA_ISO3) - set(panel.dropna(subset=[r.column])["iso3"])
        assert missing == observed, r.column


def test_identical_anaemia_series(panel):
    diff = (panel["out_anaemia_wra_unicef_pct"] - panel["out_anaemia_wra_fs_pct"]).abs().max()
    assert diff == 0


def test_income_positive(panel):
    for c in (cfg.INCOME, cfg.INCOME_ALT):
        assert (panel[c].dropna() > 0).all()


def test_no_imputation_signature(panel):
    # a modelled annual series is complete for its years; a survey-point series stays sparse
    assert panel["out_anaemia_wra_fs_pct"].notna().sum() == 49 * 24
    assert panel["out_wasting_u5_pct"].notna().sum() < 49 * 10
