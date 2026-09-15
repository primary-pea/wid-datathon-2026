"""
Clean the combined GIFNA tables (policies, programmes & actions, mechanisms) and
extract a country-year feature table for modeling maternal anemia, birth outcomes,
and birthweight. Only GIFNA-derived signals are used -- see the feature ledger
artifact for the rationale behind each block.

Input:  gifna_policies.csv, gifna_programmes_and_actions.csv, gifna_mechanisms.csv
        (the deduplicated, combined files already produced in this project)
Output: gifna_feature_table.csv, one row per (iso3, year), 1999-2025.

Usage:
    py build_feature_table.py
    py build_feature_table.py --input-dir "C:\\path\\to\\csvs" --output "features.csv"
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

YEAR_MIN = 1999
YEAR_MAX = 2025

# ---------------------------------------------------------------------------
# Controlled-vocabulary lookups, taken directly from the values observed in
# the combined GIFNA files (Policy_Type, Topics, Target_Group, Micronutrient,
# Theme, Delivery, Area, mechanism Type/Coordination/Monitoring/Topics).
# ---------------------------------------------------------------------------

ANEMIA_TOPICS = {
    "Anaemia", "Anaemia in adolescent girls", "Anaemia in pregnant women",
    "Anaemia in women 15-49 yrs", "Iron", "Folic acid", "Iron and folic acid",
    "Multiple micronutrients supplementation", "Micronutrient supplementation",
    "Deworming", "Vitamin A deficiency", "Iodine deficiency disorders",
    "Underweight in women", "Nutrition and malaria",
}

MATERNAL_BIRTH_TOPICS = {
    "Maternal, infant and young child nutrition", "Maternity protection",
    "Counselling on healthy diets and nutrition during pregnancy",
    "Balanced energy protein supplement", "Family planning (including birth spacing)",
    "Low birth weight", "Breastfeeding - Early initiation by 1 hour",
    "Growth monitoring and promotion", "Stunting in children 0-5 yrs",
    "Underweight in children 0-5 years",
}

# Matches phrasing like "Mandatory fortification of wheat flours with iron",
# "Voluntary fortification of salt with iron (amended)", "Mandatory salt iodization".
FORTIFICATION_MANDATE_RE = re.compile(
    r"fortif.*\b(iron|folic acid|vitamin a|iodine)\b|iodiz", re.IGNORECASE
)

POLICY_TYPE_SLUGS = {
    "Comprehensive national nutrition policy, strategy or plan": "comprehensive_nutrition_plan",
    "Food security or agriculture sector national policy, strategy or plan with nutrition components": "food_security_plan",
    "Government guidance": "government_guidance",
    "Health sector policy, strategy or plan with nutrition components": "health_sector_plan",
    "Legislation relevant to nutrition": "legislation",
    "Multisectoral development plan with nutrition components": "multisectoral_plan",
    "NCD policy, strategy or plan with healthy diet components": "ncd_plan",
    "Non-national nutrition policy document": "non_national_policy",
    "Nutrition policy, strategy or plan focusing on specific nutrition areas": "specific_area_plan",
    "Other, please specify": "other",
    "Social protection plan with nutrition components": "social_protection_plan",
    "Sub-national nutrition policy document": "subnational_policy",
}

PROGRAMME_TYPE_SLUGS = {
    "Community/sub-national": "community_subnational",
    "Large scale programmes": "large_scale",
    "Multi-national": "multi_national",
    "National": "national",
    "Other": "other",
    "Pilot/research": "pilot_research",
}

MATERNAL_TARGET_SLUGS = {
    "Pregnant women (PW)": "pregnant_women",
    "Lactating women (LW)": "lactating_women",
    "Women of reproductive age (WRA)": "women_reproductive_age",
    "Non-pregnant, non-lactating women (NPNLW)": "non_pregnant_non_lactating_women",
}

INFECTION_TARGET_GROUPS = {"Malaria cases", "HIV cases", "TB cases"}
INFECTION_THEMES = {"Nutrition and infectious disease"}

MICRONUTRIENT_SLUGS = {
    "Iron": "iron", "Folic acid": "folic_acid", "Vitamin A": "vitamin_a",
    "Zinc": "zinc", "Iodine": "iodine", "Calcium": "calcium",
    "Vitamin D": "vitamin_d", "B vitamins": "b_vitamins",
}

THEME_SLUGS = {
    "Micronutrient supplementation": "micronutrient_supplementation",
    "Maternal, infant and young child nutrition": "miycn",
    "Food fortification": "food_fortification",
    "Breastfeeding promotion and counselling": "breastfeeding_promotion",
    "Baby-friendly Hospital Initiative (BFHI)": "bfhi",
    "Management of wasting": "wasting_management",
    "Nutrition and infectious disease": "infectious_disease_nutrition",
}

DELIVERY_SLUGS = {
    "Primary health care center": "primary_health_care", "Hospital/clinic": "hospital_clinic",
    "Community-based": "community_based", "Kindergarten/school": "school",
    "Media": "media", "Commercial": "commercial", "Other": "other",
}

AREA_SLUGS = {"Urban": "urban", "Peri-urban": "peri_urban", "Rural": "rural"}

MECHANISM_TYPE_SLUGS = {"Coordination": "coordination", "Monitoring": "monitoring"}

MECHANISM_TOPIC_SLUGS = {
    "Maternal, infant and young child nutrition": "miycn",
    "Vitamin and mineral nutrition": "vitamin_mineral_nutrition",
    "Nutrition and infectious disease": "infectious_disease_nutrition",
    "Food fortification": "food_fortification",
    "Nutrition sensitive actions": "nutrition_sensitive_actions",
}

COORDINATION_FUNCS = {
    "Convening nutrition partners",
    "Coordination in development of national nutrition policies and programmes",
    "Coordination in implementation of national nutrition policies and programmes",
    "Coordination in monitoring of national nutrition policies and programmes",
}

MONITORING_FUNCS = {
    "Monitoring compliance", "Applying sanctions to identified violations",
    "Public dissemination of monitoring results", "Public dissemination of sanctions applied",
}

# Partner_* column names differ in casing across the three source files.
PARTNER_COLS_POLICY = [
    "Partner_Gov", "Partner_UN", "Partner_NGO", "Partner_Donors", "Partner_InterGov",
    "Partner_National_NGO", "Partner_Research", "Partner_Private", "Partner_Other",
]
PARTNER_COLS_PROGRAMME = PARTNER_COLS_POLICY
PARTNER_COLS_MECHANISM = [
    "Partner_Gov", "Partner_Un", "Partner_Ngo", "Partner_Donors", "Partner_Intergov",
    "Partner_National_Ngo", "Partner_Research", "Partner_Private", "Partner_Other",
]


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def split_list(value):
    if pd.isna(value) or str(value).strip() == "":
        return []
    return [tok.strip() for tok in str(value).split("|") if tok.strip()]


def is_populated(value):
    return pd.notna(value) and str(value).strip() != ""


def partner_breadth(df, partner_cols):
    present = [df[c].apply(is_populated) for c in partner_cols if c in df.columns]
    return pd.concat(present, axis=1).sum(axis=1)


def explode_active_years(df, id_col, start_col, end_col):
    """One row per (record, active year), for years overlapping [YEAR_MIN, YEAR_MAX]."""
    df = df[df[start_col].notna() & df[end_col].notna()].copy()
    df = df[(df[start_col] <= YEAR_MAX) & (df[end_col] >= YEAR_MIN)]
    clipped_start = df[start_col].clip(lower=YEAR_MIN).astype(int)
    clipped_end = df[end_col].clip(upper=YEAR_MAX).astype(int)
    df["year"] = [list(range(s, e + 1)) for s, e in zip(clipped_start, clipped_end)]
    df = df.explode("year")
    df["year"] = df["year"].astype(int)
    df["exposure_years"] = (df["year"] - df[start_col]).clip(lower=0)
    return df


def counts_from_bools(long_df, id_col, bool_cols):
    """For each boolean column, count distinct active records per (iso3, year) where it's True."""
    frames = {}
    for col in bool_cols:
        sub = long_df.loc[long_df[col], ["iso3", "year", id_col]]
        frames[f"{col}_count"] = sub.groupby(["iso3", "year"])[id_col].nunique()
    if not frames:
        return pd.DataFrame(index=pd.MultiIndex.from_arrays([[], []], names=["iso3", "year"]))
    return pd.concat(frames, axis=1)


