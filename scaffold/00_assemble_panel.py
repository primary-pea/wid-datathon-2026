"""00 — assemble the Sub-Saharan Africa country × year panel from the raw inputs (scaffold v1.2, 2026-09-11).

One wide table (iso3 × year, 2000–2025), a readiness summary, a content-hashed MANIFEST.json and a data version.
Every join uses a code (ISO3, ISO2 or FAOSTAT area code) taken from inputs/country_codes_ssa.csv; duplicate keys and
unexpected coverage gaps fail the build. Sources are read-only. Nothing is imputed.

Raw-input locations:
  scaffold/inputs/ — pinned copies committed with the code (unicef/*.xlsx, faostat/*.parquet, igme_2025_ssa_national.csv,
                     lookups), so any clone rebuilds. Fallback: the atlas dir (SCAFFOLD_ATLAS_DIR → derived/, cache/).
  repo dir (SCAFFOLD_REPO_DIR) — gifna/gifna_feature_table.csv, the three registry files gifna/gifna_policies.csv,
                     gifna/gifna_programmes_and_actions.csv, gifna/gifna_mechanisms.csv (read directly by gifna_direct.py,
                     v1.2), subsaharan_data/GDP_per_capita.csv, subsaharan_data/subsahran_africa_countries.csv
"""

from __future__ import annotations

import fnmatch
import glob
import json
import os
import platform
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg
import gifna_direct
from util import check_panel_grid, sha256_of

WID = Path(os.environ.get("SCAFFOLD_ATLAS_DIR", cfg.ROOT))
_repo_default = next(
    (p for p in (cfg.SCAF.parents[1], Path.home() / "miscP" / "parent-primary-pea" / "wid-datathon-2026") if (p / "gifna").exists()),
    cfg.SCAF.parents[1],
)
SCR = Path(os.environ.get("SCAFFOLD_REPO_DIR", _repo_default))
OUT = cfg.PANEL_DIR
SSA = set(cfg.SSA_ISO3)
YEARS = list(cfg.YEARS)
USED_INPUTS: list[Path] = []


