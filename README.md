# Primary Pea — WiD 2026 Datathon: "What's Cooking"

> [!NOTE]
> repo to be renamed before submission

> ⟨ *One-sentence research question — **to be set*** ⟩

Team submission and portfolio repository for the Women in Data 2026 Datathon: FAOSTAT-based analysis of food security and nutrition.

## Findings
> ⟨ *2–3 headline findings with claim tags — **to be filled** at analysis freeze (?Aug 30?)* ⟩

## Repository map
- `notebooks/` — the analysis, fresh-runtime-safe top to bottom
- `dashboard/` — interactive companion to the video
- `figures/` — static visuals as presented
- `docs/` — methodology, data notes and known FAOSTAT sharp edges
- `scripts/` — release checks (`preflip_scan.sh`) and small utilities
- `data/` — not committed; `data/README.md` documents every source and how to re-pull it
> - [ *more as they come* ]

## Directions for Reproducibility

### For Python Notebooks
1. Set `FAOSTAT_USER` + `FAOSTAT_PASS` as env vars or Colab Secrets.
2. Run `notebooks/` in listed order — cell 1 of each is the shared bootstrap (`notebooks/bootstrap_cell.py`), which handles auth and guards a known API bug in `faostat==2.0.1`.
3. Data sources, domains and release vintages: `docs/data-sources.md`.

### For R [? ?]
> ⟨ ***To be added*** ⟩

## Data discipline
FBS "food supply" means availability, not intake, and is captioned as such. Food-security pulls filter `Element == 'Value'`. Every reported number is tagged [E] exact from API · [C] chart-read · [X] external.

## Team
> Primary Pea — ⟨ *each member adds their own credit line as they'd like to be publicly credited* ⟩

## Visibility
Private while we work; **this is the repo that gets published** — planned public at submission (exact date ratified at track lock) as the team's portfolio artifact. Only work deliberately copied here from the scratchpad appears. 

Write for readers; `scripts/preflip_scan.sh` gates the flip and blocks on hits.
