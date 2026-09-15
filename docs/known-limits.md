# Known limits

What the numbers can and cannot carry, in the order a reader is likely to trip over them.

- **The registry counts documents, not delivery.** GIFNA records what governments wrote. Three in four programme records carry no date, so the dated dose is built from the policies file alone; nothing in the registry records coverage. A null on this dose says the *count* is uninformative, not that the policies were.
- **Anaemia is estimated, not measured, in most country-years.** The WHO series is a model over surveys. Only 33 of the 49 countries have a haemoglobin survey in the window; the `feat_dhs_anaemia_survey` flag marks the anchored years and the ladder has a survey-anchored row (n = 80, wide interval).
- **The lead test cannot tell anticipation from reverse causation.** Policies three years ahead predicting today's anaemia is consistent with governments reacting to a trend, with data revisions, or with both; it rules out reading the main coefficient as an effect, and that is all it does.
- **Two-way fixed effects under staggered adoption.** The TWFE event study shows a post-adoption decline with a pre-trend of the same sign and a 27% negative-weight share; the two estimators built for staggered adoption find nothing. We report all three.
- **"Income explains six percent" includes year effects.** The income-only reference model is income *plus* year effects (R² 0.06 on 1,135 country-years). Income alone explains about 3% of the pooled variation and about 3.5% of the between-country differences; the hook's "under five percent" is the between-country reading.
- **The context model is fitted on country-years.** Its R² of 0.81 is on levels across countries *and* years; the residual ranking uses 2015–2023 means and covers 43 countries — six lack a control (Eritrea, Equatorial Guinea, Lesotho, Mauritius, South Sudan, Seychelles).
- **Series end at different years.** NCD-RisC underweight and overweight stop in 2022, FIES starts in 2014, diet cost in 2017, low birthweight covers 35 countries. The dashboard uses the latest value within three years where a series ends early and says so.
- **The delivery measure is narrow.** Deworming coverage is among school-age children, 2006–2023, 46 countries; it is a contrast for the paper record, not a confounder in the main model.
- **The registry snapshot is dated.** GIFNA exports of 3–5 September 2026; the topic clusters come from 47 token patterns (`scaffold/inputs/gifna_cluster_rules.csv`), and unmatched tokens are reported rather than guessed.
- **The concern score's weights are a judgement.** Equal weights over four indicators; the dashboard shows how often each country stays in the worst ten under 500 random weightings (rank correlation 0.997 with the equal-weight ranking).
- **Unused data.** MICS and DHS microdata were not used; the panel is national-level throughout.