# ---- helpers ------------------------------------------------------------------
def inp(path: Path) -> Path:
    """Register a raw input (for the manifest) and fail early with a useful message if it is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"input missing: {path}\n  set SCAFFOLD_ATLAS_DIR / SCAFFOLD_REPO_DIR or copy the file (see README)"
        )
    USED_INPUTS.append(path)
    return path


def one_file(*patterns: str) -> Path:
    """First pattern (in order) matching exactly one file; more than one match means two releases are cached."""
    for pattern in patterns:
        hits = sorted(glob.glob(pattern))
        if len(hits) > 1:
            raise FileNotFoundError(f"expected exactly one file for {pattern}, found {len(hits)}: {hits}")
        if hits:
            return inp(Path(hits[0]))
    raise FileNotFoundError(f"no file matches any of {patterns}")


def first_existing(*paths: Path) -> Path:
    for q in paths:
        if q.exists():
            return inp(q)
    raise FileNotFoundError(f"none of these inputs exist: {[str(q) for q in paths]}")


def rel(p: Path) -> str:
    """Repo-relative label for the manifest (scaffold parent first, then the team repo), never an absolute path."""
    for base, tag_ in ((cfg.ROOT, ""), (SCR, "team-repo/")):
        try:
            return tag_ + str(p.resolve().relative_to(base.resolve()))
        except ValueError:
            continue
    return p.name


def load_codes() -> pd.DataFrame:
    c = pd.read_csv(inp(cfg.COUNTRY_CODES_CSV), keep_default_na=False, na_values=[""], dtype=str, encoding="utf-8")
    if set(c["iso3"]) != SSA or len(c) != len(SSA):
        raise ValueError("inputs/country_codes_ssa.csv does not match config.SSA_ISO3")
    return c


def tidy(d: pd.DataFrame, col: str) -> pd.DataFrame:
    """Standardise a (iso3, year, value) frame: SSA rows, panel years, non-null values, unique keys."""
    d = d[["iso3", "year", "value"]].copy()
    d["year"] = pd.to_numeric(d["year"], errors="coerce")
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    d = d.dropna(subset=["iso3", "year", "value"])
    d["year"] = d["year"].astype(int)
    d = d[d["iso3"].isin(SSA) & d["year"].between(YEARS[0], YEARS[-1])]
    dup = int(d.duplicated(["iso3", "year"]).sum())
    if dup:
        raise ValueError(
            f"{col}: {dup} duplicate (iso3, year) rows in the source — resolve upstream, not with .first()"
        )
    return d.rename(columns={"value": col})


def expected_missing(col: str) -> set[str]:
    for key, val in cfg.EXPECTED_MISSING.items():
        if fnmatch.fnmatch(col, key):
            return set(val)
    return set()


class PanelBuilder:
    def __init__(self) -> None:
        self.panel = pd.MultiIndex.from_product([sorted(SSA), YEARS], names=["iso3", "year"]).to_frame(index=False)
        self.readiness: list[dict] = []

    def add(self, d: pd.DataFrame, col: str, group: str, source: str, strict: bool = True) -> None:
        d = tidy(d, col)
        self.panel = self.panel.merge(d, on=["iso3", "year"], how="left", validate="one_to_one")
        present = set(d["iso3"])
        missing, expected = SSA - present, expected_missing(col)
        if missing - expected and not strict:
            print(f"  note: {col} has no values for {sorted(missing - expected)} (recorded in readiness; not fatal)")
        elif missing - expected:
            raise ValueError(
                f"{col}: unexpected coverage gap for {sorted(missing - expected)} — investigate or add to config.EXPECTED_MISSING"
            )
        if expected - missing:
            print(f"  note: {col} now covers {sorted(expected - missing)} (config.EXPECTED_MISSING can be tightened)")
        self.readiness.append(
            dict(
                group=group,
                column=col,
                source=source,
                countries_of_49=len(present),
                year_min=int(d["year"].min()) if len(d) else pd.NA,
                year_max=int(d["year"].max()) if len(d) else pd.NA,
                country_year_cells=len(d),
                missing_countries=" ".join(sorted(missing)),
            )
        )
        print(f"  + {col:42s} {len(present):2d} countries  {len(d):4d} cells")


# ---- loaders ------------------------------------------------------------------
def unicef_sheet(xl: pd.ExcelFile, sheet: str) -> pd.DataFrame:
    """UNICEF women's-nutrition workbook: locate the header row by its 'ISO3Code' label instead of fixed offsets."""
    raw = xl.parse(sheet, header=None)
    hdr = raw.index[raw[1].astype(str).str.strip() == "ISO3Code"].tolist()
    if len(hdr) != 1:
        raise ValueError(f"UNICEF sheet {sheet}: could not locate the ISO3Code header row")
    r = hdr[0]
    years = pd.Series(raw.iloc[r - 2]).ffill()
    stat = raw.iloc[r - 1].astype(str).str.strip()
    rows = raw.iloc[r + 1 :]
    recs = [
        pd.DataFrame({"iso3": rows[1].astype(str).values, "year": int(float(years[j])), "value": rows[j].values})
        for j in range(6, raw.shape[1])
        if stat[j] == "Point Estimate"
    ]
    return pd.concat(recs, ignore_index=True)


def faostat(
    parquet: Path, area2iso: dict[str, str], item: str | None = None, unit_kw: str | None = None
) -> pd.DataFrame:
    d = pd.read_parquet(parquet)
    d = d[d["Element"] == "Value"]
    if item is not None:
        d = d[d["Item"] == item]
    if unit_kw is not None:
        d = d[d["Unit"].astype(str).str.contains(unit_kw, regex=False)]
    return pd.DataFrame({"iso3": d["Area Code"].astype(str).map(area2iso), "year": d["Year"], "value": d["Value"]})


def load_igme() -> pd.DataFrame:
    """Slim pinned extract (iso3, indicator, year, value) or, failing that, the full atlas parquet filtered the same way."""
    slim = cfg.INPUTS / "igme_2025_ssa_national.csv"
    if slim.exists():
        return pd.read_csv(inp(slim))
    ig = pd.read_parquet(inp(WID / "derived" / "igme_2025_estimates.parquet"))
    wq = ig["wealth_quintile"]
    d = ig[(ig["sex"] == "Total") & (wq.isna() | wq.astype(str).str.lower().isin(["total", "nan", "none"]))]
    return d[["iso3", "indicator", "year", "estimate"]].rename(columns={"estimate": "value"})


