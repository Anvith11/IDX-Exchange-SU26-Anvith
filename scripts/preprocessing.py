"""
preprocessing.py

California Property Close Price Prediction — IDX Exchange SU26
Author: Anvith Mulpuri

Data preprocessing pipeline for CRMLS Single Family Residential (SFR) sold data.
Mirrors the logic in notebooks/02_preprocessing.ipynb, refactored into reusable,
importable functions.

Pipeline stages (in order):
    1. Load raw CRMLSSold CSVs, filter to SFR
    2. Drop fully-null / unusable Trestle fields (column-level, no leakage risk)
    3. Drop structural row errors (LivingArea == 0 -- a hard rule, not a learned stat)
    4. Build the chronological train/test split (test = latest month, train = X months prior)
    5. Learn ClosePrice outlier thresholds (0.5th/99.5th percentile) from TRAIN ONLY,
       apply the frozen cutoffs to both train and test
    6. Impute missing values -- constants applied identically to both splits;
       data-derived statistics (medians/modes) are fit on TRAIN ONLY
    7. Save the baseline (no engineered features) train/test CSVs

Feature engineering, encoding, and scaling (Sections 6-9 of the notebook) are intentionally
NOT included in this script. Per project convention, the Week 4 baseline model is trained
on raw/cleaned fields only -- see 02_preprocessing.ipynb for the full engineered pipeline
used in Week 5+.

Usage:
    python preprocessing.py

    or, imported:
    from preprocessing import run_pipeline
    train_df, test_df = run_pipeline(data_dir="../data/raw")
"""

from pathlib import Path
import numpy as np
import pandas as pd


# ── Configuration ─────────────────────────────────────────────────────

FILE_MONTHS = [
    "CRMLSSold202511.csv",  # November 2025
    "CRMLSSold202512.csv",  # December 2025
    "CRMLSSold202601.csv",  # January 2026
    "CRMLSSold202602.csv",  # February 2026
    "CRMLSSold202603.csv",  # March 2026
    "CRMLSSold202604.csv",  # April 2026
    "CRMLSSold202605.csv",  # May 2026  <- held-out test month
]

# Trestle fields confirmed 100% null in this CRMLS extract (Week 2 field audit)
FULLY_NULL_FIELDS = [
    "AboveGradeFinishedArea",
    "BelowGradeFinishedArea",
    "BuildingAreaTotal",
    "TaxAnnualAmount",
    "TaxYear",
    "CoveredSpaces",
    "FireplacesTotal",           # use FireplaceYN instead
    "BusinessType",              # not applicable to SFR
    "ElementarySchoolDistrict",
    "MiddleOrJuniorSchoolDistrict",
]

# Additional fields dropped for sparsity / redundancy (not 100% null, but unusable)
SPARSE_OR_REDUNDANT_FIELDS = [
    "WaterfrontYN",              # 99.9% null
    "BasementYN",                # 97.6% null
    "ElementarySchool",          # 87.3% null
    "MiddleOrJuniorSchool",      # 87.2% null
    "HighSchool",                # 83.2% null -- HighSchoolDistrict preferred
    "LotSizeAcres",              # redundant with LotSizeSquareFeet
    "LotSizeArea",               # redundant with LotSizeSquareFeet
    "LotSizeDimensions",         # freeform String 150 -- not modelable
    "MainLevelBedrooms",         # 39.0% null; overlaps BedroomsTotal
]

# Fields excluded from modelling at every stage of this project -- target leakage.
# ListPrice/OriginalListPrice don't exist for off-market properties and are highly
# correlated with ClosePrice. DaysOnMarket and PriceReductionYN only exist because
# a sale process happened and reflect post-sale pricing decisions.
LEAKAGE_EXCLUDED_FIELDS = [
    "ListPrice",
    "OriginalListPrice",
    "DaysOnMarket",
    "PriceReductionYN",
]

