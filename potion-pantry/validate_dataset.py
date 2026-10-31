"""
Potion Pantry - Madam Hexley's Potion Shop
Dataset Validation Script

Rigorously verifies synthetic dataset quality:
- Row counts
- Missing values (Nulls/NaNs)
- Duplicate combinations
- Chronological ordering & contiguous date ranges
- Non-negative integer constraints
- Anomaly ground truth consistency & isolation
- Festival scenario specifications (3 surge ingredients @ 3x multiplier, 7 unchanged)
- Supabase schema compatibility (snake_case, standard column naming)
"""

import argparse
import os
import re
import sys
import pandas as pd

EXPECTED_INGREDIENTS = [
    "Moonflower", "Dragon Root", "Crystal Dust", "Phoenix Feather", "Witch Hazel",
    "Unicorn Hair", "Shadow Berries", "Mystic Water", "Silver Thorn", "Enchanted Mushroom"
]

SNAKE_CASE_REGEX = re.compile(r"^[a-z][a-z0-9_]*$")


class ValidationReporter:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.errors = []
        self.warnings = []

    def log_pass(self, test_name, message):
        self.checks_passed += 1
        print(f"  [PASS] {test_name}: {message}")

    def log_fail(self, test_name, message):
        self.checks_failed += 1
        self.errors.append(f"{test_name}: {message}")
        print(f"  [FAIL] {test_name}: {message}")

    def summary(self):
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Checks Passed: {self.checks_passed}")
        print(f"Total Checks Failed: {self.checks_failed}")
        if self.checks_failed > 0:
            print("\nFailures:")
            for err in self.errors:
                print(f"  ❌ {err}")
            return False
        else:
            print("\n✨ ALL DATA QUALITY & SCHEMA CHECKS PASSED PERFECTLY! ✨")
            return True


def check_column_names(df, table_name, reporter):
    """Verifies all columns follow Supabase-compatible lowercase snake_case."""
    invalid_cols = [col for col in df.columns if not SNAKE_CASE_REGEX.match(col)]
    if not invalid_cols:
        reporter.log_pass(f"{table_name} Columns", f"All column names are valid Supabase snake_case ({list(df.columns)})")
    else:
        reporter.log_fail(f"{table_name} Columns", f"Invalid column names for Supabase: {invalid_cols}")


def check_missing_values(df, table_name, reporter):
    """Verifies zero null or missing values across the dataframe."""
    null_counts = df.isnull().sum()
    total_nulls = null_counts.sum()
    if total_nulls == 0:
        reporter.log_pass(f"{table_name} Missing Values", "0 missing or null values found across all columns")
    else:
        details = null_counts[null_counts > 0].to_dict()
        reporter.log_fail(f"{table_name} Missing Values", f"Found nulls: {details}")


