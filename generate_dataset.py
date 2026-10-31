"""
Potion Pantry - Madam Hexley's Potion Shop
Synthetic Dataset Generator

Generates reproducible synthetic datasets for inventory management, demand forecasting,
and anomaly detection during the Hack-O-Lantern Hackathon.
"""

import argparse
import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Fixed seed for reproducibility
DEFAULT_RANDOM_SEED = 42

# 10 Fictional Potion Ingredients
INGREDIENTS_DATA = [
    {
        "name": "Moonflower",
        "category": "Flora & Herbs",
        "current_stock": 120,
        "safety_stock": 30,
        "supplier": "Silvermoon Botanical Coven",
        "lead_time_days": 4,
        "unit": "blossoms",
        "base_daily_demand": 18,
    },
    {
        "name": "Dragon Root",
        "category": "Roots & Bark",
        "current_stock": 85,
        "safety_stock": 25,
        "supplier": "Wyrmfang Mountain Foragers",
        "lead_time_days": 7,
        "unit": "roots",
        "base_daily_demand": 12,
    },
    {
        "name": "Crystal Dust",
        "category": "Minerals & Gems",
        "current_stock": 250,
        "safety_stock": 50,
        "supplier": "Starlight Alchemical Guild",
        "lead_time_days": 3,
        "unit": "ounces",
        "base_daily_demand": 28,
    },
    {
        "name": "Phoenix Feather",
        "category": "Mythical Fauna",
        "current_stock": 35,
        "safety_stock": 15,
        "supplier": "Ashen Crest Aviaries",
        "lead_time_days": 10,
        "unit": "feathers",
        "base_daily_demand": 6,
    },
    {
        "name": "Witch Hazel",
        "category": "Flora & Herbs",
        "current_stock": 180,
        "safety_stock": 40,
        "supplier": "Shadowbrook Herbalists",
        "lead_time_days": 2,
        "unit": "bundles",
        "base_daily_demand": 22,
    },
    {
        "name": "Unicorn Hair",
        "category": "Mythical Fauna",
        "current_stock": 45,
        "safety_stock": 15,
        "supplier": "Glade of the Celestials",
        "lead_time_days": 12,
        "unit": "strands",
        "base_daily_demand": 7,
    },
    {
        "name": "Shadow Berries",
        "category": "Flora & Herbs",
        "current_stock": 140,
        "safety_stock": 35,
        "supplier": "Nightfall Briar Harvesters",
        "lead_time_days": 5,
        "unit": "pints",
        "base_daily_demand": 16,
    },
    {
        "name": "Mystic Water",
        "category": "Essences & Liquids",
        "current_stock": 300,
        "safety_stock": 60,
        "supplier": "Feywild Springs Co.",
        "lead_time_days": 3,
        "unit": "vials",
        "base_daily_demand": 40,
    },
    {
        "name": "Silver Thorn",
        "category": "Roots & Bark",
        "current_stock": 95,
        "safety_stock": 20,
        "supplier": "Ironbark Bramble Keepers",
        "lead_time_days": 6,
        "unit": "spikes",
        "base_daily_demand": 14,
    },
    {
        "name": "Enchanted Mushroom",
        "category": "Fungi & Spores",
        "current_stock": 160,
        "safety_stock": 45,
        "supplier": "Gloomspore Fungi Hollow",
        "lead_time_days": 4,
        "unit": "caps",
        "base_daily_demand": 24,
    },
]

# Intentionally controlled anomalies (separated from training data)
PLANTED_ANOMALIES = [
    {
        "date": "2026-06-13",
        "product_name": "Dragon Root",
        "spike_multiplier": 4.5,
        "anomaly_label": "consumption_spike",
        "description": "Dragon Fire Outbreak in Whispering Woods: sudden emergency demand for fire-warding salves",
    },
    {
        "date": "2026-07-28",
        "product_name": "Phoenix Feather",
        "spike_multiplier": 4.0,
        "anomaly_label": "consumption_spike",
        "description": "High Inquisitor Resurrection Ritual: massive unexpected requisition by Grand Sorcerers",
    },
    {
        "date": "2026-08-20",
        "product_name": "Mystic Water",
        "spike_multiplier": 3.5,
        "anomaly_label": "consumption_spike",
        "description": "Cauldron Cooling Crisis: regional heatwave dried local wells, creating emergency water buying",
    },
    {
        "date": "2026-09-15",
        "product_name": "Moonflower",
        "spike_multiplier": 4.2,
        "anomaly_label": "consumption_spike",
        "description": "Total Lunar Eclipse Gathering: Silver Coven gathered for rare midnight brewing ceremonies",
    },
    {
        "date": "2026-10-13",
        "product_name": "Enchanted Mushroom",
        "spike_multiplier": 4.8,
        "anomaly_label": "consumption_spike",
        "description": "Fairy Ring Convergence: alchemical panic buying after wild mushroom shortage rumor",
    },
]

