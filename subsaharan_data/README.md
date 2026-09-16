# subsaharan_data/ — country context pulls

Three tables pulled by Hope Winsor with the `WDI` and `FAOSTAT` R packages (the notebooks that built them are in [`eda/income-and-context/`](../eda/income-and-context/) and [`eda/food-insecurity/`](../eda/food-insecurity/)):

- [`GDP_per_capita.csv`](GDP_per_capita.csv) — World Bank `NY.GDP.PCAP.CD`, 2000–2025; the series is in **current US$** whatever the header says. The panel's main income measure is constant 2015 US$ from [`scaffold/inputs/`](../scaffold/inputs/); this series is the current-US$ sensitivity row.
- [`food_insecurity.csv`](food_insecurity.csv) — FAOSTAT FIES prevalence of severe food insecurity, three-year averages, total and by sex.
- [`subsahran_africa_countries.csv`](subsahran_africa_countries.csv) — the 49-country list with ISO codes (the pipeline pins its own copy in [`scaffold/config.py`](../scaffold/config.py); the original spelling of the file name is kept because the pipeline reads it by name).

How they were pulled and what was left out: [`derived/DATA_ACQUISITION.md`](../derived/DATA_ACQUISITION.md). The pipeline reads this folder by name from the repo root.
