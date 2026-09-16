# How this repo was filled

> The pre-submission handout, kept as the record of who was asked for what. Every folder it names is now filled; where a planned file name changed on landing, the link below points at the file that exists.

The repo is public at submission. Three rules that apply to everything:

1. **No person's name in any file or folder name.** Names go in READMEs and in git history, not in paths. `Hope_EDA.Rmd` becomes [`first-pass.Rmd`](eda/income-and-context/first-pass.Rmd); a Colab called `Unicef_Women's_nutrition.ipynb` lands as [`Unicef_Women_s_nutrition.ipynb`](eda/womens-nutrition-unicef/Unicef_Women_s_nutrition.ipynb).
2. **Notebooks are committed with their outputs**, so they read without running. R notebooks come with the knitted HTML or PDF next to them.
3. **Data a notebook reads is either under 1 MB and in the same folder, or a path into [`derived/`](derived/), [`gifna/`](gifna/) or [`subsaharan_data/`](subsaharan_data/).** Nothing licensed, nothing bulk — [`derived/DATA_ACQUISITION.md`](derived/DATA_ACQUISITION.md) says how the bulk pulls are re-acquired.

| Who | Pushes | Where |
|---|---|---|
| **Tiana** | [`combine_gifna_raw.py`](gifna/combine_gifna_raw.py), [`build_feature_table.py`](gifna/build_feature_table.py), [`gifna_feature_table.csv`](gifna/gifna_feature_table.csv), [`gifna_policies.csv`](gifna/gifna_policies.csv), [`gifna_programmes_and_actions.csv`](gifna/gifna_programmes_and_actions.csv), [`gifna_mechanisms.csv`](gifna/gifna_mechanisms.csv) | [`gifna/`](gifna/) |
| **Hope** | [`GDP_per_capita.csv`](subsaharan_data/GDP_per_capita.csv), [`food_insecurity.csv`](subsaharan_data/food_insecurity.csv), [`subsahran_africa_countries.csv`](subsaharan_data/subsahran_africa_countries.csv) | [`subsaharan_data/`](subsaharan_data/) |
| **Hope** | [`food-insecurity.Rmd`](eda/food-insecurity/food-insecurity.Rmd), [`food-insecurity-by-gender.Rmd`](eda/food-insecurity/food-insecurity-by-gender.Rmd) and its [PDF](eda/food-insecurity/food-insecurity-by-gender.pdf) | [`eda/food-insecurity/`](eda/food-insecurity/) |
| **Hope** | [`world-bank-income.Rmd`](eda/income-and-context/world-bank-income.Rmd), [`first-pass.Rmd`](eda/income-and-context/first-pass.Rmd) | [`eda/income-and-context/`](eda/income-and-context/) |
| **Alison** | [`Unicef_Women_s_nutrition.ipynb`](eda/womens-nutrition-unicef/Unicef_Women_s_nutrition.ipynb), with outputs (the 194-country concern score lives here) | [`eda/womens-nutrition-unicef/`](eda/womens-nutrition-unicef/) |
| **Alison** | [`Food Balances Exploration.ipynb`](eda/faostat-food-balances/Food%20Balances%20Exploration.ipynb) | [`eda/faostat-food-balances/`](eda/faostat-food-balances/) |
| **Alison** | [`FAOSTAT CoAHD Exploration.ipynb`](eda/faostat-diet-cost/FAOSTAT%20CoAHD%20Exploration.ipynb) | [`eda/faostat-diet-cost/`](eda/faostat-diet-cost/) |
| **Ramya** | [`script.md`](presentation/script.md); the deck as [`deck-DRAFT1.pdf`](presentation/deck-DRAFT1.pdf) | [`presentation/`](presentation/) |
| **Saarah** | [`faostat-overview.ipynb`](eda/faostat-overview/faostat-overview.ipynb) | [`eda/faostat-overview/`](eda/faostat-overview/) |
| **Saarah** | [`scaffold/`](scaffold/), [`derived/`](derived/), [`dashboard/`](dashboard/), [`docs/`](docs/), this file, the README | — |

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
