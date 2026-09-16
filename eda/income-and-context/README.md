# income-and-context/

Hope's work on the World Bank side in R. [`world-bank-income.Rmd`](world-bank-income.Rmd) pulls GDP per capita through the WDI API, checks which of the 49 countries the World Bank carries, and writes [`subsaharan_data/GDP_per_capita.csv`](../../subsaharan_data/GDP_per_capita.csv); [`first-pass.Rmd`](first-pass.Rmd) is the initial look across FAOSTAT food-security indicators for 2024 that preceded it. Both read the country list from [`subsaharan_data/`](../../subsaharan_data/) by relative path.