def means_from_cols(long_df, cols):
    return long_df.groupby(["iso3", "year"])[cols].mean()


def add_membership_flags(df, list_col, cat_slugs, out_prefix):
    bool_cols = []
    for cat, slug in cat_slugs.items():
        col = f"{out_prefix}_{slug}"
        df[col] = df[list_col].apply(lambda lst, c=cat: c in lst)
        bool_cols.append(col)
    return df, bool_cols


def add_any_flag(df, list_col, keyword_set, out_col):
    df[out_col] = df[list_col].apply(lambda lst: any(t in keyword_set for t in lst))
    return df


# ---------------------------------------------------------------------------
# Per-source cleaning
# ---------------------------------------------------------------------------

def clean_policies(path):
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    df = df.rename(columns={"Iso3Code": "iso3"})
    df = df[df["iso3"].apply(is_populated)].copy()

    for col in ["Adopted_Year", "Start_Year", "End_Year", "Published_Year"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Adopted"] = df["Adopted"].astype(str).str.strip().str.lower().eq("true")

    df["effective_start"] = df["Adopted_Year"].fillna(df["Start_Year"]).fillna(df["Published_Year"])
    df["effective_end"] = df["End_Year"].fillna(YEAR_MAX)

    df["Topics_list"] = df["Topics"].apply(split_list)
    df["Policy_Type_list"] = df["Policy_Type"].apply(split_list)

    df, policy_type_bools = add_membership_flags(df, "Policy_Type_list", POLICY_TYPE_SLUGS, "policy_type")
    df = add_any_flag(df, "Topics_list", ANEMIA_TOPICS, "policy_anemia_topic")
    df = add_any_flag(df, "Topics_list", MATERNAL_BIRTH_TOPICS, "policy_maternal_topic")
    df["policy_fortification_mandate"] = df["Topics_list"].apply(
        lambda lst: any(FORTIFICATION_MANDATE_RE.search(t) for t in lst)
    )
    df["policy_is_subnational"] = df["Province"].apply(is_populated)
    df["policy_partner_breadth"] = partner_breadth(df, PARTNER_COLS_POLICY)

    bool_cols = policy_type_bools + [
        "policy_anemia_topic", "policy_maternal_topic", "policy_fortification_mandate",
    ]
    keep = ["Policy_Id", "iso3", "effective_start", "effective_end",
            "policy_is_subnational", "policy_partner_breadth"] + bool_cols
    return df[keep], bool_cols


def clean_programmes(path):
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    df = df.rename(columns={"Iso3Code": "iso3"})
    df = df[df["iso3"].apply(is_populated)].copy()

    for col in ["Start_Year", "End_Year"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Coverage_Percent"] = pd.to_numeric(df["Coverage_Percent"], errors="coerce")

    df["effective_start"] = df["Start_Year"]
    ongoing_end = np.where(df["Status"].astype(str).str.strip().str.lower().eq("on-going"), YEAR_MAX, df["Start_Year"])
    df["effective_end"] = df["End_Year"].fillna(pd.Series(ongoing_end, index=df.index))

    df["Target_Group_list"] = df["Target_Group"].apply(split_list)
    df["Micronutrient_list"] = df["Micronutrient"].apply(split_list)
    df["Theme_list"] = df["Theme"].apply(split_list)
    df["Programme_Type_list"] = df["Programme_Type"].apply(split_list)
    df["Delivery_list"] = df["Delivery"].apply(split_list)
    df["Area_list"] = df["Area"].apply(split_list)

    df, programme_type_bools = add_membership_flags(df, "Programme_Type_list", PROGRAMME_TYPE_SLUGS, "programme_type")
    df, maternal_target_bools = add_membership_flags(df, "Target_Group_list", MATERNAL_TARGET_SLUGS, "target")
    df, micronutrient_bools = add_membership_flags(df, "Micronutrient_list", MICRONUTRIENT_SLUGS, "micronutrient_programme")
    df, theme_bools = add_membership_flags(df, "Theme_list", THEME_SLUGS, "theme")
    df, delivery_bools = add_membership_flags(df, "Delivery_list", DELIVERY_SLUGS, "delivery")
    df, area_bools = add_membership_flags(df, "Area_list", AREA_SLUGS, "area")

    df["programme_maternal_target_any"] = df[maternal_target_bools].any(axis=1)
    df["programme_infection_linked"] = df["Target_Group_list"].apply(
        lambda lst: any(t in INFECTION_TARGET_GROUPS for t in lst)
    ) | df["Theme_list"].apply(lambda lst: any(t in INFECTION_THEMES for t in lst))

    df["programme_me_maturity"] = (
        df["ME_System"].apply(is_populated) | df["Impact_Indicators"].apply(is_populated)
        | df["Baseline"].apply(is_populated) | df["Post_Intervention"].apply(is_populated)
    )
    df["programme_policy_linked"] = df["Related_Policy"].apply(is_populated) | df["New_Policy"].apply(is_populated)
    df["programme_partner_breadth"] = partner_breadth(df, PARTNER_COLS_PROGRAMME)

    bool_cols = (
        programme_type_bools + maternal_target_bools + micronutrient_bools + theme_bools
        + delivery_bools + area_bools
        + ["programme_maternal_target_any", "programme_infection_linked"]
    )
    mean_cols = [
        "programme_me_maturity", "programme_policy_linked",
        "programme_partner_breadth", "Coverage_Percent",
    ]
    keep = ["Programme_Id", "iso3", "effective_start", "effective_end"] + bool_cols + mean_cols
    return df[keep], bool_cols, mean_cols


def clean_mechanisms(path):
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    df = df.rename(columns={"ISO3Code": "iso3"})
    df = df[df["iso3"].apply(is_populated)].copy()

    df["StartYear"] = pd.to_numeric(df["StartYear"], errors="coerce")
    df["effective_start"] = df["StartYear"]
    # No end-date field is collected for mechanisms; assume a coordination body,
    # once established, stays active through the end of the study window.
    df["effective_end"] = YEAR_MAX

    df["Topics_list"] = df["Topics"].apply(split_list)
    df["Type_list"] = df["Type"].apply(split_list)
    df["Coordination_list"] = df["Coordination"].apply(split_list)
    df["Monitoring_list"] = df["Monitoring"].apply(split_list)

    df, mech_type_bools = add_membership_flags(df, "Type_list", MECHANISM_TYPE_SLUGS, "mechanism_type")
    df, mech_topic_bools = add_membership_flags(df, "Topics_list", MECHANISM_TOPIC_SLUGS, "mechanism_topic")

    df["mechanism_coordination_breadth"] = df["Coordination_list"].apply(
        lambda lst: sum(1 for t in lst if t in COORDINATION_FUNCS)
    )
    df["mechanism_monitoring_breadth"] = df["Monitoring_list"].apply(
        lambda lst: sum(1 for t in lst if t in MONITORING_FUNCS)
    )
    df["mechanism_partner_breadth"] = partner_breadth(df, PARTNER_COLS_MECHANISM)

    bool_cols = mech_type_bools + mech_topic_bools
    mean_cols = ["mechanism_coordination_breadth", "mechanism_monitoring_breadth", "mechanism_partner_breadth"]
    keep = ["Id", "iso3", "effective_start", "effective_end"] + bool_cols + mean_cols
    return df[keep], bool_cols, mean_cols


# ---------------------------------------------------------------------------
# Feature assembly
# ---------------------------------------------------------------------------

def build_skeleton(iso3_values):
    years = range(YEAR_MIN, YEAR_MAX + 1)
    idx = pd.MultiIndex.from_product([sorted(iso3_values), years], names=["iso3", "year"])
    return pd.DataFrame(index=idx)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input-dir", default=".", help="Directory containing the three combined GIFNA CSVs")
    parser.add_argument("--output", default="gifna_feature_table.csv", help="Path to write the feature table to")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    policies, policy_bools = clean_policies(input_dir / "gifna_policies.csv")
    programmes, programme_bools, programme_means = clean_programmes(input_dir / "gifna_programmes_and_actions.csv")
    mechanisms, mechanism_bools, mechanism_means = clean_mechanisms(input_dir / "gifna_mechanisms.csv")

    policies_long = explode_active_years(policies, "Policy_Id", "effective_start", "effective_end")
    programmes_long = explode_active_years(programmes, "Programme_Id", "effective_start", "effective_end")
    mechanisms_long = explode_active_years(mechanisms, "Id", "effective_start", "effective_end")

    all_iso3 = set(policies_long["iso3"]) | set(programmes_long["iso3"]) | set(mechanisms_long["iso3"])
    features = build_skeleton(all_iso3)

    # Base activity counts
    features["policy_count_active"] = policies_long.groupby(["iso3", "year"])["Policy_Id"].nunique()
    features["programme_count_active"] = programmes_long.groupby(["iso3", "year"])["Programme_Id"].nunique()
    features["mechanism_count_active"] = mechanisms_long.groupby(["iso3", "year"])["Id"].nunique()

    # Per-category counts (policy types, anemia/maternal topic flags, fortification, etc.)
    features = features.join(counts_from_bools(policies_long, "Policy_Id", policy_bools))
    features = features.join(counts_from_bools(programmes_long, "Programme_Id", programme_bools))
    features = features.join(counts_from_bools(mechanisms_long, "Id", mechanism_bools))

    # Share/mean-style features (kept as NaN, not 0, when no record was active that year)
    features = features.join(means_from_cols(policies_long, ["policy_is_subnational", "policy_partner_breadth"]))
    features = features.join(means_from_cols(programmes_long, programme_means))
    features = features.join(means_from_cols(mechanisms_long, mechanism_means))

    # Cumulative exposure across all three sources combined
    exposure = pd.concat([
        policies_long[["iso3", "year", "exposure_years"]],
        programmes_long[["iso3", "year", "exposure_years"]],
        mechanisms_long[["iso3", "year", "exposure_years"]],
    ])
    features["cumulative_exposure_years"] = exposure.groupby(["iso3", "year"])["exposure_years"].sum()

    # Composite indices
    count_cols = [c for c in features.columns if c.endswith("_count")]
    features[count_cols] = features[count_cols].fillna(0)
    features["cumulative_exposure_years"] = features["cumulative_exposure_years"].fillna(0)

    features["policy_to_practice_ratio"] = (
        features["programme_count_active"] / features["policy_count_active"].replace(0, np.nan)
    )
    features["governance_to_volume_ratio"] = (
        features["mechanism_count_active"]
        / (features["policy_count_active"] + features["programme_count_active"]).replace(0, np.nan)
    )
    features["multisectoral_partnership_index"] = features[
        ["policy_partner_breadth", "programme_partner_breadth", "mechanism_partner_breadth"]
    ].mean(axis=1)

    anemia_inputs = [
        "policy_anemia_topic_count", "policy_fortification_mandate_count",
        "micronutrient_programme_iron_count", "micronutrient_programme_folic_acid_count",
        "programme_infection_linked_count", "mechanism_topic_vitamin_mineral_nutrition_count",
    ]
    features["anemia_programming_intensity"] = features[anemia_inputs].sum(axis=1)

    maternal_inputs = [
        "policy_maternal_topic_count", "programme_maternal_target_any_count",
        "theme_miycn_count", "mechanism_topic_miycn_count",
    ]
    features["maternal_newborn_programming_intensity"] = features[maternal_inputs].sum(axis=1)

    features = features.reset_index()
    country_names = pd.concat([
        pd.read_csv(input_dir / "gifna_policies.csv", encoding="utf-8-sig", usecols=["Iso3Code", "Country_Name"], low_memory=False)
            .rename(columns={"Iso3Code": "iso3", "Country_Name": "country_name"}),
        pd.read_csv(input_dir / "gifna_programmes_and_actions.csv", encoding="utf-8-sig", usecols=["Iso3Code", "Country_Name"], low_memory=False)
            .rename(columns={"Iso3Code": "iso3", "Country_Name": "country_name"}),
        pd.read_csv(input_dir / "gifna_mechanisms.csv", encoding="utf-8-sig", usecols=["ISO3Code", "CountryName"], low_memory=False)
            .rename(columns={"ISO3Code": "iso3", "CountryName": "country_name"}),
    ]).dropna().drop_duplicates(subset="iso3", keep="first")
    features = features.merge(country_names, on="iso3", how="left")

    front = ["iso3", "country_name", "year"]
    features = features[front + [c for c in features.columns if c not in front]]
    features = features.sort_values(["iso3", "year"]).reset_index(drop=True)

    out_path = input_dir / args.output if not Path(args.output).is_absolute() else Path(args.output)
    features.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"Wrote {len(features):,} rows x {features.shape[1]} columns to {out_path}")
    print(f"Countries: {features['iso3'].nunique()}  Years: {features['year'].min()}-{features['year'].max()}")


if __name__ == "__main__":
    main()
