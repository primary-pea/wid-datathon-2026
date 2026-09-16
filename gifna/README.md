# gifna/ — the WHO policy registry

The team's copy of the WHO Global database on the Implementation of Food and Nutrition Action ([GIFNA](https://gifna.who.int/)): what governments have written down about nutrition, one record per policy, programme or coordination mechanism. Built by Tatiana Gabel.

- [`gifna_policies.csv`](gifna_policies.csv) (5,580 rows), [`gifna_programmes_and_actions.csv`](gifna_programmes_and_actions.csv) (8,442), [`gifna_mechanisms.csv`](gifna_mechanisms.csv) (131) — the per-country exports of 3–5 September 2026, combined and de-duplicated by [`combine_gifna_raw.py`](combine_gifna_raw.py); the raw per-country files are not committed (see [`derived/DATA_ACQUISITION.md`](../derived/DATA_ACQUISITION.md)).
- [`build_feature_table.py`](build_feature_table.py) → [`gifna_feature_table.csv`](gifna_feature_table.csv) — one row per country-year, 1999–2025: counts of active policies, programmes and mechanisms, cumulative exposure, and the six-flag anaemia programming composite. These become the `feat_gifna_*` columns of the panel.

**How the pipeline uses it.** [`scaffold/gifna_direct.py`](../scaffold/gifna_direct.py) reads the three files directly and assigns every record to topic clusters by matching its controlled-vocabulary tokens against 47 patterns ([`scaffold/inputs/gifna_cluster_rules.csv`](../scaffold/inputs/gifna_cluster_rules.csv)); the model's dose is the number of **dated policies in the anaemia cluster** in force in a year. The feature table supplies the alternative doses on the ladder.

**What the registry cannot say.** It records what was written, not what reached anyone: three in four programme records carry no date, and no record carries coverage. That gap is the finding.

The pipeline reads this folder by name from the repo root, so the file names must stay as they are.
