# Filling this repo — who pushes what, by 18:30 ET on 15 September

The repo is public at submission. Three rules that apply to everything:

1. **No person's name in any file or folder name.** Names go in READMEs and in git history, not in paths. `Hope_EDA.Rmd` becomes `first-pass.Rmd`; a Colab called `Unicef_Women's_nutrition.ipynb` becomes `womens-nutrition-concern-score.ipynb`.
2. **Notebooks are committed with their outputs**, so they read without running. R notebooks come with the knitted HTML or PDF next to them.
3. **Data a notebook reads is either under 1 MB and in the same folder, or a path into `derived/`, `gifna/` or `subsaharan_data/`.** Nothing licensed, nothing bulk — `derived/DATA_ACQUISITION.md` says how the bulk pulls are re-acquired.

| Who | Pushes | Where |
|---|---|---|
| **Tiana** | `combine_gifna_raw.py`, `build_feature_table.py`, `gifna_feature_table.csv`, `gifna_policies.csv`, `gifna_programmes_and_actions.csv`, `gifna_mechanisms.csv`, plus the feature ledger if it is a document | `gifna/` |
| **Hope** | `GDP_per_capita.csv`, `food_insecurity.csv`, `subsahran_africa_countries.csv` | `subsaharan_data/` |
| **Hope** | `food_insecurity_data.Rmd`, `notable_countries_FI_by_gender.Rmd` and its PDF | `eda/food-insecurity/` |
| **Hope** | `world_bank_data.Rmd`, `Hope_EDA.Rmd` (renamed for what it does, e.g. `first-pass.Rmd`) | `eda/income-and-context/` |
| **Alison** | the UNICEF women's-nutrition Colab, downloaded as `.ipynb` with outputs (the 194-country concern score lives here) | `eda/womens-nutrition-unicef/` |
| **Alison** | the FAOSTAT food-balances Colab | `eda/faostat-food-balances/` |
| **Alison** | the FAOSTAT cost-of-a-healthy-diet Colab | `eda/faostat-diet-cost/` |
| **Ramya** | the final script as `script.md`, the deck exported as `deck.pdf`, `captions.srt` once cut, `video.md` with the link | `presentation/` |
| **Saarah** | the August FAOSTAT first pass | `eda/faostat-overview/` |
| **Saarah** | `scaffold/`, `derived/`, `dashboard/`, `docs/`, this file, the README | — |

Each folder already has a README that lists what belongs in it; replace the "this goes here" list with a line or two about what the files are.

## How to push

```
git clone https://github.com/primary-pea/wid-datathon-2026.git
cd wid-datathon-2026
# copy your files into the folder named above, then:
git add gifna/            # or eda/food-insecurity/ etc.
git commit -m "gifna: registry exports, combine and feature-table scripts"
git push
```

You need to be a collaborator on the repo (you will get the invitation by email). If you cannot push in time, drop the files in the shared repo as before and Saarah copies them across with your name in the commit message.
