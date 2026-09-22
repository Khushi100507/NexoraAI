from pathlib import Path
import random
import pandas as pd
import numpy as np


BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

SALES = DATA / "sales.csv"
ORDERS = DATA / "orders.csv"
CUSTOMERS = DATA / "customers.csv"
FINANCE = DATA / "finance.csv"
MARKETING = DATA / "marketing.csv"

START = pd.Timestamp("2026-09-01")
END = pd.Timestamp("2026-09-30")

random.seed(42)
np.random.seed(42)


def backup(file):
    backup_file = file.with_name(
        file.stem + "_before_september_backup" + file.suffix
    )
    if not backup_file.exists():
        pd.read_csv(file).to_csv(backup_file, index=False)
    return backup_file


# ============================================================
# LOAD
# ============================================================

sales = pd.read_csv(SALES)
orders = pd.read_csv(ORDERS)
customers = pd.read_csv(CUSTOMERS)
finance = pd.read_csv(FINANCE)
marketing = pd.read_csv(MARKETING)

sales["date"] = pd.to_datetime(
    sales["date"],
    format="mixed"
)

orders["date"] = pd.to_datetime(
    orders["date"],
    format="mixed"
)

customers["last_purchase"] = pd.to_datetime(
    customers["last_purchase"],
    format="mixed"
)

finance["date"] = pd.to_datetime(
    finance["date"],
    format="mixed"
)

marketing["date"] = pd.to_datetime(
    marketing["date"],
    format="mixed"
)


# ============================================================
# CHECK SEPTEMBER SALES
# ============================================================

sept_sales = sales[
    (sales["date"] >= START)
    & (sales["date"] <= END)
].copy()

if sept_sales.empty:
    raise ValueError(
        "No September sales found. Run extend_september.py first."
    )


print()
print("=" * 65)
print("NEXORAAI — SEPTEMBER BUSINESS DATA EXTENSION")
print("=" * 65)


# ============================================================
# 1. ORDERS
# ============================================================

sept_orders = orders[
    (orders["date"] >= START)
    & (orders["date"] <= END)
]

if sept_orders.empty:

    new_orders = pd.DataFrame({
        "order_id": sept_sales["order_id"].astype(int),
        "date": sept_sales["date"],
        "customer_id": sept_sales["customer_id"].astype(int),
        "status": [
            random.choices(
                ["completed", "pending", "cancelled"],
                weights=[90, 7, 3]
            )[0]
            for _ in range(len(sept_sales))
        ],
        "region": sept_sales["region"],
        "channel": sept_sales["channel"]
    })

    orders = pd.concat(
        [orders, new_orders],
        ignore_index=True
    )

    orders.to_csv(ORDERS, index=False)

    print(
        f"Orders added      : {len(new_orders):,}"
    )

else:

    print(
        f"Orders already exist for September: "
        f"{len(sept_orders):,}"
    )


# ============================================================
# 2. FINANCE
# ============================================================

sept_finance = finance[
    (finance["date"] >= START)
    & (finance["date"] <= END)
]

if sept_finance.empty:

    daily_finance = (
        sept_sales
        .groupby("date", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            expense=("expense", "sum"),
            profit=("profit", "sum")
        )
    )

    finance = pd.concat(
        [finance, daily_finance],
        ignore_index=True
    )

    finance.to_csv(FINANCE, index=False)

    print(
        f"Finance days added: {len(daily_finance):,}"
    )

else:

    print(
        f"Finance already exists for September: "
        f"{len(sept_finance):,} days"
    )


# ============================================================
# 3. MARKETING
# ============================================================

sept_marketing = marketing[
    (marketing["date"] >= START)
    & (marketing["date"] <= END)
]

if sept_marketing.empty:

    campaigns = [
        "Search",
        "Social Media",
        "Email",
        "Partner",
        "Display"
    ]

    marketing_rows = []

    for day in pd.date_range(START, END):

        campaign = random.choice(campaigns)

        spend = round(
            random.uniform(25000, 80000),
            2
        )

        leads = random.randint(
            500,
            1800
        )

        conversions = random.randint(
            max(10, int(leads * 0.08)),
            max(20, int(leads * 0.20))
        )

        conversion_rate = (
            conversions / leads
        ) * 100

        marketing_rows.append({
            "date": day,
            "campaign": campaign,
            "spend": spend,
            "leads": leads,
            "conversions": conversions,
            "conversion_rate": round(
                conversion_rate,
                2
            )
        })

    new_marketing = pd.DataFrame(
        marketing_rows
    )

    marketing = pd.concat(
        [marketing, new_marketing],
        ignore_index=True
    )

    marketing.to_csv(
        MARKETING,
        index=False
    )

    print(
        f"Marketing days added: "
        f"{len(new_marketing):,}"
    )

else:

    print(
        f"Marketing already exists for September: "
        f"{len(sept_marketing):,} days"
    )


# ============================================================
# 4. CUSTOMER METRICS
# ============================================================

customer_updates = (
    sept_sales
    .groupby("customer_id")
    .agg(
        september_orders=("order_id", "nunique"),
        september_value=("revenue", "sum"),
        last_purchase_september=("date", "max")
    )
)

updated_customers = 0

for customer_id, row in customer_updates.iterrows():

    mask = (
        customers["customer_id"].astype(int)
        == int(customer_id)
    )

    if not mask.any():
        continue

    index = customers.index[mask][0]

    customers.loc[
        index,
        "orders_count"
    ] += int(row["september_orders"])

    customers.loc[
        index,
        "lifetime_value"
    ] += float(row["september_value"])

    old_date = customers.loc[
        index,
        "last_purchase"
    ]

    new_date = row[
        "last_purchase_september"
    ]

    if pd.isna(old_date) or new_date > old_date:

        customers.loc[
            index,
            "last_purchase"
        ] = new_date

    updated_customers += 1


customers.to_csv(
    CUSTOMERS,
    index=False
)


# ============================================================
# BACKUPS
# ============================================================

backup(ORDERS)
backup(CUSTOMERS)
backup(FINANCE)
backup(MARKETING)


# ============================================================
# FINAL SUMMARY
# ============================================================

print(
    f"Customers updated : {updated_customers:,}"
)

print()
print("September business data is now connected:")
print("  Sales      ✓")
print("  Orders     ✓")
print("  Finance    ✓")
print("  Marketing  ✓")
print("  Customers  ✓")

print()
print(
    f"September Revenue : "
    f"₹{sept_sales['revenue'].sum():,.2f}"
)

print(
    f"September Profit  : "
    f"₹{sept_sales['profit'].sum():,.2f}"
)

print()
print("=" * 65)
print("SEPTEMBER 2026 BUSINESS DATA READY")
print("=" * 65)