BOOLEAN_IMPUTE_FALSE = [
    "PoolPrivateYN",
    "ViewYN",
    "FireplaceYN",
    "AttachedGarageYN",
    "NewConstructionYN",
]

TRAIN_WINDOW_MONTHS_DEFAULT = 6  # X in "X months immediately preceding the test month"
OUTLIER_LOW_PCTILE = 0.005
OUTLIER_HIGH_PCTILE = 0.995


# ── Stage 1: Load & Filter ────────────────────────────────────────────

def load_and_filter_sfr(data_dir: Path, file_months: list[str] = FILE_MONTHS) -> pd.DataFrame:
    """Load all monthly CRMLSSold CSVs and filter to Single Family Residential."""
    frames = []
    for fname in file_months:
        df_month = pd.read_csv(data_dir / fname, low_memory=False)
        df_month["_source_file"] = fname
        frames.append(df_month)

    raw = pd.concat(frames, ignore_index=True)
    print(f"Total rows loaded (all PropertyTypes): {len(raw):,}")

    df = raw[
        (raw["PropertyType"] == "Residential")
        & (raw["PropertySubType"] == "SingleFamilyResidence")
    ].copy()
    print(f"Rows after SFR filter: {len(df):,}")

    for col in ["CloseDate", "ListingContractDate", "PurchaseContractDate"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["CloseYearMonth"] = df["CloseDate"].dt.to_period("M")
    df["CloseMonth"] = df["CloseDate"].dt.month

    return df


# ── Stage 2: Drop Fully-Null / Unusable Fields ────────────────────────

def drop_unusable_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Drop Trestle fields that are 100% null in this extract, or sparse/redundant.
    Column-level operation -- safe to run before the train/test split, since it
    doesn't depend on any statistic that could leak between splits."""
    drop_fields = FULLY_NULL_FIELDS + SPARSE_OR_REDUNDANT_FIELDS
    drop_fields = [c for c in drop_fields if c in df.columns]

    df = df.drop(columns=drop_fields)
    print(f"Dropped {len(drop_fields)} fields. Remaining columns: {df.shape[1]}")
    return df


# ── Stage 3: Drop Structural Row Errors (Hard Rules Only) ─────────────

def drop_structural_errors(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with physically impossible values. Only universal, non-statistical
    rules are applied here -- LivingArea == 0 is a structural impossibility, not a
    learned outlier threshold, so it's safe to apply before the split."""
    before = len(df)
    df = df[df["LivingArea"] > 0]
    after = len(df)
    print(f"Structural row drop (LivingArea==0): {before:,} -> {after:,} "
          f"({before - after} dropped)")
    return df


# ── Stage 4: Chronological Train / Test Split ─────────────────────────

def build_train_test_split(
    df: pd.DataFrame,
    test_month,
    window_x: int,
    date_col: str = "CloseYearMonth",
):
    """
    Build a train/test split where:
      - test set  = the single most recent month (test_month)
      - train set = the X months immediately preceding test_month

    window_x is a parameter, not fixed, so different training window lengths
    can be experimented with (e.g. X=2,3,4,5,6) to find the best value.
    """
    available = sorted(df[date_col].unique())
    test_idx = available.index(test_month)

    if test_idx - window_x < 0:
        raise ValueError(
            f"Requested window_x={window_x} months, but only {test_idx} months "
            f"are available before {test_month}."
        )

    train_months = available[test_idx - window_x: test_idx]

    train_df = df[df[date_col].isin(train_months)].copy()
    test_df = df[df[date_col] == test_month].copy()

    return train_df, test_df, train_months


# ── Stage 5: Outlier Thresholds — Learned From Train Only ─────────────

def apply_outlier_thresholds(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    low_pctile: float = OUTLIER_LOW_PCTILE,
    high_pctile: float = OUTLIER_HIGH_PCTILE,
):
    """Compute ClosePrice percentile thresholds from train_df ONLY, then apply the
    identical, frozen cutoffs to both train_df and test_df. Never recompute
    percentiles on the test set -- that leaks test-set distribution information
    into the filtering decision."""
    price_low = train_df["ClosePrice"].quantile(low_pctile)
    price_high = train_df["ClosePrice"].quantile(high_pctile)

    print(f"ClosePrice outlier thresholds (learned from TRAIN only): "
          f"[${price_low:,.0f}, ${price_high:,.0f}]")

    before_train, before_test = len(train_df), len(test_df)

    train_df = train_df[
        (train_df["ClosePrice"] >= price_low) & (train_df["ClosePrice"] <= price_high)
    ].copy()
    test_df = test_df[
        (test_df["ClosePrice"] >= price_low) & (test_df["ClosePrice"] <= price_high)
    ].copy()

    print(f"Train: {before_train:,} -> {len(train_df):,} "
          f"({before_train - len(train_df)} dropped)")
    print(f"Test:  {before_test:,} -> {len(test_df):,} "
          f"({before_test - len(test_df)} dropped)")

    return train_df, test_df


# ── Stage 6: Missing Value Imputation — Fit on Train, Applied to Both ──

def impute_missing_values(train_df: pd.DataFrame, test_df: pd.DataFrame):
    """Impute missing values. Constant-value imputation (booleans, counts,
    placeholders) is applied identically to both splits -- it carries no leakage
    risk since the fill value doesn't depend on the data's distribution.
    Data-derived imputations (medians, modes) are fit on train_df only and the
    learned value is applied to both splits."""

    # Boolean amenities -- constant, no leakage risk
    for col in BOOLEAN_IMPUTE_FALSE:
        if col in train_df.columns:
            train_df[col] = train_df[col].fillna(False)
            test_df[col] = test_df[col].fillna(False)

    # Counts -- constant
    for col in ["GarageSpaces", "ParkingTotal"]:
        if col in train_df.columns:
            train_df[col] = train_df[col].fillna(0)
            test_df[col] = test_df[col].fillna(0)

    # HOA fields -- constant (NaN assumed to mean no HOA)
    train_df["AssociationFee"] = train_df["AssociationFee"].fillna(0)
    test_df["AssociationFee"] = test_df["AssociationFee"].fillna(0)
    train_df["AssociationFeeFrequency"] = train_df["AssociationFeeFrequency"].fillna("None")
    test_df["AssociationFeeFrequency"] = test_df["AssociationFeeFrequency"].fillna("None")

    # LotSizeSquareFeet -- ZIP median -> county median -> global median, LEARNED FROM TRAIN
    zip_median_lookup = train_df.groupby("PostalCode")["LotSizeSquareFeet"].median()
    county_median_lookup = train_df.groupby("CountyOrParish")["LotSizeSquareFeet"].median()
    global_median = train_df["LotSizeSquareFeet"].median()

    for df_ in (train_df, test_df):
        zip_med = df_["PostalCode"].map(zip_median_lookup)
        county_med = df_["CountyOrParish"].map(county_median_lookup)
        df_["LotSizeSquareFeet"] = (
            df_["LotSizeSquareFeet"].fillna(zip_med).fillna(county_med).fillna(global_median)
        )

    # Stories -- mode, LEARNED FROM TRAIN
    stories_mode = train_df["Stories"].mode()[0]
    train_df["Stories"] = train_df["Stories"].fillna(stories_mode)
    test_df["Stories"] = test_df["Stories"].fillna(stories_mode)

    # YearBuilt -- median, LEARNED FROM TRAIN
    year_median = train_df["YearBuilt"].median()
    train_df["YearBuilt"] = train_df["YearBuilt"].fillna(year_median)
    test_df["YearBuilt"] = test_df["YearBuilt"].fillna(year_median)

    # Flooring -- constant placeholder
    train_df["Flooring"] = train_df["Flooring"].fillna("Unknown")
    test_df["Flooring"] = test_df["Flooring"].fillna("Unknown")

    # Levels -- mode, LEARNED FROM TRAIN
    levels_mode = train_df["Levels"].mode()[0]
    train_df["Levels"] = train_df["Levels"].fillna(levels_mode)
    test_df["Levels"] = test_df["Levels"].fillna(levels_mode)

    # HighSchoolDistrict -- INTENTIONALLY LEFT NULL, not imputed (26.9% null).
    # Reserved for the Week 6 spatial join against CA School District Areas
    # 2024-25 boundaries, using Latitude/Longitude.

    # MLSAreaMajor / City -- constant placeholder
    for col in ["MLSAreaMajor", "City"]:
        if col in train_df.columns:
            train_df[col] = train_df[col].fillna("Unknown")
            test_df[col] = test_df[col].fillna("Unknown")

    print("Missing value imputation complete (constants applied to both splits; "
          "medians/modes learned from train only).")

    return train_df, test_df


# ── Stage 7: Full Pipeline Runner ─────────────────────────────────────

def run_pipeline(
    data_dir: str = "../data/raw",
    output_dir: str = "../data/cleaned",
    train_window_months: int = TRAIN_WINDOW_MONTHS_DEFAULT,
    file_months: list[str] = FILE_MONTHS,
):
    """
    Run the full leakage-safe preprocessing pipeline end-to-end and save the
    baseline (no engineered features) train/test CSVs.

    Returns (train_df, test_df).
    """
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("STAGE 1 — Load & Filter to SFR")
    print("=" * 60)
    df = load_and_filter_sfr(data_dir, file_months)

    print("\n" + "=" * 60)
    print("STAGE 2 — Drop Fully-Null / Unusable Fields")
    print("=" * 60)
    df = drop_unusable_fields(df)

    print("\n" + "=" * 60)
    print("STAGE 3 — Drop Structural Row Errors")
    print("=" * 60)
    df = drop_structural_errors(df)

    print("\n" + "=" * 60)
    print("STAGE 4 — Chronological Train / Test Split")
    print("=" * 60)
    available_months = sorted(df["CloseYearMonth"].unique())
    test_month = available_months[-1]
    print(f"Test month (most recent): {test_month}")

    train_df, test_df, train_months = build_train_test_split(
        df, test_month, train_window_months
    )
    print(f"Training window (X={train_window_months} months): {train_months}")
    print(f"Train: {len(train_df):,} rows | Test: {len(test_df):,} rows")

    print("\n" + "=" * 60)
    print("STAGE 5 — Outlier Thresholds (Learned From Train Only)")
    print("=" * 60)
    train_df, test_df = apply_outlier_thresholds(train_df, test_df)

    print("\n" + "=" * 60)
    print("STAGE 6 — Missing Value Imputation")
    print("=" * 60)
    train_df, test_df = impute_missing_values(train_df, test_df)

    print("\n" + "=" * 60)
    print("STAGE 7 — Save Baseline CSVs")
    print("=" * 60)
    train_path = output_dir / "sfr_baseline_train.csv"
    test_path = output_dir / "sfr_baseline_test.csv"
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    print(f"Saved: {train_path}  ({train_df.shape[0]:,} rows, {train_df.shape[1]} columns)")
    print(f"Saved: {test_path}  ({test_df.shape[0]:,} rows, {test_df.shape[1]} columns)")
    print("\nNOTE: These files contain cleaned/imputed RAW fields only -- zero "
          "engineered features. This is the intended input for the Week 4 baseline "
          "model. Feature engineering, encoding, and scaling are handled separately "
          "in 02_preprocessing.ipynb for Week 5+ modelling.")
    print(f"\nExcluded from modelling at every stage (target leakage): {LEAKAGE_EXCLUDED_FIELDS}")

    return train_df, test_df


if __name__ == "__main__":
    run_pipeline()