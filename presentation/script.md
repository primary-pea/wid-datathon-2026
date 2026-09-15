
Hook:
Title Slide
[Ramya]: What happens when a health condition affects not only a woman’s well-being, but also her family’s health, her ability to work, and the resilience of her community?

Slide 2
[Ramya]: Rwanda and Mali earn about the same per person. In Rwanda one woman in six is anaemic; in Mali, more than one in two. Why?
(pause)
Across 49 countries, income explains under five percent of that gap. So what explains the rest?
Intro:
[Ramya]: Hello, we are Primary Pea and I am Ramyashree Shetty.
[Alison]: My name is Alison Nichols.
[Hope]: My name is Hope Winsor.
[Sarah]: My name is Saarah Hossain.
[Tiana]: and My name is Tatiana Gabel
[Ramya]: Our project focuses on the Eat track, asking whether nutrition policy affects anemia  amongst women in Sub Saharan Africa.

Problem Statement (and Why this is an area of concern):
Problem Slide 2
[Ramya]: Across 49 Sub-Saharan African countries, the population-weighted prevalence of anemia among women aged 15 to 49 fell from about 43 percent in 2000 to under 36 percent by 2018, then turned upward, reaching nearly 37 percent in 2023.  Progress was uneven, and the differences between countries are one's income alone cannot explain.
This is the problem we set out to investigate: what factors may explain these different outcomes, and do countries’ recorded nutrition policies move with changes in anemia over time?

Our stakeholders are women in Sub-Saharan Africa, and the policy makers and partner organizations working to reach them.

Methodology and Approach (what data we pulled, name and overview of contents, & what subsections we looked at):
Data Slide 1
[Alison]:  To find the answer we combined twelve data sources into a country-year panel covering 49 Sub-Saharan African countries between the years 2000 and 2025.
Our main outcome came from WHO anemia estimates republished through FAOSTAT, focusing on women ages 15 to 49. With additional data from UNICEF for estimates for pregnant and non-pregnant women, as well as underweight and overweight prevalence, UN IGME data for neonatal, infant, and under-five mortality rates, DHS hemoglobin survey data to anchor anemia estimates, and WHO deworming-coverage records as our one measure of delivery.
For policy data, WHO’s GIFNA registry provided nutrition policy, program, and mechanism records while The Global Fortification Data Exchange added food-fortification mandates and their passage years.
For country context, World Bank data supplied GDP per capita and FAOSTAT contributed the cost and affordability of a healthy diet, along with food insecurity estimates.
Data Slide 2
[Alison]:  We standardized the country codes, reshaped the sources into a country-year format, and checked for duplicates and gaps before combining them for analysis.
The final panel dataset was built using a script which joins the sources while refusing duplicate keys, undeclared gaps and an incomplete grid;  24 automated tests check for any inconsistency. All of it is public at our github : one command rebuilds the panel and every result, and a notebook re-fits the headline model.
The dataset presented real obstacles. The registry records what governments write, not what they deliver and three in four programme records carry no date plus two series had to be rebuilt before we could use them.
Method 1
[Sarah]: We used a fixed-effects regression to estimate the association between policy and anemia. Our primary model compared each country with itself over time. Country effects accounted for stable differences such as geography, while year effects accounted for events affecting the entire region. We also controlled for GDP per capita. The primary policy measure was the number of dated anaemia-related policies that had been active three years earlier, allowing time for implementation.
Method 2
[Sarah]: Finally, we tested the result using alternative time lags, a lead test with future policies, country-specific trends, difference models, event studies, out-of-sample prediction and 336 alternative specifications. Each test examined whether the initial relationship remained consistent under different assumptions.
Model Results and Insights:
Finding 1
Our results produced three main insights.
First, income alone does not explain the differences in anemia across the region. We also found that anaemia prevalence was higher in 2023 than in 2015 in 37 of the 49 countries studied. A concern score over 194 countries, built from whether an indicator sits in the worst quarter and is failing to improve, had put three of the five most concerning countries in this region.
Altered =
After an initial study of maternal health concern scores across 194 countries, we idenitifed that 3 of the 5 most at risk countries were located in sub-saharan Africa.
Within this region, we found that anemia prevalence was higher in 2023 than in 2015
However income ALONE does not explain the differences across this region.

Finding 2
Second, though policy stock and anemia rate appear to move together, recorded policy stock did not reliably predict lower anaemia. In our main model, one additional policy was associated with a 0.21 percentage-point decline in anemia three years later. The interval spans zero: benefits larger than about half a point per policy are ruled out, and anything smaller we could not have detected.
Finding 2 (Slide 2)
More importantly, policies recorded three years in the future also predicted current anemia. Because a future policy cannot cause a past outcome, this result suggests that governments may have introduced policies in response to existing trends. When we accounted for a separate trend in each country, the estimated association fell to approximately negative 0.02 percentage points—essentially zero.
Finding 3
Finally, income, health and geography explain 81 percent of the differences between countries, yet the countries doing better than that context predicts did not have a clearly different policy record from those doing worse.
These findings do not show that nutrition policies are ineffective. They show that counting policy documents cannot tell us whether those policies were funded, enforced or delivered to women.
Recommendations/Next Steps:
[Hope]:With these findings in mind our team developed three recommendations:
For Data Custodians, while policy data exists it was frequently incomplete, with three in four programme records missing their dates, and none recording coverage. Dating every record and reporting coverage would make the registry usable for evaluation.
For Policy Makers, since counting adopted policies did not predict lower anemia, governments should back interventions with trial evidence, delivered through programmes that report coverage, and make delivery data a condition of support.
For Funders and Researchers, we recommend conducting more hemoglobin surveys, so that anemia estimates rest on measurement: only 33 of the 49 countries have one in our window, and without them no evaluation can see real improvement.
Conclusion:
[Hope]:Until delivery is recorded adequately, no one can say which policies work. The last mile is measured in blood, not in documents. So record what reaches women, not what is written.
Thank you from Primary Pea.
