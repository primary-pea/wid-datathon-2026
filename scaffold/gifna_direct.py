"""gifna_direct — country × year features derived straight from the three GIFNA registry files (scaffold v1.2, 2026-09-11).

Why: the model should not depend only on a pre-built feature table. This module reads the combined registry exports
(``gifna/gifna_policies.csv``, ``gifna/gifna_programmes_and_actions.csv``, ``gifna/gifna_mechanisms.csv``, produced by
``gifna/combine_gifna_raw.py`` from the per-country GIFNA downloads of 3–5 Sep 2026) and derives deterministic features
from their CONTROLLED columns only (policy ``Topics``; programme ``Theme``, ``Topic``, ``Target_Group``,
``Micronutrient``; mechanism ``Topics`` and ``Type``). Free-text descriptions are never read, so language is not an issue.

Topic clusters: every controlled token is matched (case-insensitive regex on the token, never on prose) against
``inputs/gifna_cluster_rules.csv``; a token can fall into several clusters; unmatched tokens are reported, not guessed.
A record (policy, programme action, mechanism) belongs to a cluster if any of its tokens does; it is counted once per
cluster, so nothing is double-counted when a record carries several matching tokens.

Dating (the unit of time is the calendar year):
  policies    — active from ``Start_Year`` to ``End_Year`` inclusive; no end year = still active.
  programmes  — the same when ``Start_Year`` is present. Undated GNPR questionnaire rows (title starts with
                "GNPR 2009-2010" or "GNPR 2016-2017") are placed in their survey window, as the team decided on
                10 Sep; undated rows of any other kind are excluded and counted in the report.
  mechanisms  — active from ``StartYear`` onward; undated mechanisms are excluded and counted.

Two feature families per cluster (and for ``all`` records, per source file, and — v2.0 — per cluster × source file for the
anaemia and fortification clusters, e.g. ``feat_gd_stock_anaemia_policies``; ``first_years()`` dates events from dated records only):
  ``feat_gd_stock_<c>``    — number of records of cluster c active in the year (an integer stock).
  ``feat_gd_logstock_<c>`` — log(1 + stock), the normalised version (a 20-programme country no longer dominates).
  ``feat_gd_any_<c>``      — 1 once any record of cluster c has started (absorbing: it never switches back to 0).
Zero means "no record in the registry", which is the literal reading of the source; it is not imputed.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

CLUSTERS = [
    "anaemia",
    "fortification",
    "micronutrient",
    "maternal",
    "iycf",
    "wasting_stunting",
    "infection",
    "food_security",
    "ncd_diet",
    "schools_education",
    "governance",
]
SOURCES: dict[str, dict] = {
    "policies": dict(
        file="gifna_policies.csv",
        id="Policy_Id",
        iso3="Iso3Code",
        start="Start_Year",
        end="End_Year",
        title="Policy_Title",
        fields=["Topics"],
    ),
    "programmes": dict(
        file="gifna_programmes_and_actions.csv",
        id="Action_Id",
        iso3="Iso3Code",
        start="Start_Year",
        end="End_Year",
        title="Programme_Title",
        fields=["Theme", "Topic", "Target_Group", "Micronutrient"],
    ),
    "mechanisms": dict(
        file="gifna_mechanisms.csv",
        id="Id",
        iso3="ISO3Code",
        start="StartYear",
        end=None,
        title="Title",
        fields=["Topics"],
    ),
}
SURVEY_WINDOWS = {"GNPR 2009-2010": (2009, 2010), "GNPR 2016-2017": (2016, 2017)}
OPEN_END = 9999
PREFIX = "feat_gd_"
PER_SOURCE_CLUSTERS = ["anaemia", "fortification"]  # v2.0: these clusters also get per-source-file families
DATED = (
    "dated",
    "dated_open_end",
)  # records with a real start year (survey-window rows are excluded from event dating)


def split_tokens(value: str) -> list[str]:
    return [t.strip() for t in str(value).split("|") if t.strip()]


def load_rules(path: Path) -> list[tuple[str, re.Pattern]]:
    rules = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    bad = sorted(set(rules["cluster"]) - set(CLUSTERS))
    if bad:
        raise ValueError(f"unknown clusters in {path.name}: {bad}")
    return [(r.cluster, re.compile(r.pattern, re.IGNORECASE)) for r in rules.itertuples()]


def map_token(token: str, rules: list[tuple[str, re.Pattern]]) -> set[str]:
    return {c for c, rx in rules if rx.search(token)}


def _year(v: str) -> int | None:
    v = str(v).strip()
    return int(v) if v.isdigit() else None


def read_source(scr: Path, name: str, rules, ssa: set[str], register=None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """One registry file → records (iso3, key, start, end, clusters, dating) + its token map + counts."""
    spec = SOURCES[name]
    path = scr / "gifna" / spec["file"]
    if register is not None:
        register(path)
    raw = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig", low_memory=False)
    counts: dict = {"rows_in_file": int(len(raw))}
    d = raw[raw[spec["iso3"]].isin(ssa)].copy()
    counts["rows_in_ssa"] = int(len(d))
    dup = d.duplicated([spec["iso3"], spec["id"]]).sum()
    counts["duplicate_ids_dropped"] = int(dup)
    d = d.drop_duplicates([spec["iso3"], spec["id"]], keep="first")

    # tokens → clusters
    token_mentions: dict[tuple[str, str], int] = {}
    clusters_per_row: list[set[str]] = []
    for row in d.itertuples(index=False):
        cl: set[str] = set()
        for f in spec["fields"]:
            for tok in split_tokens(getattr(row, f)):
                token_mentions[(f, tok)] = token_mentions.get((f, tok), 0) + 1
                cl |= map_token(tok, rules)
        if name == "mechanisms":
            cl.add("governance")
        clusters_per_row.append(cl)
    token_map = pd.DataFrame(
        [
            dict(
                source=name,
                field=f,
                token=t,
                mentions=n,
                clusters="|".join(sorted(map_token(t, rules))) or ("governance" if name == "mechanisms" else ""),
            )
            for (f, t), n in sorted(token_mentions.items(), key=lambda kv: (-kv[1], kv[0]))
        ]
    )

    # dating
    starts, ends, rule = [], [], []
    for row in d.itertuples(index=False):
        s = _year(getattr(row, spec["start"]))
        e = _year(getattr(row, spec["end"])) if spec["end"] else None
        if s is not None:
            starts.append(s)
            ends.append(e if e is not None and e >= s else OPEN_END)
            rule.append("dated" if e is not None and e >= s else "dated_open_end")
        else:
            win = next((w for k, w in SURVEY_WINDOWS.items() if str(getattr(row, spec["title"])).startswith(k)), None)
            if name == "programmes" and win is not None:
                starts.append(win[0])
                ends.append(win[1])
                rule.append("survey_window")
            else:
                starts.append(None)
                ends.append(None)
                rule.append("undated_excluded")
    rec = pd.DataFrame(
        dict(
            source=name,
            iso3=d[spec["iso3"]].values,
            key=[f"{name}:{k}" for k in d[spec["id"]].values],
            start=starts,
            end=ends,
            dating=rule,
            clusters=clusters_per_row,
        )
    )
    counts.update(
        {k: int((rec["dating"] == k).sum()) for k in ["dated", "dated_open_end", "survey_window", "undated_excluded"]}
    )
    counts["records_used"] = int((rec["dating"] != "undated_excluded").sum())
    counts["countries_with_records"] = int(rec.loc[rec["dating"] != "undated_excluded", "iso3"].nunique())
    counts["tokens"] = int(len(token_map))
    counts["tokens_unmapped"] = int((token_map["clusters"] == "").sum()) if len(token_map) else 0
    counts["mentions_unmapped_share"] = (
        float(token_map.loc[token_map["clusters"] == "", "mentions"].sum() / token_map["mentions"].sum())
        if len(token_map)
        else 0.0
    )
    return rec, token_map, counts


def _expand(rec: pd.DataFrame, years: list[int], absorbing: bool) -> pd.DataFrame:
    """Long table (iso3, year, cluster, key) of records active in the year (stock) or started by the year (any)."""
    r = rec[rec["dating"] != "undated_excluded"]
    y0, y1 = years[0], years[-1]
    rows = []
    for row in r.itertuples(index=False):
        lo = max(int(row.start), y0)
        hi = y1 if absorbing else min(int(row.end), y1)
        if lo > hi:
            continue
        groups = (
            list(row.clusters)
            + ["all", row.source]
            + [f"{c}_{row.source}" for c in row.clusters if c in PER_SOURCE_CLUSTERS]
        )
        for t in range(lo, hi + 1):
            for g in groups:
                rows.append((row.iso3, t, g, row.key))
    return pd.DataFrame(rows, columns=["iso3", "year", "group", "key"])


def build(scr: Path, rules_path: Path, ssa: list[str], years: list[int], register=None):
    """→ (wide features on the full iso3 × year grid, token map, report). ``register`` records inputs for the manifest."""
    if register is not None:
        register(rules_path)
    rules = load_rules(rules_path)
    ssa_set, years = set(ssa), list(years)
    recs, maps, report = [], [], {}
    for name in SOURCES:
        rec, tm, counts = read_source(scr, name, rules, ssa_set, register)
        recs.append(rec)
        maps.append(tm)
        report[name] = counts
    rec = pd.concat(recs, ignore_index=True)
    token_map = pd.concat(maps, ignore_index=True)

    grid = pd.MultiIndex.from_product([sorted(ssa_set), years], names=["iso3", "year"])
    combos = [f"{c}_{s}" for c in PER_SOURCE_CLUSTERS for s in SOURCES]
    groups = CLUSTERS + ["all"] + list(SOURCES) + combos
    stock = _expand(rec, years, absorbing=False).groupby(["iso3", "year", "group"])["key"].nunique()
    stock = stock.unstack("group").reindex(grid).reindex(columns=groups).fillna(0).astype(int)
    ever = _expand(rec, years, absorbing=True).groupby(["iso3", "year", "group"])["key"].nunique()
    ever = (ever.unstack("group").reindex(grid).reindex(columns=groups).fillna(0) > 0).astype(int)

    out = pd.DataFrame(index=grid)
    for g in groups:
        out[f"{PREFIX}stock_{g}"] = stock[g]
        if g in CLUSTERS or g == "all" or g in combos:
            out[f"{PREFIX}logstock_{g}"] = np.log1p(stock[g].astype(float))
        out[f"{PREFIX}any_{g}"] = ever[g]
    out = out.reset_index()

    used = rec[rec["dating"] != "undated_excluded"]
    report["clusters"] = {c: int(used["clusters"].apply(lambda s, c=c: c in s).sum()) for c in CLUSTERS}
    report["records_without_cluster"] = int(used["clusters"].apply(len).eq(0).sum())
    report["countries_zero_records"] = {
        name: sorted(ssa_set - set(used.loc[used["source"] == name, "iso3"])) for name in SOURCES
    }
    report["columns"] = [c for c in out.columns if c.startswith(PREFIX)]
    return out, token_map, report, first_years(rec, ssa_set)


def first_years(rec: pd.DataFrame, ssa: set[str]) -> pd.DataFrame:
    """One row per country: the first start year of a dated record, per cluster in PER_SOURCE_CLUSTERS, per source file
    and across all files. Survey-window and undated rows never date an event. NaN = no dated record."""
    r = rec[rec["dating"].isin(DATED)].copy()
    out = pd.DataFrame({"iso3": sorted(ssa)}).set_index("iso3")
    for c in PER_SOURCE_CLUSTERS:
        rc = r[r["clusters"].apply(lambda s, c=c: c in s)]
        for s in SOURCES:
            out[f"first_{c}_{s}_year"] = rc[rc["source"] == s].groupby("iso3")["start"].min()
        out[f"first_{c}_any_file_year"] = rc.groupby("iso3")["start"].min()
    return out.reset_index()


def report_lines(report: dict) -> list[str]:
    lines = [
        "| source | rows in file | rows in the 49 | records used | dated | open end | survey window | "
        "undated, excluded | countries with records | tokens | unmapped tokens (share of mentions) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in SOURCES:
        c = report[name]
        lines.append(
            f"| {name} | {c['rows_in_file']} | {c['rows_in_ssa']} | {c['records_used']} | {c['dated']} | {c['dated_open_end']} | "
            f"{c['survey_window']} | {c['undated_excluded']} | {c['countries_with_records']} | {c['tokens']} | "
            f"{c['tokens_unmapped']} ({c['mentions_unmapped_share']:.1%}) |"
        )
    lines.append("")
    lines.append(
        "Records per cluster (a record can sit in several): "
        + ", ".join(f"{k} {v}" for k, v in report["clusters"].items())
        + f"; records in no cluster: {report['records_without_cluster']}."
    )
    zero = {k: v for k, v in report["countries_zero_records"].items() if v}
    if zero:
        lines.append(
            "Countries with no usable record in a file (their features are 0 there): "
            + "; ".join(f"{k}: {' '.join(v)}" for k, v in zero.items())
            + "."
        )
    return lines


if __name__ == "__main__":  # standalone mapping pass: python gifna_direct.py [shared-repo-dir]
    import sys

    import config as cfg

    scr = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "miscP" / "parent-primary-pea" / "misc-scratchpads-etc"
    feats, tm, rep, fy = build(scr, cfg.INPUTS / "gifna_cluster_rules.csv", cfg.SSA_ISO3, list(cfg.YEARS))
    print("\n".join(report_lines(rep)))
    print(f"\nfeatures {feats.shape}; columns: {len(rep['columns'])}")
    un = tm[tm["clusters"] == ""].sort_values("mentions", ascending=False)
    print(f"\nUNMAPPED tokens: {len(un)} (top 40 by mentions)")
    for r in un.head(40).itertuples():
        print(f"  {r.mentions:4d} | {r.source}.{r.field} | {r.token}")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if out:
        tm.to_csv(out, index=False)
        print(f"token map → {out}")
