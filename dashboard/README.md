# dashboard/ — The Delivery Gap

Live at <https://primary-pea.github.io/dashboard/> (page source in the [`primary-pea/dashboard`](https://github.com/primary-pea/dashboard) repo). Built by Saarah Hossain.

**What it shows.** A map of the 49 countries coloured by any outcome, its change, the policies on the books in any registry cluster, the gap against what context predicts, or the concern score; documents and blood on one time axis, for the region or any country; the scatter that has no tilt; the four headline numbers; the 28-row ladder, the event studies, the leave-one-out validation and the 336-specification curve with their own controls; the concern watchlist with rank stability; and the 47 cluster rules themselves. Every panel follows a filter bar; the URL carries the state.

- [`build_data.py`](build_data.py) — writes the four JSON files the page reads (`meta`, `countries`, `series`, `model`) from [`scaffold/results/`](../scaffold/results/), [`derived/`](../derived/) and [`scaffold/inputs/gifna_cluster_rules.csv`](../scaffold/inputs/gifna_cluster_rules.csv). Run it from anywhere after a pipeline re-run and commit [`data/`](data/).
- [`data/`](data/) — the snapshot the live page is serving (scaffold v2.0, data version `afe63e46c26b`).

Nothing is computed in the browser: every number on the page is in one of these files.