def validate_ingredients(data_dir, reporter):
    print("\n--- Validating ingredients.csv ---")
    path = os.path.join(data_dir, "ingredients.csv")
    if not os.path.exists(path):
        reporter.log_fail("ingredients.csv", f"File not found at {path}")
        return None

    df = pd.read_csv(path)

    # 1. Row count
    if len(df) == 10:
        reporter.log_pass("Ingredients Row Count", "Contains exactly 10 ingredient rows")
    else:
        reporter.log_fail("Ingredients Row Count", f"Expected 10 rows, found {len(df)}")

    # 2. Supabase schema column names
    expected_cols = {"name", "category", "current_stock", "safety_stock", "supplier", "lead_time_days", "unit"}
    check_column_names(df, "ingredients.csv", reporter)
    if expected_cols.issubset(set(df.columns)):
        reporter.log_pass("Ingredients Schema", f"Contains required columns: {sorted(list(expected_cols))}")
    else:
        reporter.log_fail("Ingredients Schema", f"Missing required columns: {expected_cols - set(df.columns)}")

    # 3. Missing values
    check_missing_values(df, "ingredients.csv", reporter)

    # 4. Duplicates
    dup_names = df["name"].duplicated().sum()
    if dup_names == 0:
        reporter.log_pass("Ingredients Uniqueness", "All ingredient names are unique")
    else:
        reporter.log_fail("Ingredients Uniqueness", f"Found {dup_names} duplicate names")

    # 5. Check exact 10 fictional ingredient names
    actual_names = sorted(df["name"].tolist())
    expected_sorted = sorted(EXPECTED_INGREDIENTS)
    if actual_names == expected_sorted:
        reporter.log_pass("Ingredients Content", "All 10 required fictional ingredients are present")
    else:
        reporter.log_fail("Ingredients Content", f"Ingredients mismatch. Diff: {set(expected_sorted) ^ set(actual_names)}")

    # 6. Integer constraints
    int_cols = ["current_stock", "safety_stock", "lead_time_days"]
    for col in int_cols:
        if col in df.columns:
            if pd.api.types.is_integer_dtype(df[col]) and (df[col] >= 0).all():
                reporter.log_pass(f"Ingredients {col}", f"All values are non-negative integers (min={df[col].min()}, max={df[col].max()})")
            else:
                reporter.log_fail(f"Ingredients {col}", f"Column {col} contains non-integer or negative values")

    return df


