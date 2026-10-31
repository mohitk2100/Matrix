# 🧙 Potion Pantry – Madam Hexley's Potion Shop
### Synthetic Dataset Generator & Data Quality Pipeline
*Created for Hack-O-Lantern Hackathon (Track 1: Smart Inventory & Demand Prediction)*

---

> [!IMPORTANT]
> **Synthetic Demonstration Data Notice**
> These datasets are synthetic demonstration records engineered for system development, CRUD testing, baseline demand forecasting, and anomaly detection testing. They are **not** real-world sales records or organizer-provided hidden test sets. They do not claim to guarantee forecasting accuracy on unseen evaluation data.

---

## 📁 Repository & Directory Layout

```text
Hackathon/
├── data/                                # Primary generated dataset directory
│   ├── ingredients.csv                  # 10 fictional potion ingredients master catalog
│   ├── historical_sales.csv             # Exactly 1,800 daily sales records (180 consecutive days)
│   ├── anomaly_ground_truth.csv         # Planted anomaly ground truth labels (isolated)
│   └── festival_scenario.csv            # Midnight Curse surge scenario (3x multiplier on 3 items)
├── generate_dataset.py                  # Python generator script (reproducible seed=42)
├── validate_dataset.py                  # Rigorous data quality and schema validator
├── requirements.txt                     # Dependencies (pandas, numpy)
└── README.md                            # Comprehensive documentation & Supabase setup guide
```

*(Mirrored inside `potion-pantry/` for full portability across root and project subdirectories)*

---

## 🧪 Dataset Schemas & Data Dictionary

All column names are standardized in **lowercase snake_case** for direct 1:1 compatibility with Supabase PostgreSQL tables.

### 1. `ingredients.csv`
Master catalog of 10 fictional potion ingredients stocked by Madam Hexley.

| Column | Supabase / SQL Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `name` | `TEXT PRIMARY KEY` | Fictional ingredient name | `Moonflower` |
| `category` | `TEXT NOT NULL` | Ingredient classification | `Flora & Herbs` |
| `current_stock` | `INTEGER NOT NULL` | Units currently on shop shelves | `120` |
| `safety_stock` | `INTEGER NOT NULL` | Minimum threshold before reorder trigger | `30` |
| `supplier` | `TEXT NOT NULL` | Coven, guild, or forager source | `Silvermoon Botanical Coven` |
| `lead_time_days`| `INTEGER NOT NULL` | Delivery delay in days from supplier | `4` |
| `unit` | `TEXT NOT NULL` | Unit of measure | `blossoms` |

#### The 10 Fictional Ingredients:
1. **Moonflower** (*Flora & Herbs*) – 120 stock, 30 safety, 4d lead time (`blossoms`)
2. **Dragon Root** (*Roots & Bark*) – 85 stock, 25 safety, 7d lead time (`roots`)
3. **Crystal Dust** (*Minerals & Gems*) – 250 stock, 50 safety, 3d lead time (`ounces`)
4. **Phoenix Feather** (*Mythical Fauna*) – 35 stock, 15 safety, 10d lead time (`feathers`)
5. **Witch Hazel** (*Flora & Herbs*) – 180 stock, 40 safety, 2d lead time (`bundles`)
6. **Unicorn Hair** (*Mythical Fauna*) – 45 stock, 15 safety, 12d lead time (`strands`)
7. **Shadow Berries** (*Flora & Herbs*) – 140 stock, 35 safety, 5d lead time (`pints`)
8. **Mystic Water** (*Essences & Liquids*) – 300 stock, 60 safety, 3d lead time (`vials`)
9. **Silver Thorn** (*Roots & Bark*) – 95 stock, 20 safety, 6d lead time (`spikes`)
10. **Enchanted Mushroom** (*Fungi & Spores*) – 160 stock, 45 safety, 4d lead time (`caps`)

---

### 2. `historical_sales.csv`
Contains **exactly 1,800 daily sales records** across 180 consecutive calendar days (May 5, 2026 to October 31, 2026) for all 10 ingredients.

