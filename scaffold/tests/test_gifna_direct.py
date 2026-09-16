"""Direct-from-source GIFNA features (v1.2): completeness, absorbing binaries, stock/any consistency, a hand recount."""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import config as cfg
import gifna_direct as gd

REPO = Path(os.environ.get("SCAFFOLD_REPO_DIR", Path(__file__).resolve().parents[2]))


@pytest.fixture(scope="module")
def panel():
    return pd.read_csv(cfg.PANEL_CSV)


def test_columns_complete_and_nonnegative(panel):
    cols = [c for c in panel.columns if c.startswith(gd.PREFIX)]
    assert (
        len(cols)
        == (len(gd.CLUSTERS) + 1) * 3 + len(gd.SOURCES) * 2 + len(gd.PER_SOURCE_CLUSTERS) * len(gd.SOURCES) * 3
    )
    assert not panel[cols].isna().any().any()
    assert (panel[cols] >= 0).all().all()


def test_any_is_absorbing_and_binary(panel):
    p = panel.sort_values(["iso3", "year"])
    for c in [c for c in p.columns if c.startswith(gd.PREFIX + "any_")]:
        assert set(p[c].unique()) <= {0, 1}, c
        assert (p.groupby("iso3")[c].diff().fillna(0) >= 0).all(), c


def test_stock_implies_any_and_log_is_log1p(panel):
    for g in (
        gd.CLUSTERS + ["all"] + list(gd.SOURCES) + [f"{c}_{s}" for c in gd.PER_SOURCE_CLUSTERS for s in gd.SOURCES]
    ):
        s, a = panel[f"{gd.PREFIX}stock_{g}"], panel[f"{gd.PREFIX}any_{g}"]
        assert ((s > 0) <= (a == 1)).all(), g
    diff = panel[f"{gd.PREFIX}logstock_all"] - np.log1p(panel[f"{gd.PREFIX}stock_all"])
    assert diff.abs().max() < 1e-9


def test_registry_files_and_rules_are_manifest_inputs():
    m = json.loads(cfg.MANIFEST.read_text(encoding="utf-8"))
    names = [k.split("/")[-1] for k in m["inputs"]]
    for f in [
        "gifna_policies.csv",
        "gifna_programmes_and_actions.csv",
        "gifna_mechanisms.csv",
        "gifna_cluster_rules.csv",
    ]:
        assert f in names, f


def test_hand_recount_of_active_anaemia_policies(panel):
    """Recount, straight from the registry file, the anaemia-cluster policies active in one country-year; the panel's
    cluster stock also holds programmes and mechanisms, so the policy recount is a lower bound it must reach."""
    src = REPO / "gifna" / "gifna_policies.csv"
    if not src.exists():
        pytest.skip("shared repo not available")
    rules = gd.load_rules(cfg.INPUTS / "gifna_cluster_rules.csv")
    pol = pd.read_csv(src, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    iso, year = "RWA", 2015
    n = 0
    for r in pol[pol["Iso3Code"] == iso].itertuples(index=False):
        s = int(r.Start_Year) if str(r.Start_Year).isdigit() else None
        e = int(r.End_Year) if str(r.End_Year).isdigit() else gd.OPEN_END
        if s is None or not (s <= year <= max(e, s)):
            continue
        if any("anaemia" in gd.map_token(t, rules) for t in gd.split_tokens(r.Topics)):
            n += 1
    got = panel.loc[(panel["iso3"] == iso) & (panel["year"] == year), f"{gd.PREFIX}stock_anaemia"].item()
    pol_only = panel.loc[(panel["iso3"] == iso) & (panel["year"] == year), f"{gd.PREFIX}stock_policies"].item()
    assert n > 0 and got >= n and pol_only >= n


def test_every_token_is_in_the_map_and_mostly_mapped():
    tm = pd.read_csv(cfg.PANEL_DIR / "gifna_direct_token_map.csv", dtype=str, keep_default_na=False)
    assert set(tm["source"]) == set(gd.SOURCES)
    mentions = tm["mentions"].astype(int)
    assert (mentions > 0).all()
    assert mentions[tm["clusters"] == ""].sum() / mentions.sum() < 0.10
