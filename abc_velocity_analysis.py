"""
SKU rationalization: ABC classification (by revenue contribution) combined with
velocity analysis (units sold per day), across all 9 dark stores.
"""
import pandas as pd

sales = pd.read_csv("sales_data.csv")

# Revenue and units contribution per SKU, across the network
sku_summary = sales.groupby("sku_id").agg(
    total_revenue=("revenue", "sum"),
    total_units=("units_sold", "sum"),
    category=("category", "first"),
).reset_index()

n_days = sales["date"].nunique()
sku_summary["velocity_units_per_day"] = sku_summary["total_units"] / n_days

# ABC classification by cumulative revenue share (Pareto)
sku_summary = sku_summary.sort_values("total_revenue", ascending=False).reset_index(drop=True)
sku_summary["revenue_share"] = sku_summary["total_revenue"] / sku_summary["total_revenue"].sum()
sku_summary["cumulative_share"] = sku_summary["revenue_share"].cumsum()


def classify(cum_share):
    if cum_share <= 0.70:
        return "A"
    elif cum_share <= 0.90:
        return "B"
    return "C"


sku_summary["abc_class"] = sku_summary["cumulative_share"].apply(classify)

# Velocity tier, independent cut, to catch high-velocity/low-revenue items too
sku_summary["velocity_tier"] = pd.qcut(
    sku_summary["velocity_units_per_day"], q=3, labels=["Low", "Medium", "High"]
)

sku_summary.to_csv("sku_classification.csv", index=False)

print(sku_summary[["sku_id", "category", "total_revenue", "abc_class", "velocity_tier"]].head(10).to_string(index=False))
print()
print("Class distribution:")
print(sku_summary["abc_class"].value_counts())
print()
print(f"A-class SKUs ({(sku_summary['abc_class']=='A').sum()}) drive "
      f"{sku_summary[sku_summary['abc_class']=='A']['revenue_share'].sum():.1%} of revenue")

# Flag slow-moving stock: C-class AND Low velocity -> candidates to de-list / cut
slow_movers = sku_summary[(sku_summary["abc_class"] == "C") & (sku_summary["velocity_tier"] == "Low")]
slow_movers.to_csv("slow_moving_candidates.csv", index=False)
print(f"\nFlagged {len(slow_movers)} SKUs as slow-moving candidates -> slow_moving_candidates.csv")