def igme(ig: pd.DataFrame, indicator: str) -> pd.DataFrame:
    return ig[ig["indicator"] == indicator][["iso3", "year", "value"]]


def wb_current(iso2_to_iso3: dict[str, str]) -> pd.DataFrame:
    """Team GDP file. Joined on ISO2 (keep_default_na=False: Namibia is 'NA'). The header says 'Constant USD' but the
    series is NY.GDP.PCAP.CD (current US$) — verified against the World Bank API, max relative difference 0.0."""
    path = inp(SCR / "subsaharan_data" / "GDP_per_capita.csv")
    g = pd.read_csv(path, keep_default_na=False, na_values=[""], dtype={"ISO2_WB_CODE": str})
    value_col = "GDP Per Capita (Constant USD)"
    if value_col not in g.columns:
        raise ValueError(f"{path.name}: expected column {value_col!r}, found {list(g.columns)}")
    unmapped = sorted(set(g["ISO2_WB_CODE"]) - set(iso2_to_iso3))
    if unmapped:
        print(f"  note: GDP file ISO2 codes not in the SSA lookup (ignored): {unmapped}")
    return pd.DataFrame({"iso3": g["ISO2_WB_CODE"].map(iso2_to_iso3), "year": g["Year"], "value": g[value_col]})


def wb_constant() -> pd.DataFrame:
    d = pd.read_csv(inp(cfg.INPUTS / "wb_gdp_pc_constant_2015usd_ssa.csv"))
    inp(cfg.INPUTS / "wb_gdp_pc_constant_2015usd_ssa.provenance.json")
    return d.rename(columns={"gdp_pc_constant_2015_usd": "value"})


def fies3() -> pd.DataFrame:
    return pd.read_csv(inp(cfg.INPUTS / "ssa_fies_3yr_average.csv"))


def gifna() -> pd.DataFrame:
    gi = pd.read_csv(inp(SCR / "gifna" / "gifna_feature_table.csv"), encoding="utf-8-sig")
    gi = gi[gi["iso3"].isin(SSA)]
    if gi.duplicated(["iso3", "year"]).any():
        raise ValueError("GIFNA feature table has duplicate (iso3, year) rows")
    keep = [
        c for c in gi.columns if c not in ("iso3", "country_name", "year", "Coverage_Percent")
    ]  # Coverage_Percent is empty
    return gi[["iso3", "year"] + keep].rename(columns={k: "feat_gifna_" + k for k in keep})


def wb_context() -> pd.DataFrame:
    """Pinned World Bank context series (v2.0): long table iso3, year, indicator columns."""
    d = pd.read_csv(inp(cfg.INPUTS / "wb_context_ssa.csv"))
    inp(cfg.INPUTS / "wb_context_ssa.provenance.json")
    return d


def team_extra(iso2_to_iso3: dict[str, str], col_in: str) -> pd.DataFrame | None:
    """A further column of the team's World Bank file (unemployment, hospital beds), joined on ISO2."""
    path = inp(SCR / "subsaharan_data" / "GDP_per_capita.csv")
    g = pd.read_csv(path, keep_default_na=False, na_values=[""], dtype={"ISO2_WB_CODE": str})
    if col_in not in g.columns:
        print(f"  note: team file has no column {col_in!r}; skipped")
        return None
    return pd.DataFrame(
        {
            "iso3": g["ISO2_WB_CODE"].map(iso2_to_iso3),
            "year": g["Year"],
            "value": pd.to_numeric(g[col_in], errors="coerce"),
        }
    ).dropna(subset=["value"])


DHS_NAME_OVERRIDES = {
    "congo democratic republic": "COD",
    "congo": "COG",
    "cote d'ivoire": "CIV",
    "tanzania": "TZA",
    "eswatini": "SWZ",
    "gambia": "GMB",
    "sao tome and principe": "STP",
    "central african republic": "CAF",
    "cabo verde": "CPV",
    "cape verde": "CPV",
}