def validate_historical_sales(data_dir, ingredients_df, reporter):
    print("\n--- Validating historical_sales.csv ---")
    path = os.path.join(data_dir, "historical_sales.csv")
    if not os.path.exists(path):
        reporter.log_fail("historical_sales.csv", f"File not found at {path}")
        return None

    df = pd.read_csv(path)

    # 1. Row count: exactly 1,800 rows (180 days * 10 ingredients)
    if len(df) == 1800:
        reporter.log_pass("Historical Sales Row Count", "Contains exactly 1,800 daily ingredient sales records")
    else:
        reporter.log_fail("Historical Sales Row Count", f"Expected 1,800 rows, found {len(df)}")

    # 2. Supabase schema column names
    expected_cols = {"date", "store_id", "product_name", "quantity_sold"}
    check_column_names(df, "historical_sales.csv", reporter)
    if expected_cols.issubset(set(df.columns)):
        reporter.log_pass("Historical Sales Schema", f"Contains required columns: {sorted(list(expected_cols))}")
    else:
        reporter.log_fail("Historical Sales Schema", f"Missing required columns: {expected_cols - set(df.columns)}")

    # 3. Check NO label leakage into training features
    forbidden_cols = {"is_anomaly", "anomaly_label", "spike_multiplier", "multiplier"}
    leaked = forbidden_cols.intersection(set(df.columns))
    if not leaked:
        reporter.log_pass("Label Isolation", "No anomaly labels or multipliers leaked into historical training features")
    else:
        reporter.log_fail("Label Isolation", f"Leaked anomaly labels found in training dataset: {leaked}")

    # 4. Missing values
    check_missing_values(df, "historical_sales.csv", reporter)

    # 5. Duplicates on (date, product_name)
    dup_pairs = df.duplicated(subset=["date", "product_name"]).sum()
    if dup_pairs == 0:
        reporter.log_pass("Historical Sales Uniqueness", "Zero duplicate (date, product_name) combinations")
    else:
        reporter.log_fail("Historical Sales Uniqueness", f"Found {dup_pairs} duplicate (date, product_name) records")

    # 6. Chronological order & contiguous 180 consecutive days
    try:
        df["parsed_date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
        unique_dates = df["parsed_date"].drop_duplicates().sort_values().reset_index(drop=True)
        if len(unique_dates) == 180:
            date_diffs = unique_dates.diff().dropna()
            is_contiguous = (date_diffs == pd.Timedelta(days=1)).all()
            if is_contiguous:
                reporter.log_pass(
                    "Historical Sales Chronology",
                    f"Exactly 180 contiguous consecutive days from {unique_dates.iloc[0].strftime('%Y-%m-%d')} to {unique_dates.iloc[-1].strftime('%Y-%m-%d')}"
                )
            else:
                reporter.log_fail("Historical Sales Chronology", "Date sequence is not strictly consecutive (gaps found)")
        else:
            reporter.log_fail("Historical Sales Chronology", f"Expected 180 unique dates, found {len(unique_dates)}")

        # Check chronological ordering in dataframe
        if df["parsed_date"].is_monotonic_increasing:
            reporter.log_pass("Historical Sales Sorting", "Records are chronologically ordered")
        else:
            reporter.log_fail("Historical Sales Sorting", "Records are not sorted in ascending chronological order")

    except Exception as e:
        reporter.log_fail("Historical Sales Date Parsing", f"Failed parsing dates: {e}")

    # 7. Foreign key validity (product_name belongs to ingredients)
    if ingredients_df is not None:
        valid_products = set(ingredients_df["name"])
        actual_products = set(df["product_name"])
        if actual_products == valid_products:
            reporter.log_pass("Product Integrity", "All sales records reference valid ingredients")
        else:
            reporter.log_fail("Product Integrity", f"Found mismatching products: {actual_products ^ valid_products}")

    # 8. Non-negative integer quantity
    if "quantity_sold" in df.columns:
        is_int = pd.api.types.is_integer_dtype(df["quantity_sold"])
        is_non_neg = (df["quantity_sold"] >= 0).all()
        if is_int and is_non_neg:
            reporter.log_pass(
                "Quantity Sold Validity",
                f"All quantities are non-negative integers (min={df['quantity_sold'].min()}, max={df['quantity_sold'].max()}, mean={df['quantity_sold'].mean():.2f})"
            )
        else:
            reporter.log_fail("Quantity Sold Validity", f"Invalid quantity values: integer={is_int}, non_negative={is_non_neg}")

    return df


def validate_anomaly_ground_truth(data_dir, sales_df, reporter):
    print("\n--- Validating anomaly_ground_truth.csv ---")
    path = os.path.join(data_dir, "anomaly_ground_truth.csv")
    if not os.path.exists(path):
        reporter.log_fail("anomaly_ground_truth.csv", f"File not found at {path}")
        return None

    df = pd.read_csv(path)

    # 1. Row count
    if len(df) > 0:
        reporter.log_pass("Anomaly Ground Truth Rows", f"Contains {len(df)} controlled planted anomalies")
    else:
        reporter.log_fail("Anomaly Ground Truth Rows", "Anomaly file is empty")

    # 2. Supabase schema column names
    expected_cols = {"date", "product_name", "quantity_sold", "expected_quantity", "spike_multiplier", "anomaly_label", "is_anomaly", "description"}
    check_column_names(df, "anomaly_ground_truth.csv", reporter)
    if expected_cols.issubset(set(df.columns)):
        reporter.log_pass("Anomaly Schema", f"Contains required columns: {sorted(list(expected_cols))}")
    else:
        reporter.log_fail("Anomaly Schema", f"Missing required columns: {expected_cols - set(df.columns)}")

    # 3. Missing values
    check_missing_values(df, "anomaly_ground_truth.csv", reporter)

    # 4. Consistency with historical_sales.csv
    if sales_df is not None:
        merged = df.merge(
            sales_df,
            on=["date", "product_name"],
            suffixes=("_ground_truth", "_sales")
        )
        if len(merged) == len(df):
            quantity_matches = (merged["quantity_sold_ground_truth"] == merged["quantity_sold_sales"]).all()
            if quantity_matches:
                reporter.log_pass(
                    "Anomaly Sales Consistency",
                    "All anomaly dates, product names, and quantities match historical_sales.csv perfectly"
                )
            else:
                reporter.log_fail("Anomaly Sales Consistency", "Discrepancy in quantities between anomaly ground truth and sales records")
        else:
            reporter.log_fail("Anomaly Sales Consistency", f"Only {len(merged)} of {len(df)} anomalies matched sales records")

    # 5. Multipliers and labels
    if "spike_multiplier" in df.columns:
        all_multipliers_valid = (df["spike_multiplier"] > 1.0).all()
        if all_multipliers_valid:
            reporter.log_pass("Anomaly Spikes", f"All anomaly spike multipliers > 1.0 (range: {df['spike_multiplier'].min()}x to {df['spike_multiplier'].max()}x)")
        else:
            reporter.log_fail("Anomaly Spikes", "Some spike multipliers are <= 1.0")

    return df


def validate_festival_scenario(data_dir, reporter):
    print("\n--- Validating festival_scenario.csv ---")
    path = os.path.join(data_dir, "festival_scenario.csv")
    if not os.path.exists(path):
        reporter.log_fail("festival_scenario.csv", f"File not found at {path}")
        return None

    df = pd.read_csv(path)

    # 1. Exactly 10 ingredients
    if len(df) == 10:
        reporter.log_pass("Festival Scenario Rows", "Contains exactly 10 ingredient records")
    else:
        reporter.log_fail("Festival Scenario Rows", f"Expected 10 rows, found {len(df)}")

    # 2. Supabase schema column names
    expected_cols = {"festival_name", "festival_start_date", "festival_end_date", "product_name", "demand_multiplier", "is_curse_affected", "baseline_daily_demand", "projected_daily_demand"}
    check_column_names(df, "festival_scenario.csv", reporter)
    if expected_cols.issubset(set(df.columns)):
        reporter.log_pass("Festival Schema", f"Contains required columns: {sorted(list(expected_cols))}")
    else:
        reporter.log_fail("Festival Schema", f"Missing required columns: {expected_cols - set(df.columns)}")

    # 3. Missing values
    check_missing_values(df, "festival_scenario.csv", reporter)

    # 4. Multiplier checks: exactly 3 ingredients with 3.0, exactly 7 with 1.0
    surge_count = (df["demand_multiplier"] == 3.0).sum()
    unchanged_count = (df["demand_multiplier"] == 1.0).sum()
    curse_flag_count = df["is_curse_affected"].sum()

    if surge_count == 3 and unchanged_count == 7 and curse_flag_count == 3:
        surging_names = df[df["demand_multiplier"] == 3.0]["product_name"].tolist()
        reporter.log_pass(
            "Festival Demand Multipliers",
            f"Exactly 3 surge ingredients with 3x multiplier {surging_names}, and 7 unchanged ingredients with 1x multiplier"
        )
    else:
        reporter.log_fail(
            "Festival Demand Multipliers",
            f"Expected 3 surging (found {surge_count}) and 7 unchanged (found {unchanged_count})"
        )

    # 5. Festival dates valid
    if "festival_start_date" in df.columns:
        start_dates = df["festival_start_date"].unique()
        if len(start_dates) == 1 and str(start_dates[0]) == "2026-11-01":
            reporter.log_pass("Festival Date", f"Festival start date is recorded: {start_dates[0]}")
        else:
            reporter.log_fail("Festival Date", f"Unexpected start dates: {start_dates}")

    return df


def main():
    parser = argparse.ArgumentParser(description="Validate synthetic datasets for Madam Hexley's Potion Shop")
    parser.add_argument("--data-dir", default="data", help="Path to data directory containing CSV files")
    args = parser.parse_args()

    print("=" * 60)
    print("🧪 Madam Hexley's Potion Shop - Dataset Validator")
    print("=" * 60)
    print(f"Data directory: {os.path.abspath(args.data_dir)}")

    reporter = ValidationReporter()

    # Run validations
    ingredients_df = validate_ingredients(args.data_dir, reporter)
    sales_df = validate_historical_sales(args.data_dir, ingredients_df, reporter)
    validate_anomaly_ground_truth(args.data_dir, sales_df, reporter)
    validate_festival_scenario(args.data_dir, reporter)

    success = reporter.summary()
    if not success:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
