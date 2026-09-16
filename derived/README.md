# derived/ — the panel

The product of [`scaffold/00_assemble_panel.py`](../scaffold/00_assemble_panel.py), committed so nobody needs to rebuild it to read it. Twelve sources, one guarded join that refuses duplicate keys, undeclared gaps and an incomplete grid.

- [`ssa_panel.csv`](ssa_panel.csv) — 49 sub-Saharan African countries × 2000–2025, 1,274 rows × 174 columns: `out_*` outcomes (anaemia, underweight, overweight, child growth and mortality), `feat_*` features (income, the context block, the GIFNA registry stocks by topic cluster, the team feature table), `geo_*` terrain
- [`events.csv`](events.csv) — one row per country: first dated anaemia policy, wheat-flour fortification mandate year
- [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) — every column, its source and its reading rule
- [`MANIFEST.json`](MANIFEST.json) — the SHA-256 of every input and of the panel; [`data_version.txt`](data_version.txt) — the first twelve characters of the panel hash (`afe63e46c26b`)
- [`ssa_panel_readiness.md`](ssa_panel_readiness.md) / [`.csv`](ssa_panel_readiness.csv) — coverage of every column by year; [`gifna_direct_token_map.csv`](gifna_direct_token_map.csv) — how registry tokens map to clusters; [`ssa_fies_3yr_average.csv`](ssa_fies_3yr_average.csv)

**How every source was obtained, and what the raw data we did not commit looks like: [`DATA_ACQUISITION.md`](DATA_ACQUISITION.md).**

Read it with `pandas.read_csv("derived/ssa_panel.csv")` or `readr::read_csv("derived/ssa_panel.csv")`; the dictionary says what each column means.