# Festival Scenario (Midnight Curse: 3 ingredients triple in demand)
FESTIVAL_AFFECTED_INGREDIENTS = ["Moonflower", "Phoenix Feather", "Enchanted Mushroom"]
FESTIVAL_MULTIPLIER = 3.0
FESTIVAL_NAME = "Full Moon Harvest Festival"
FESTIVAL_START_DATE = "2026-11-01"
FESTIVAL_END_DATE = "2026-11-07"


def generate_ingredients_df():
    """Generates the master ingredients dataframe."""
    records = []
    for item in INGREDIENTS_DATA:
        records.append({
            "name": item["name"],
            "category": item["category"],
            "current_stock": int(item["current_stock"]),
            "safety_stock": int(item["safety_stock"]),
            "supplier": item["supplier"],
            "lead_time_days": int(item["lead_time_days"]),
            "unit": item["unit"],
        })
    df = pd.DataFrame(records)
    return df


def generate_historical_sales_and_anomalies(
    seed=DEFAULT_RANDOM_SEED,
    num_days=180,
    end_date_str="2026-10-31",
    store_id="HEXLEY-001"
):
    """
    Generates 180 consecutive days of historical sales for all 10 ingredients (1,800 records).
    Incorporate weekday/weekend patterns, gradual seasonal ramp, and controlled spikes.
    Ground truth anomalies are extracted and returned separately.
    """
    np.random.seed(seed)
    random.seed(seed)

    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    start_date = end_date - timedelta(days=num_days - 1)
    date_range = [start_date + timedelta(days=i) for i in range(num_days)]

    # Map anomalies by (date_str, product_name)
    anomaly_map = {
        (a["date"], a["product_name"]): a for a in PLANTED_ANOMALIES
    }

    sales_records = []
    anomaly_records = []

    # Day-of-week multipliers: Monday=0 to Sunday=6
    # Potion brewing and witch gatherings surge on Friday, Saturday, Sunday
    weekday_multipliers = {
        0: 0.88,  # Monday
        1: 0.92,  # Tuesday
        2: 0.98,  # Wednesday
        3: 1.02,  # Thursday
        4: 1.25,  # Friday (weekend brewing prep)
        5: 1.40,  # Saturday (peak market day)
        6: 1.20,  # Sunday (coven rituals)
    }

    # Demand generation per day and per ingredient
    for day_idx, d in enumerate(date_range):
        date_str = d.strftime("%Y-%m-%d")
        day_of_week = d.weekday()
        dow_mult = weekday_multipliers[day_of_week]

        # Gradual seasonal trend: demand grows as Halloween / Autumn approaches
        # Ramp from ~0.85 in May to ~1.25 in late October + slight lunar oscillation
        seasonal_progress = day_idx / float(num_days - 1)
        seasonal_trend = 0.85 + 0.35 * seasonal_progress
        lunar_cycle = 0.08 * np.sin(2 * np.pi * day_idx / 29.53)  # Synodic lunar month
        seasonal_factor = seasonal_trend + lunar_cycle

        for item in INGREDIENTS_DATA:
            p_name = item["name"]
            base = item["base_daily_demand"]

            # Baseline expected demand with seasonality and day of week
            expected_demand = base * dow_mult * seasonal_factor

            # Stochastic noise (normal variation, ~12% std dev)
            noise = np.random.normal(loc=0.0, scale=0.12 * base)
            normal_demand = expected_demand + noise

            # Check if this date & product has a planted anomaly
            anomaly_key = (date_str, p_name)
            if anomaly_key in anomaly_map:
                anomaly_info = anomaly_map[anomaly_key]
                multiplier = anomaly_info["spike_multiplier"]
                spiked_demand = normal_demand * multiplier
                qty_sold = int(round(spiked_demand))
                expected_baseline_int = max(1, int(round(normal_demand)))

                # Record anomaly ground truth
                anomaly_records.append({
                    "date": date_str,
                    "product_name": p_name,
                    "quantity_sold": qty_sold,
                    "expected_quantity": expected_baseline_int,
                    "spike_multiplier": float(multiplier),
                    "anomaly_label": anomaly_info["anomaly_label"],
                    "is_anomaly": True,
                    "description": anomaly_info["description"],
                })
            else:
                qty_sold = int(round(normal_demand))

            # Guarantee non-negative integer
            qty_sold = max(0, qty_sold)

            sales_records.append({
                "date": date_str,
                "store_id": store_id,
                "product_name": p_name,
                "quantity_sold": qty_sold,
            })

    sales_df = pd.DataFrame(sales_records)
    # Ensure chronological sorting by date, then product_name
    sales_df = sales_df.sort_values(by=["date", "product_name"]).reset_index(drop=True)

    anomaly_df = pd.DataFrame(anomaly_records)
    anomaly_df = anomaly_df.sort_values(by=["date", "product_name"]).reset_index(drop=True)

    return sales_df, anomaly_df


