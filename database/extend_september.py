import random
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# NEXORAAI — SEPTEMBER 2026 DATA EXTENSION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
SALES_FILE = BASE_DIR / "data" / "sales.csv"


# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------

START_DATE = "2026-09-01"
END_DATE = "2026-09-30"

ROWS_TO_ADD = 3000

random.seed(42)
np.random.seed(42)


# ------------------------------------------------------------
# LOAD EXISTING DATA
# ------------------------------------------------------------

if not SALES_FILE.exists():
    raise FileNotFoundError(
        f"sales.csv not found at: {SALES_FILE}"
    )

sales = pd.read_csv(SALES_FILE)


# ------------------------------------------------------------
# REQUIRED COLUMNS
# ------------------------------------------------------------

required_columns = [
    "sale_id",
    "date",
    "order_id",
    "customer_id",
    "product",
    "region",
    "channel",
    "units",
    "revenue",
    "cost",
    "expense",
    "profit",
]

missing = [
    column
    for column in required_columns
    if column not in sales.columns
]

if missing:
    raise ValueError(
        f"sales.csv is missing required columns: {missing}"
    )


# ------------------------------------------------------------
# CONVERT DATE
# ------------------------------------------------------------

sales["date"] = pd.to_datetime(sales["date"])


# ------------------------------------------------------------
# PREVENT DUPLICATE SEPTEMBER DATA
# ------------------------------------------------------------

september_start = pd.Timestamp(START_DATE)
september_end = pd.Timestamp(END_DATE)

existing_september = sales[
    (sales["date"] >= september_start)
    & (sales["date"] <= september_end)
]

if not existing_september.empty:
    print(
        "September 2026 data already exists in sales.csv."
    )
    print(
        f"Existing September rows: {len(existing_september)}"
    )
    print(
        "No new rows were added."
    )
    raise SystemExit


# ------------------------------------------------------------
# EXISTING VALUES
# ------------------------------------------------------------

products = sales["product"].dropna().unique().tolist()
regions = sales["region"].dropna().unique().tolist()
channels = sales["channel"].dropna().unique().tolist()
customers = sales["customer_id"].dropna().unique().tolist()


if not products:
    raise ValueError("No products found in sales.csv.")

if not regions:
    raise ValueError("No regions found in sales.csv.")

if not channels:
    raise ValueError("No channels found in sales.csv.")

if not customers:
    raise ValueError("No customers found in sales.csv.")


# ------------------------------------------------------------
# CONTINUE IDs FROM EXISTING DATA
# ------------------------------------------------------------

next_sale_id = int(sales["sale_id"].max()) + 1
next_order_id = int(sales["order_id"].max()) + 1


# ------------------------------------------------------------
# PRODUCT-LEVEL HISTORICAL PRICING / COST PATTERNS
# ------------------------------------------------------------

sales["revenue_per_unit"] = (
    sales["revenue"] / sales["units"].replace(0, np.nan)
)

sales["cost_ratio"] = (
    sales["cost"] / sales["revenue"].replace(0, np.nan)
)

sales["expense_ratio"] = (
    sales["expense"] / sales["revenue"].replace(0, np.nan)
)


product_profiles = {}

for product in products:

    product_data = sales[
        sales["product"] == product
    ]

    revenue_per_unit = (
        product_data["revenue_per_unit"]
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
        .median()
    )

    cost_ratio = (
        product_data["cost_ratio"]
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
        .median()
    )

    expense_ratio = (
        product_data["expense_ratio"]
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
        .median()
    )

    # Safety fallbacks
    if pd.isna(revenue_per_unit):
        revenue_per_unit = sales["revenue_per_unit"].median()

    if pd.isna(cost_ratio):
        cost_ratio = sales["cost_ratio"].median()

    if pd.isna(expense_ratio):
        expense_ratio = sales["expense_ratio"].median()

    product_profiles[product] = {
        "revenue_per_unit": float(revenue_per_unit),
        "cost_ratio": float(cost_ratio),
        "expense_ratio": float(expense_ratio),
    }


# ------------------------------------------------------------
# GENERATE SEPTEMBER 2026
# ------------------------------------------------------------

dates = pd.date_range(
    START_DATE,
    END_DATE,
    freq="D"
)


new_rows = []


for i in range(ROWS_TO_ADD):

    date = random.choice(dates)

    product = random.choice(products)

    region = random.choice(regions)

    channel = random.choice(channels)

    customer_id = random.choice(customers)

    units = random.randint(1, 5)

    profile = product_profiles[product]

    # Small natural variation in selling price
    price_variation = random.uniform(
        0.88,
        1.12
    )

    revenue_per_unit = (
        profile["revenue_per_unit"]
        * price_variation
    )

    revenue = revenue_per_unit * units

    # Natural variation in cost
    cost_ratio = (
        profile["cost_ratio"]
        * random.uniform(0.95, 1.05)
    )

    cost = revenue * cost_ratio

    # Natural variation in operating expense
    expense_ratio = (
        profile["expense_ratio"]
        * random.uniform(0.90, 1.10)
    )

    expense = revenue * expense_ratio

    profit = revenue - cost - expense

    new_rows.append({
        "sale_id": next_sale_id + i,
        "date": date.strftime("%Y-%m-%d"),
        "order_id": next_order_id + i,
        "customer_id": customer_id,
        "product": product,
        "region": region,
        "channel": channel,
        "units": units,
        "revenue": round(revenue, 2),
        "cost": round(cost, 2),
        "expense": round(expense, 2),
        "profit": round(profit, 2),
    })


# ------------------------------------------------------------
# CREATE DATAFRAME
# ------------------------------------------------------------

new_sales = pd.DataFrame(
    new_rows,
    columns=required_columns
)


# ------------------------------------------------------------
# BACKUP
# ------------------------------------------------------------

backup_file = (
    SALES_FILE.parent
    / "sales_before_september_backup.csv"
)

sales[required_columns].to_csv(
    backup_file,
    index=False
)


# ------------------------------------------------------------
# APPEND
# ------------------------------------------------------------

updated_sales = pd.concat(
    [
        sales[required_columns],
        new_sales
    ],
    ignore_index=True
)


updated_sales.to_csv(
    SALES_FILE,
    index=False
)


# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

updated_sales["date"] = pd.to_datetime(
    updated_sales["date"]
)

september_data = updated_sales[
    (updated_sales["date"] >= september_start)
    & (updated_sales["date"] <= september_end)
]


print()
print("=" * 60)
print("NEXORAAI — SEPTEMBER 2026 DATA EXTENSION")
print("=" * 60)

print(
    f"Previous sales rows : {len(sales):,}"
)

print(
    f"Rows added          : {len(new_sales):,}"
)

print(
    f"New total rows      : {len(updated_sales):,}"
)

print(
    f"September rows      : {len(september_data):,}"
)

print(
    f"Dataset start       : "
    f"{updated_sales['date'].min().date()}"
)

print(
    f"Dataset end         : "
    f"{updated_sales['date'].max().date()}"
)

print(
    f"September revenue   : "
    f"₹{september_data['revenue'].sum():,.2f}"
)

print(
    f"September units     : "
    f"{september_data['units'].sum():,}"
)

print(
    f"September orders    : "
    f"{september_data['order_id'].nunique():,}"
)

print(
    f"September customers : "
    f"{september_data['customer_id'].nunique():,}"
)

print(
    f"September profit    : "
    f"₹{september_data['profit'].sum():,.2f}"
)

print()
print(
    f"Backup created at:"
)
print(
    backup_file
)

print()
print(
    "September 2026 data added successfully."
)
print("=" * 60)