def _norm(s: str) -> str:
    import unicodedata

    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z' ]+", " ", s.lower()).strip()


def dhs_surveys(codes: pd.DataFrame) -> pd.DataFrame:
    """Country-years with a DHS survey that measured women's anaemia (pinned API pull) → (iso3, year, value=1)."""
    d = pd.read_csv(inp(cfg.INPUTS / "dhs_anaemia_women_surveys.csv"))
    inp(cfg.INPUTS / "dhs_anaemia_women_surveys.provenance.json")
    name_to_iso = {_norm(n): i for n, i in zip(codes["display_name"], codes["iso3"], strict=True)}
    for extra_col in ("name", "official_name", "faostat_name"):
        if extra_col in codes.columns:
            name_to_iso.update({_norm(n): i for n, i in zip(codes[extra_col], codes["iso3"], strict=True) if str(n)})
    name_to_iso.update(DHS_NAME_OVERRIDES)
    d["iso3"] = d["country_name"].map(lambda n: name_to_iso.get(_norm(n)))
    d = d[d["iso3"].isin(SSA)].copy()
    d["year"] = pd.to_numeric(d["survey_year"].astype(str).str[:4], errors="coerce")
    d = d.dropna(subset=["year"]).astype({"year": int})
    d = d[d["year"].between(YEARS[0], YEARS[-1])].drop_duplicates(["iso3", "year"])
    return pd.DataFrame({"iso3": d["iso3"], "year": d["year"], "value": 1.0})


def gfdx_years() -> pd.DataFrame:
    """GFDx mandatory-fortification years per country (wheat flour, maize flour) from the pinned extract."""
    d = pd.read_csv(inp(cfg.INPUTS / "gfdx_legislation_years_ssa.csv"))
    inp(cfg.INPUTS / "gfdx_legislation_years_ssa.provenance.json")
    out = pd.DataFrame({"iso3": sorted(SSA)}).set_index("iso3")
    for vehicle, col in [("Wheat flour", "gfdx_wheat_mandate_year"), ("Maize flour", "gfdx_maize_mandate_year")]:
        v = d[(d["vehicle"] == vehicle) & (d["mandatory_fortification"] == "YES")]
        out[col] = pd.to_numeric(v.set_index("iso3")["fortification_year"], errors="coerce")
        out[col.replace("_year", "_status")] = d[d["vehicle"] == vehicle].set_index("iso3")["mandatory_fortification"]
    return out.reset_index()


def sth_coverage() -> pd.DataFrame:
    """WHO PCT databank, soil-transmitted helminthiases: national coverage of preventive chemotherapy among school-age
    children, % (implementation, not policy on paper). NaN in a year the country had a population requiring PC is read
    as 0 (no treatment reported); years with no requirement stay NaN. Joined on the file's ISO3 code."""
    path = inp(cfg.INPUTS / "STH_data.xlsx")
    inp(cfg.INPUTS / "STH_data.provenance.json")
    d = pd.read_excel(path, sheet_name="STH_DATA")
    cov = next(c for c in d.columns if str(c).startswith("National coverage, SAC"))
    req = next(
        c
        for c in d.columns
        if str(c).startswith("Population requiring PC") and "Pre-SAC" not in str(c) and "SAC" in str(c)
    )
    d["iso3"] = d["country_code"].astype(str).str.upper()
    d = d[d["iso3"].isin(SSA)].copy()
    d["cov"] = pd.to_numeric(d[cov], errors="coerce").clip(upper=100)
    d["req"] = pd.to_numeric(d[req], errors="coerce")
    # several rows per country-year = several treatment rounds; the year's coverage is the best round (WHO convention)
    g = d.groupby(["iso3", "year"], as_index=False).agg(cov=("cov", "max"), req=("req", "max"))
    value = g["cov"].where(g["cov"].notna(), (g["req"] > 0).map({True: 0.0, False: np.nan}))
    return pd.DataFrame({"iso3": g["iso3"], "year": g["year"].astype(int), "value": value}).dropna(subset=["value"])