def generate_festival_scenario_df():
    """
    Generates the festival scenario dataset for the Midnight Curse.
    Selects exactly 3 ingredients with a 3.0 demand multiplier,
    keeping the remaining 7 at 1.0.
    """
    records = []
    for item in INGREDIENTS_DATA:
        p_name = item["name"]
        is_curse = p_name in FESTIVAL_AFFECTED_INGREDIENTS
        mult = FESTIVAL_MULTIPLIER if is_curse else 1.0
        base_demand = item["base_daily_demand"]
        projected = int(round(base_demand * mult))

        if is_curse:
            notes = f"Surge item for {FESTIVAL_NAME}; full moon magical catalyst required in 3x quantities"
        else:
            notes = "Standard consumption pattern unaffected by full moon alignment"

        records.append({
            "festival_name": FESTIVAL_NAME,
            "festival_start_date": FESTIVAL_START_DATE,
            "festival_end_date": FESTIVAL_END_DATE,
            "product_name": p_name,
            "demand_multiplier": mult,
            "is_curse_affected": is_curse,
            "baseline_daily_demand": base_demand,
            "projected_daily_demand": projected,
            "scenario_notes": notes,
        })

    df = pd.DataFrame(records)
    df = df.sort_values(by=["is_curse_affected", "product_name"], ascending=[False, True]).reset_index(drop=True)
    return df


def main():
    parser = argparse.ArgumentParser(description="Synthetic dataset generator for Madam Hexley's Potion Shop")
    parser.add_argument("--output-dir", default="data", help="Output directory for generated CSV files")
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED, help="Random seed for reproducibility")
    parser.add_argument("--days", type=int, default=180, help="Number of historical days to generate")
    parser.add_argument("--end-date", default="2026-10-31", help="End date for historical sales (YYYY-MM-DD)")
    parser.add_argument("--store-id", default="HEXLEY-001", help="Store ID identifier")

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 60)
    print("🧙 Madam Hexley's Potion Shop - Dataset Generator")
    print("=" * 60)
    print(f"Output directory : {os.path.abspath(args.output_dir)}")
    print(f"Random seed      : {args.seed}")
    print(f"Historical window: {args.days} days ending on {args.end_date}")
    print(f"Store ID         : {args.store_id}")
    print("-" * 60)

    # 1. Generate ingredients.csv
    ingredients_df = generate_ingredients_df()
    ingredients_path = os.path.join(args.output_dir, "ingredients.csv")
    ingredients_df.to_csv(ingredients_path, index=False)
    print(f"✓ Generated {ingredients_path} ({len(ingredients_df)} ingredients)")

    # 2 & 3. Generate historical_sales.csv and anomaly_ground_truth.csv
    sales_df, anomaly_df = generate_historical_sales_and_anomalies(
        seed=args.seed,
        num_days=args.days,
        end_date_str=args.end_date,
        store_id=args.store_id
    )
    sales_path = os.path.join(args.output_dir, "historical_sales.csv")
    sales_df.to_csv(sales_path, index=False)
    print(f"✓ Generated {sales_path} ({len(sales_df)} daily sales records)")

    anomaly_path = os.path.join(args.output_dir, "anomaly_ground_truth.csv")
    anomaly_df.to_csv(anomaly_path, index=False)
    print(f"✓ Generated {anomaly_path} ({len(anomaly_df)} planted anomaly records)")

    # 4. Generate festival_scenario.csv
    festival_df = generate_festival_scenario_df()
    festival_path = os.path.join(args.output_dir, "festival_scenario.csv")
    festival_df.to_csv(festival_path, index=False)
    print(f"✓ Generated {festival_path} ({len(festival_df)} scenario records)")

    print("=" * 60)
    print("✨ Synthetic dataset generation completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

