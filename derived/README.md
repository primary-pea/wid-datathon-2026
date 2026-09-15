# derived/ — the panel

The product of `scaffold/00_assemble_panel.py`, committed so nobody needs to rebuild it to read it:

- `ssa_panel.csv` — 49 sub-Saharan African countries × 2000–2025, 1,274 rows × 174 columns: `out_*` outcomes, `feat_*` features (income, context, the GIFNA registry stocks by topic cluster, the team feature table), `geo_*` terrain
- `events.csv` — one row per country: first dated anaemia policy, wheat-flour fortification mandate year
- `DATA_DICTIONARY.md` — every column, its source and its reading rule
- `MANIFEST.json` — the SHA-256 of every input and of the panel; `data_version.txt` — the first twelve characters of the panel hash
- `ssa_panel_readiness.md` / `.csv` — coverage of every column by year; `gifna_direct_token_map.csv` — how registry tokens map to clusters; `ssa_fies_3yr_average.csv`

**How every source was obtained, and what the raw data we did not commit looks like: [`DATA_ACQUISITION.md`](DATA_ACQUISITION.md).**

Kept by Saarah; arrives with the freeze copy.
