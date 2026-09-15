# dashboard/ — The Delivery Gap

Live at https://primary-pea.github.io/dashboard/ (its page source is the `primary-pea/dashboard` repo). Kept by Saarah.

- `build_data.py` — writes the four JSON files the page reads (`meta`, `countries`, `series`, `model`) from `scaffold/results/`, `derived/` and `scaffold/inputs/gifna_cluster_rules.csv`; run it after any pipeline re-run and commit `data/`
- `data/` — the snapshot the live page is serving (scaffold v2.0, data version `afe63e46c26b`)

Nothing is computed in the browser: every number on the page is one of these files.
