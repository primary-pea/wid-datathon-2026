# eda/ — exploration, by topic

Notebooks are committed with outputs; R notebooks come with their knitted HTML or PDF. Open `eda.Rproj` to work on the R notebooks as one project.

| Folder | Question it explored | Data | Files | Who | What it fed |
|---|---|---|---|---|---|
| `faostat-overview/` | what FAOSTAT holds for the 49 countries, first pass | FAOSTAT FS suite | `faostat-overview.ipynb` | Saarah | the choice of outcome series and the panel design |
| `faostat-food-balances/` | food balances across the region | FAOSTAT FBS | `food-balances.ipynb` | Alison | data slide 1 |
| `faostat-diet-cost/` | cost and affordability of a healthy diet | FAOSTAT CAHD | `diet-cost-coahd.ipynb` | Alison | the `feat_pua_pct` sensitivity row |
| `womens-nutrition-unicef/` | where women's nutrition indicators are most concerning — the 194-country concern score | UNICEF Global Database, Women's Nutrition | `womens-nutrition-concern-score.ipynb` | Alison | Finding 1; reproduced on the 49 countries in `scaffold/08_concern_score.py` |
| `food-insecurity/` | food insecurity by country and by gender | FAOSTAT FIES | `food-insecurity.Rmd`, `food-insecurity-by-gender.Rmd` + PDF | Hope | `subsaharan_data/food_insecurity.csv`; the FIES gender-gap sensitivity row |
| `income-and-context/` | income and the first look at the panel's context | World Bank WDI | `world-bank-income.Rmd`, `first-pass.Rmd` | Hope | `subsaharan_data/GDP_per_capita.csv` |