| Column | Supabase / SQL Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `date` | `DATE NOT NULL` | Date of sale (YYYY-MM-DD, chronological) | `2026-05-05` |
| `store_id` | `TEXT NOT NULL` | Shop identifier | `HEXLEY-001` |
| `product_name` | `TEXT REFERENCES ingredients(name)` | Foreign key referencing ingredient | `Crystal Dust` |
| `quantity_sold` | `INTEGER NOT NULL` | Non-negative integer count of units sold | `24` |

#### Demand Modeling Features:
- **Reproducibility**: Governed by fixed random seed `42`.
- **Weekday vs. Weekend Patterns**: Weekend demand peaks (Friday +25%, Saturday +40%, Sunday +20%) reflecting witch coven gatherings and market days; Monday/Tuesday dips (-12% / -8%).
- **Gradual Seasonal Trend**: Autumn ramp from May to October 31st (+35% increase) combined with a 29.5-day synodic lunar wave.
- **Controlled Spikes**: Specific high-demand days (detailed in anomaly ground truth).
- **Strict Isolation**: Does **NOT** include any anomaly labels or leak future scenario features.

---

### 3. `anomaly_ground_truth.csv`
Isolated validation set recording the exact dates, products, and characteristics of intentionally generated consumption spikes.

| Column | Supabase / SQL Type | Description |
| :--- | :--- | :--- |
| `date` | `DATE NOT NULL` | Event occurrence date |
| `product_name` | `TEXT NOT NULL` | Affected ingredient |
| `quantity_sold` | `INTEGER NOT NULL` | Spiked quantity recorded in `historical_sales.csv` |
| `expected_quantity`| `INTEGER NOT NULL` | Normal baseline expected quantity without anomaly |
| `spike_multiplier`| `NUMERIC NOT NULL` | Multiplier applied (3.5x to 4.8x) |
| `anomaly_label` | `TEXT NOT NULL` | Label (`consumption_spike`) |
| `is_anomaly` | `BOOLEAN NOT NULL` | `TRUE` |
| `description` | `TEXT NOT NULL` | Lore-based root cause explanation |

#### Planted Anomaly Catalog:
1. `2026-06-13` – **Dragon Root** (Qty: 79 vs Expected: 17, 4.5x) – *Dragon Fire Outbreak in Whispering Woods: sudden emergency demand for fire-warding salves.*
2. `2026-07-28` – **Phoenix Feather** (Qty: 22 vs Expected: 6, 4.0x) – *High Inquisitor Resurrection Ritual: massive unexpected requisition by Grand Sorcerers.*
3. `2026-08-20` – **Mystic Water** (Qty: 136 vs Expected: 39, 3.5x) – *Cauldron Cooling Crisis: regional heatwave dried local wells, creating emergency water buying.*
4. `2026-09-15` – **Moonflower** (Qty: 91 vs Expected: 22, 4.2x) – *Total Lunar Eclipse Gathering: Silver Coven gathered for rare midnight brewing ceremonies.*
5. `2026-10-13` – **Enchanted Mushroom** (Qty: 142 vs Expected: 30, 4.8x) – *Fairy Ring Convergence: alchemical panic buying after wild mushroom shortage rumor.*

---

### 4. `festival_scenario.csv`
Represents the **Midnight Curse** challenge twist (Hack-O-Lantern Round 2 / Slide 16):
> *"A full moon festival is announced for next week. Demand for 3 ingredients triples."*

| Column | Supabase / SQL Type | Description |
| :--- | :--- | :--- |
| `festival_name` | `TEXT NOT NULL` | `Full Moon Harvest Festival` |
| `festival_start_date`| `DATE NOT NULL` | `2026-11-01` (immediate post-historical start) |
| `festival_end_date` | `DATE NOT NULL` | `2026-11-07` |
| `product_name` | `TEXT NOT NULL` | Ingredient name |
| `demand_multiplier` | `NUMERIC NOT NULL` | `3.0` for 3 surge items, `1.0` for 7 baseline items |
| `is_curse_affected` | `BOOLEAN NOT NULL` | `TRUE` for surging items, `FALSE` for unchanged items |
| `baseline_daily_demand`| `INTEGER NOT NULL` | Normal daily base demand |
| `projected_daily_demand`| `INTEGER NOT NULL`| Surged daily demand during the festival |
| `scenario_notes` | `TEXT NOT NULL` | Explanatory context |

