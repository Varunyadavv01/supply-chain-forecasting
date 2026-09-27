"""
ETL pipeline: pulls raw transaction-level sales data, cleans it, and rolls it
up into the aggregates a monthly sales report actually needs — replacing what
used to be a manual, spreadsheet-heavy process.
"""
import pandas as pd
import json

raw = pd.read_csv("sales_data.csv", parse_dates=["order_date"])

# --- Clean ---
before = len(raw)
raw = raw.drop_duplicates()
raw = raw[raw["quantity"] > 0]
raw = raw.dropna(subset=["region", "product", "revenue"])
print(f"Cleaned: {before:,} -> {len(raw):,} rows ({before - len(raw)} removed)")

raw["month"] = raw["order_date"].dt.strftime("%Y-%m")

# --- Aggregate: monthly revenue by region ---
monthly_region = raw.groupby(["month", "region"])["revenue"].sum().reset_index()
monthly_region.to_csv("monthly_revenue_by_region.csv", index=False)

# --- Aggregate: category performance ---
category_perf = raw.groupby("category").agg(
    revenue=("revenue", "sum"), units=("quantity", "sum"), orders=("revenue", "count")
).reset_index().sort_values("revenue", ascending=False)
category_perf.to_csv("category_performance.csv", index=False)

# --- Aggregate: region performance with month-over-month growth ---
region_monthly = raw.groupby(["region", "month"])["revenue"].sum().reset_index()
region_totals = raw.groupby("region")["revenue"].sum().sort_values(ascending=False)

first_month = region_monthly["month"].min()
last_month = region_monthly["month"].max()
growth = {}
for region in region_totals.index:
    r = region_monthly[region_monthly["region"] == region]
    first_val = r[r["month"] == first_month]["revenue"].sum()
    last_val = r[r["month"] == last_month]["revenue"].sum()
    growth[region] = round(((last_val - first_val) / first_val) * 100, 1) if first_val else None

# --- KPIs ---
kpis = {
    "total_revenue": round(raw["revenue"].sum(), 0),
    "total_orders": len(raw),
    "total_units": int(raw["quantity"].sum()),
    "avg_order_value": round(raw["revenue"].mean(), 0),
    "best_region": region_totals.index[0],
    "best_category": category_perf.iloc[0]["category"],
}

data = {
    "kpis": kpis,
    "monthly_labels": sorted(raw["month"].unique().tolist()),
    "monthly_revenue_overall": raw.groupby("month")["revenue"].sum().sort_index().round(0).tolist(),
    "region_labels": region_totals.index.tolist(),
    "region_values": region_totals.round(0).tolist(),
    "region_growth_pct": growth,
    "category_labels": category_perf["category"].tolist(),
    "category_values": category_perf["revenue"].round(0).tolist(),
    "top_products": raw.groupby("product")["revenue"].sum().sort_values(ascending=False).head(6).round(0).to_dict(),
}

with open("dashboard_data.json", "w") as f:
    json.dump(data, f)

print(json.dumps(kpis, indent=2))
print("\nRegion growth (first month -> last month):", growth)
