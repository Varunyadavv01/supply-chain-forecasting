"""
Generates synthetic 90-day sales, inventory, and batch data across 9 dark stores
and 30 SKUs, to simulate a real quick-commerce style retail dataset.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

STORES = [f"Store_{i+1}" for i in range(9)]
CATEGORIES = ["Beverages", "Snacks", "Dairy", "Personal Care", "Household"]
N_SKUS = 30

# Give each SKU a category and a "true" popularity tier so ABC classification
# has a realistic underlying signal, not pure noise.
sku_info = []
for i in range(N_SKUS):
    tier = np.random.choice(["A", "B", "C"], p=[0.2, 0.3, 0.5])
    base_demand = {"A": np.random.uniform(40, 80), "B": np.random.uniform(15, 35), "C": np.random.uniform(2, 12)}[tier]
    sku_info.append({
        "sku_id": f"SKU_{i+1:03d}",
        "category": np.random.choice(CATEGORIES),
        "true_tier": tier,
        "base_demand": base_demand,
        "unit_cost": round(np.random.uniform(20, 400), 2),
        "shelf_life_days": int(np.random.choice([7, 14, 30, 90, 365])),
    })
sku_df = pd.DataFrame(sku_info)

start_date = datetime(2026, 4, 1)
dates = [start_date + timedelta(days=d) for d in range(90)]

rows = []
for store in STORES:
    store_factor = np.random.uniform(0.8, 1.3)  # some stores just sell more
    for _, sku in sku_df.iterrows():
        for d in dates:
            weekday_boost = 1.25 if d.weekday() >= 5 else 1.0
            noise = np.random.poisson(max(sku["base_demand"] * store_factor * weekday_boost, 0.5))
            rows.append({
                "date": d.strftime("%Y-%m-%d"),
                "store": store,
                "sku_id": sku["sku_id"],
                "category": sku["category"],
                "units_sold": int(noise),
            })

sales_df = pd.DataFrame(rows)
sales_df = sales_df.merge(sku_df[["sku_id", "unit_cost", "shelf_life_days", "true_tier"]], on="sku_id")
sales_df["revenue"] = sales_df["units_sold"] * sales_df["unit_cost"]

# Current inventory snapshot (as of last date), in-transit stock, and store capacity per SKU
snapshot = []
last_30 = sales_df[sales_df["date"] >= (start_date + timedelta(days=60)).strftime("%Y-%m-%d")]
avg_daily = last_30.groupby(["store", "sku_id"])["units_sold"].mean().reset_index()
avg_daily.columns = ["store", "sku_id", "avg_daily_sales"]

for _, r in avg_daily.iterrows():
    on_hand = max(int(np.random.normal(r["avg_daily_sales"] * np.random.uniform(2, 6), 3)), 0)
    in_transit = int(np.random.choice([0, 0, 0, r["avg_daily_sales"] * 3], p=[0.5, 0.2, 0.2, 0.1])) if np.random.rand() > 0.3 else 0
    snapshot.append({
        "store": r["store"],
        "sku_id": r["sku_id"],
        "avg_daily_sales": round(r["avg_daily_sales"], 2),
        "on_hand_units": on_hand,
        "in_transit_units": int(in_transit),
        "store_capacity_units": int(np.random.uniform(150, 400)),
        "lead_time_days": int(np.random.choice([1, 2, 3])),
    })
inventory_df = pd.DataFrame(snapshot)

# Batch-level data for FIFO picklist logic
batches = []
for _, r in inventory_df.iterrows():
    remaining = r["on_hand_units"]
    n_batches = np.random.randint(1, 4)
    for b in range(n_batches):
        if remaining <= 0:
            break
        qty = int(remaining / (n_batches - b)) if b < n_batches - 1 else remaining
        qty = min(qty, remaining)
        remaining -= qty
        sku_row = sku_df[sku_df["sku_id"] == r["sku_id"]].iloc[0]
        received_days_ago = np.random.randint(0, int(sku_row["shelf_life_days"] * 0.8) + 1)
        batches.append({
            "store": r["store"],
            "sku_id": r["sku_id"],
            "batch_id": f"{r['sku_id']}_{r['store']}_{b+1}",
            "quantity": qty,
            "received_date": (start_date + timedelta(days=89 - received_days_ago)).strftime("%Y-%m-%d"),
            "shelf_life_days": int(sku_row["shelf_life_days"]),
        })
batch_df = pd.DataFrame(batches)

sales_df.to_csv("sales_data.csv", index=False)
sku_df.to_csv("sku_master.csv", index=False)
inventory_df.to_csv("inventory_snapshot.csv", index=False)
batch_df.to_csv("batch_data.csv", index=False)

print("Generated:")
print(f"  sales_data.csv        {len(sales_df):,} rows")
print(f"  sku_master.csv        {len(sku_df):,} rows")
print(f"  inventory_snapshot.csv {len(inventory_df):,} rows")
print(f"  batch_data.csv        {len(batch_df):,} rows")