def geography() -> pd.DataFrame:
    """Nunn & Puga (2012) terrain variables, time-invariant; used by the context ranking model only."""
    d = pd.read_csv(inp(cfg.INPUTS / "nunn_puga_ruggedness_ssa.csv"))
    inp(cfg.INPUTS / "nunn_puga_ruggedness_ssa.provenance.json")
    return d.rename(
        columns={"isocode": "iso3", "rugged": "geo_rugged", "tropical": "geo_tropical", "dist_coast": "geo_dist_coast"}
    )[["iso3", "geo_rugged", "geo_tropical", "geo_dist_coast"]]


def cross_check_team_list(codes: pd.DataFrame) -> str:
    """The team CSV is provenance only (not valid UTF-8); report whether its 49 names still match the pinned list."""
    path = SCR / "subsaharan_data" / "subsahran_africa_countries.csv"
    if not path.exists():
        return f"team country list not found at {path} (pinned list used)"
    USED_INPUTS.append(path)
    names = pd.read_csv(path, encoding="latin-1")["Country"].tolist()
    known = set(codes["faostat_area_name"]) | set(codes["wb_name"]) | set(codes["display_name"])
    odd = [n for n in names if n not in known]
    return f"team country list: {len(names)} names; {len(names) - len(odd)} match the pinned lookup; unmatched (encoding): {odd}"