#### Surging Ingredients (3x Multiplier):
- **Moonflower**: Base 18 $\rightarrow$ Projected 54 / day (Full moon night rituals and lunar draughts)
- **Phoenix Feather**: Base 6 $\rightarrow$ Projected 18 / day (Festival fire wards and perpetual hearth lanterns)
- **Enchanted Mushroom**: Base 24 $\rightarrow$ Projected 72 / day (Festive levitation brews and fairy elixirs)

#### Unchanged Ingredients (1x Multiplier):
- Crystal Dust (28), Dragon Root (12), Mystic Water (40), Shadow Berries (16), Silver Thorn (14), Unicorn Hair (7), Witch Hazel (22).

---

## 🚀 How to Run the Generator & Validator

### 1. Prerequisites
Ensure Python 3.9+ is installed and install the required packages:

```bash
pip install -r requirements.txt
```

### 2. Generate the Datasets
To re-generate the CSV files in `data/`:

```bash
python generate_dataset.py
```

Optional CLI flags:
```bash
python generate_dataset.py --output-dir data --seed 42 --days 180 --end-date 2026-10-31 --store-id HEXLEY-001
```

### 3. Validate Data Quality & Schema Integrity
Run the validation script to test all 31 automated quality assertions:

```bash
python validate_dataset.py
```

For custom directory targets:
```bash
python validate_dataset.py --data-dir potion-pantry/data
```

---

## 🗄️ Supabase PostgreSQL Schema (DDL)

You can copy and execute this SQL directly in your Supabase SQL Editor:

```sql
-- 1. Master Ingredients Table
CREATE TABLE IF NOT EXISTS public.ingredients (
    name TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    current_stock INTEGER NOT NULL CHECK (current_stock >= 0),
    safety_stock INTEGER NOT NULL CHECK (safety_stock >= 0),
    supplier TEXT NOT NULL,
    lead_time_days INTEGER NOT NULL CHECK (lead_time_days > 0),
    unit TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Historical Sales Table
CREATE TABLE IF NOT EXISTS public.historical_sales (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    store_id TEXT NOT NULL,
    product_name TEXT NOT NULL REFERENCES public.ingredients(name) ON UPDATE CASCADE,
    quantity_sold INTEGER NOT NULL CHECK (quantity_sold >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_store_product_date UNIQUE (date, store_id, product_name)
);

CREATE INDEX IF NOT EXISTS idx_sales_date_product ON public.historical_sales(date, product_name);

-- 3. Anomaly Ground Truth Table (Kept separate from training)
CREATE TABLE IF NOT EXISTS public.anomaly_ground_truth (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    product_name TEXT NOT NULL REFERENCES public.ingredients(name) ON UPDATE CASCADE,
    quantity_sold INTEGER NOT NULL,
    expected_quantity INTEGER NOT NULL,
    spike_multiplier NUMERIC(4, 2) NOT NULL,
    anomaly_label TEXT NOT NULL,
    is_anomaly BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT NOT NULL
);

-- 4. Festival Scenario Table (Challenge Twist)
CREATE TABLE IF NOT EXISTS public.festival_scenario (
    id SERIAL PRIMARY KEY,
    festival_name TEXT NOT NULL,
    festival_start_date DATE NOT NULL,
    festival_end_date DATE NOT NULL,
    product_name TEXT NOT NULL REFERENCES public.ingredients(name) ON UPDATE CASCADE,
    demand_multiplier NUMERIC(4, 2) NOT NULL,
    is_curse_affected BOOLEAN NOT NULL,
    baseline_daily_demand INTEGER NOT NULL,
    projected_daily_demand INTEGER NOT NULL,
    scenario_notes TEXT NOT NULL
);
```
