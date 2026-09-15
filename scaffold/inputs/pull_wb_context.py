"""Pull the World Bank context series used by the scaffold into inputs/wb_context_ssa.csv with a provenance file.

Replicable input: run from the scaffold folder (``../.venv/bin/python inputs/pull_wb_context.py``); the CSV and the
provenance JSON are committed so any clone builds the panel without network access. Indicators (all annual, WDI):
malaria incidence, fertility, urbanisation, HIV prevalence, employment-to-population, health expenditure per capita,
and (12 Sep, late) basic sanitation and open defecation from the WHO/UNICEF Joint Monitoring Programme.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as cfg  # noqa: E402

INDICATORS = {
    "SH.MLR.INCD.P3": "malaria_incidence_per1000",
    "SP.DYN.TFRT.IN": "fertility_rate",
    "SP.URB.TOTL.IN.ZS": "urban_pct",
    "SL.EMP.TOTL.SP.ZS": "employment_pop_pct",
    "SH.DYN.AIDS.ZS": "hiv_prev_pct",
    "SH.XPD.CHEX.PC.CD": "health_exp_pc_usd",
    "SH.STA.BASS.ZS": "sanitation_basic_pct",
    "SH.STA.ODFC.ZS": "open_defecation_pct",
}
URL = "https://api.worldbank.org/v2/country/all/indicator/{ind}?format=json&per_page=20000&date=2000:2025"


def fetch(ind: str) -> tuple[dict, list]:
    err = None
    for _ in range(4):
        try:
            meta, data = json.load(urllib.request.urlopen(URL.format(ind=ind), timeout=120))
            return meta, data
        except Exception as e:  # transient API errors: retry
            err = e
    raise RuntimeError(f"{ind}: {err!r}")


def main() -> None:
    ssa = set(cfg.SSA_ISO3)
    rows, prov_ind = [], {}
    for ind, name in INDICATORS.items():
        meta, data = fetch(ind)
        n = 0
        for r in data:
            if r["countryiso3code"] in ssa and r["value"] is not None:
                rows.append(
                    {
                        "iso3": r["countryiso3code"],
                        "year": int(r["date"]),
                        "indicator": name,
                        "value": float(r["value"]),
                    }
                )
                n += 1
        prov_ind[ind] = {
            "column": name,
            "label": data[0]["indicator"]["value"] if data else None,
            "rows": n,
            "source_lastupdated": meta.get("lastupdated"),
        }
        print(f"{ind:22s} {name:26s} {n} rows")
    df = pd.DataFrame(rows).pivot_table(index=["iso3", "year"], columns="indicator", values="value").reset_index()
    df = df[["iso3", "year"] + list(INDICATORS.values())]
    out = cfg.INPUTS / "wb_context_ssa.csv"
    df.to_csv(out, index=False)
    prov = {
        "file": out.name,
        "source": "World Bank WDI via api.worldbank.org/v2 (json, per_page=20000, date=2000:2025), pulled by inputs/pull_wb_context.py",
        "retrieved_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "filter": "49 SSA iso3 from config.SSA_ISO3; null values dropped; one column per indicator",
        "indicators": prov_ind,
        "rows": int(len(df)),
        "columns": list(df.columns),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    }
    (cfg.INPUTS / "wb_context_ssa.provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print(f"wrote {out} {df.shape}; provenance updated")


if __name__ == "__main__":
    main()
