# derived/ — team data contract & distribution
Snapshot once, read many. Consumers never need FAOSTAT auth.

- Parquet, one table per topic, lowercase_snake names.
- Schema: iso3 · year · indicator · unit · sex (where split) · value · source_release · claim_tag

Versioning: data_version.txt here (e.g. 2026-08-26a). Figures and the dashboard cite the version they read. Tagged + FROZEN at analysis freeze (~Aug 30); post-freeze changes need a team ping.

Read:
- RStudio: arrow::read_parquet("derived/<table>.parquet")  (repo clone)
- Colab:   pd.read_parquet on the Drive mirror of this folder (synced by Sarah at each release — no git, no tokens)

Raw bulk pulls: shared Drive, not git. MICS microdata: licensed per registered user — never committed, never in the shared Drive; its survey-weighted aggregates are published here instead.