# ---- main ---------------------------------------------------------------------
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    codes = load_codes()
    area2iso = dict(zip(codes["faostat_area_code"], codes["iso3"], strict=True))
    iso2_to_iso3 = dict(zip(codes["iso2"], codes["iso3"], strict=True))
    display = dict(zip(codes["iso3"], codes["display_name"], strict=True))
    b = PanelBuilder()

    print("== outcomes: UNICEF women's nutrition (modelled annual)")
    wb = "UNICEF_Global-database_Womens-Nutrition_August-2025_2.xlsx"
    xl = pd.ExcelFile(first_existing(cfg.INPUTS / "unicef" / wb, WID / "cache" / "unicef" / wb))
    for sheet, col in [
        ("underweight", "out_women_underweight_pct"),
        ("overweight", "out_women_overweight_pct"),
        ("anaemia_WRA", "out_anaemia_wra_unicef_pct"),
        ("anaemia_pregnant_women", "out_anaemia_pregnant_pct"),
    ]:
        b.add(
            unicef_sheet(xl, sheet),
            col,
            "outcome",
            f"UNICEF Global database on women's nutrition, Aug-2025 ({sheet}, modelled point estimates)",
        )

    print("== outcomes: FAOSTAT FS (July-2026 release, cached)")
    fs_items = {
        "21043": "out_anaemia_wra_fs_pct",
        "21049": "out_lbw_pct",
        "21025": "out_stunting_u5_pct",
        "21026": "out_wasting_u5_pct",
        "21041": "out_overweight_u5_pct",
        "21044": "out_ebf_0_5mo_pct",
    }
    for code, col in fs_items.items():
        b.add(
            faostat(
                one_file(
                    str(cfg.INPUTS / "faostat" / f"data_FS_item{code}_*.parquet"),
                    str(WID / "cache" / "faostat" / f"data_FS_item{code}_*.parquet"),
                ),
                area2iso,
            ),
            col,
            "outcome",
            f"FAOSTAT FS item {code} (July-2026 release), joined on FAOSTAT area code",
        )

    print("== outcomes: UN IGME 2025 round")
    ig = load_igme()
    for ind, col in [
        ("Neonatal mortality rate", "out_nmr_per1000"),
        ("Infant mortality rate", "out_imr_per1000"),
        ("Under-five mortality rate", "out_u5mr_per1000"),
    ]:
        b.add(igme(ig, ind), col, "outcome", f"UN IGME 2025 round ({ind}, both sexes)")

    print("== features: income")
    b.add(
        wb_current(iso2_to_iso3),
        cfg.INCOME_ALT,
        "feature",
        "World Bank NY.GDP.PCAP.CD via subsaharan_data/GDP_per_capita.csv, joined on ISO2 (series is CURRENT US$ despite the file header)",
    )
    b.add(
        wb_constant(),
        cfg.INCOME,
        "feature",
        "World Bank NY.GDP.PCAP.KD (constant 2015 US$), pinned API pull 2026-09-09 in scaffold/inputs/ with provenance — "
        "the main income measure from v2.0",
    )

    print("== features: context block (pinned World Bank series, v2.0) and the team's confounders")
    ctx = wb_context()
    for col_in, col in [
        ("malaria_incidence_per1000", "feat_malaria_incidence_per1000"),
        ("fertility_rate", "feat_fertility_rate"),
        ("urban_pct", "feat_urban_pct"),
        ("hiv_prev_pct", "feat_hiv_prev_pct"),
        ("employment_pop_pct", "feat_employment_pop_pct"),
        ("health_exp_pc_usd", "feat_health_exp_pc_usd"),
        ("sanitation_basic_pct", "feat_sanitation_basic_pct"),
    ]:
        b.add(
            ctx[["iso3", "year", col_in]].rename(columns={col_in: "value"}).dropna(subset=["value"]),
            col,
            "feature",
            f"{cfg.CONTROL_LABELS[col]} — scaffold/inputs/wb_context_ssa.csv (World Bank API pull 12 Sep 2026)",
            strict=False,
        )
    for col_in, col in [
        ("Unemployment (% of Pop)", "feat_unemployment_pct"),
        ("Hospital Beds Per 1000 People", "feat_hospital_beds_per1000"),
    ]:
        te = team_extra(iso2_to_iso3, col_in)
        if te is not None:
            b.add(
                te,
                col,
                "feature",
                f"{cfg.CONTROL_LABELS[col]} — subsaharan_data/GDP_per_capita.csv, joined on ISO2",
                strict=False,
            )
    b.add(
        sth_coverage(),
        "feat_sth_pc_coverage_sac_pct",
        "feature",
        f"{cfg.CONTROL_LABELS['feat_sth_pc_coverage_sac_pct']} — scaffold/inputs/STH_data.xlsx (WHO PCT databank download, 12 Sep 2026)",
        strict=False,
    )
    b.add(
        dhs_surveys(codes),
        cfg.SURVEY_FLAG,
        "feature",
        "1 = a DHS survey with women's haemoglobin testing in that country-year (DHS API, indicator AN_ANEM_W_ANY, pinned); absent = 0",
        strict=False,
    )

    print("== features: CAHD (FAOSTAT release 7S2026, cached)")
    cahd = one_file(
        str(cfg.INPUTS / "faostat" / "data_CAHD_full_release_7S2026.parquet"),
        str(WID / "cache" / "faostat" / "data_CAHD_full_release_7S2026.parquet"),
    )
    for item, unit_kw, col in [
        ("Cost of a healthy diet (CoHD)", "PPP", "feat_cohd_ppp_per_day"),
        ("Prevalence of unaffordability (PUA)", "%", "feat_pua_pct"),
        ("Number of people unable to afford a healthy diet (NUA)", "million", "feat_nua_million"),
    ]:
        b.add(
            faostat(cahd, area2iso, item=item, unit_kw=unit_kw),
            col,
            "feature",
            f"FAOSTAT CAHD 7S2026: {item}, joined on FAOSTAT area code",
        )

    print("== features: FIES 3-year averages (window centred on its middle year)")
    f3 = fies3()
    for col in [c for c in f3.columns if c.startswith("fies_")]:
        b.add(
            f3[["iso3", "mid_year", col]].rename(columns={"mid_year": "year", col: "value"}),
            "feat_" + col + "_3yr",
            "feature",
            "FAOSTAT FS FIES 3-year average (scaffold/inputs/ssa_fies_3yr_average.csv, rebuilt 8 Sep from the cached July-2026 release)",
        )

    print("== features: GIFNA feature table")
    gi_w = gifna()
    gi_years = gi_w[gi_w["year"].between(YEARS[0], YEARS[-1])]
    b.panel = b.panel.merge(gi_w, on=["iso3", "year"], how="left", validate="one_to_one")
    n_gifna = len([c for c in gi_w.columns if c.startswith("feat_gifna_")])
    b.readiness.append(
        dict(
            group="feature",
            column=f"feat_gifna_* ({n_gifna} columns)",
            source="GIFNA via gifna/build_feature_table.py (policies, programmes, mechanisms; 1999–2025)",
            countries_of_49=gi_years["iso3"].nunique(),
            year_min=int(gi_years["year"].min()),
            year_max=int(gi_years["year"].max()),
            country_year_cells=len(gi_years),
            missing_countries=" ".join(sorted(SSA - set(gi_years["iso3"]))),
        )
    )

    print("== features: GIFNA registry files read directly (policies, programmes & actions, mechanisms)")
    gd, gd_tokens, gd_report, gd_first = gifna_direct.build(
        SCR, cfg.INPUTS / "gifna_cluster_rules.csv", cfg.SSA_ISO3, YEARS, register=inp
    )
    if gd[gd_report["columns"]].isna().any().any():
        raise ValueError("direct GIFNA features must be complete on the grid (zero = no record, never NaN)")
    b.panel = b.panel.merge(gd, on=["iso3", "year"], how="left", validate="one_to_one")
    gd_tokens.to_csv(OUT / "gifna_direct_token_map.csv", index=False)
    b.readiness.append(
        dict(
            group="feature",
            column=f"feat_gd_* ({len(gd_report['columns'])} columns)",
            source="WHO GIFNA registry files read directly by gifna_direct.py (policies, programmes & actions, mechanisms; "
            "clusters from inputs/gifna_cluster_rules.csv; 0 = no record)",
            countries_of_49=int(gd["iso3"].nunique()),
            year_min=YEARS[0],
            year_max=YEARS[-1],
            country_year_cells=int(len(gd)),
            missing_countries="",
        )
    )

    print("== events table (v2.0): dated policy adoption and fortification legislation years")
    events = gd_first.merge(gfdx_years(), on="iso3", how="left", validate="one_to_one")
    events["first_anaemia_policy_year"] = events["first_anaemia_policies_year"]
    events["subregion"] = events["iso3"].map(cfg.SUBREGION)
    events = events.merge(geography(), on="iso3", how="left", validate="one_to_one")
    events.to_csv(OUT / "events.csv", index=False)
    n_pol = int(events["first_anaemia_policy_year"].notna().sum())
    n_wheat = int(events["gfdx_wheat_mandate_year"].notna().sum())
    print(f"  events.csv: {n_pol} countries with a dated anaemia policy, {n_wheat} with a wheat-flour mandate year")

    panel = b.panel.copy()
    panel[cfg.SURVEY_FLAG] = panel[cfg.SURVEY_FLAG].fillna(0.0)  # 0 = no survey that year: complete by construction
    for row in b.readiness:
        if row["column"] == cfg.SURVEY_FLAG:
            row.update(
                countries_of_49=len(SSA),
                country_year_cells=int(len(panel)),
                missing_countries="",
                source=row["source"] + " — filled with 0 elsewhere, so complete on the grid",
            )
    panel.insert(1, "country", panel["iso3"].map(display))
    check_panel_grid(panel)
    ident = float((panel["out_anaemia_wra_unicef_pct"] - panel["out_anaemia_wra_fs_pct"]).abs().max())

    # ---- write outputs ----
    panel_path = OUT / "ssa_panel.csv"
    panel.to_csv(panel_path, index=False)
    (OUT / "ssa_fies_3yr_average.csv").write_bytes((cfg.INPUTS / "ssa_fies_3yr_average.csv").read_bytes())
    rd = pd.DataFrame(b.readiness)
    rd["year_min"] = rd["year_min"].astype("Int64")
    rd["year_max"] = rd["year_max"].astype("Int64")
    rd.to_csv(OUT / "ssa_panel_readiness.csv", index=False)
    sha = sha256_of(panel_path)
    version = sha[:12]
    (OUT / "data_version.txt").write_text(version + "\n", encoding="utf-8")
    try:
        head = subprocess.run(
            ["git", "-C", str(SCR), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        head = None
    manifest = {
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "config_version": cfg.CONFIG_VERSION,
        "data_version": version,
        "panel": {
            "path": panel_path.name,
            "sha256": sha,
            "rows": int(panel.shape[0]),
            "columns": int(panel.shape[1]),
            "bytes": panel_path.stat().st_size,
        },
        "inputs": {
            rel(p): {
                "sha256": sha256_of(p),
                "bytes": p.stat().st_size,
                "mtime": datetime.fromtimestamp(p.stat().st_mtime, UTC).isoformat(timespec="seconds"),
            }
            for p in sorted(set(USED_INPUTS), key=str)
        },
        "events": {
            "path": "events.csv",
            "sha256": sha256_of(OUT / "events.csv"),
            "countries_with_dated_anaemia_policy": n_pol,
            "countries_with_wheat_mandate_year": n_wheat,
        },
        "shared_repo_head": head,
        "checks": {"complete_grid": True, "duplicate_keys": 0, "anaemia_unicef_vs_fs_max_abs_diff": ident},
        "versions": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__},
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    core_out = [cfg.OUTCOME] + list(cfg.SECONDARY)[:2]
    core_feat = [cfg.INCOME, "feat_gifna_policy_count_active"]
    m = panel[panel["year"].between(cfg.YEAR_MIN, cfg.YEAR_MAX)]
    ok = m.dropna(subset=core_out + core_feat)
    fewest = ok.groupby("iso3").size().reindex(sorted(SSA)).fillna(0).astype(int).sort_values().head(10)
    lines = [
        f"# SSA panel — readiness (scaffold {cfg.SCAFFOLD_VERSION}, built {cfg.RUN_DATE}, data version {version})\n",
        f"Panel: {panel.shape[0]} rows ({len(SSA)} countries × {len(YEARS)} years, {YEARS[0]}–{YEARS[-1]}) × {panel.shape[1]} columns. "
        f"File: `{panel_path.name}`; manifest: `MANIFEST.json`. Script: `scaffold/00_assemble_panel.py`.\n",
        "| group | column | source | countries (of 49) | years | cells | countries without values |\n|---|---|---|---:|---|---:|---|",
    ]
    for r in rd.itertuples():
        lines.append(
            f"| {r.group} | {r.column} | {r.source} | {r.countries_of_49} | {r.year_min}–{r.year_max} | "
            f"{r.country_year_cells} | {r.missing_countries or '—'} |"
        )
    lines += [
        "",
        "Events (v2.0, `events.csv`, one row per country): first dated anaemia-cluster policy year per registry file and across files "
        "(survey-window rows never date an event), GFDx mandatory wheat-/maize-flour fortification years and status, UNICEF sub-region, "
        "Nunn–Puga terrain variables.",
        f"\nIdentical series check: `out_anaemia_wra_unicef_pct` vs `out_anaemia_wra_fs_pct` max |difference| = {ident:g} "
        "(the UNICEF workbook republishes the same WHO 2025 edition; not independent).",
        f"\n## Candidate modelling frame ({cfg.YEAR_MIN}–{cfg.YEAR_MAX}): rows with all of {core_out + core_feat} non-null: "
        f"{len(ok)} of {len(m)} country-years, {ok['iso3'].nunique()} countries.",
        "\nCountries with fewest complete rows: " + ", ".join(f"{k} ({v})" for k, v in fewest.items()),
        "\n" + cross_check_team_list(codes),
        "\n## GIFNA registry files read directly (`gifna_direct.py`; v2.0 adds per-file anaemia and fortification families and the dated events table `events.csv`)\n",  # noqa: E501
        "Source: WHO GIFNA (https://gifna.who.int/), per-country exports of 3–5 Sep 2026 combined by `gifna/combine_gifna_raw.py`. "
        "Features come from the controlled topic / theme / target-group columns only (rules: `inputs/gifna_cluster_rules.csv`; "
        "every token and its clusters: `gifna_direct_token_map.csv`). Policies are active from start to end year (open end = still active); "
        "undated GNPR questionnaire rows are placed in their survey window (2009–2010, 2016–2017); other undated rows are excluded.\n",
        *gifna_direct.report_lines(gd_report),
    ]
    (OUT / "ssa_panel_readiness.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:2]))
    print(f"panel {panel.shape} → {panel_path} | data version {version} | anaemia UNICEF vs FS max diff {ident:g}")


if __name__ == "__main__":
    sys.exit(main())
