# gifna/ — the WHO policy registry

What goes here (Tiana):

- `gifna_policies.csv`, `gifna_programmes_and_actions.csv`, `gifna_mechanisms.csv` — the per-country GIFNA exports of 3–5 September 2026, combined and de-duplicated
- `combine_gifna_raw.py` — builds the three files from the raw exports (which are not committed; see `derived/DATA_ACQUISITION.md`)
- `build_feature_table.py` and `gifna_feature_table.csv` — the country-year feature table, 1999–2025 (the `feat_gifna_*` columns of the panel)
- the feature ledger, if it is a document

The pipeline reads this folder **by name** from the repo root (`scaffold/00_assemble_panel.py`, `scaffold/gifna_direct.py`), so the file names above must stay as they are.
