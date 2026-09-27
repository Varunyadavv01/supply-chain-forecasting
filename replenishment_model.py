"""
Daily replenishment model: for each store-SKU pair, decides how much stock to
order today, factoring in current on-hand inventory, stock already in transit,
lead time, and the store's physical capacity limit for that SKU.
"""
import pandas as pd
import numpy as np

inv = pd.read_csv("inventory_snapshot.csv")
sku_class = pd.read_csv("sku_classification.csv")[["sku_id", "abc_class"]]
inv = inv.merge(sku_class, on="sku_id")

# Safety stock: more days of cover for A-class (can't afford stockouts),
# leaner for C-class (avoid tying up capacity on slow movers)
SAFETY_DAYS = {"A": 5, "B": 3, "C": 1.5}

inv["safety_days"] = inv["abc_class"].map(SAFETY_DAYS)
inv["target_stock"] = inv["avg_daily_sales"] * (inv["lead_time_days"] + inv["safety_days"])
inv["effective_stock"] = inv["on_hand_units"] + inv["in_transit_units"]
inv["raw_order_qty"] = (inv["target_stock"] - inv["effective_stock"]).clip(lower=0)

# Cap the order so on-hand + in-transit + new order never exceeds store capacity
inv["max_allowed"] = (inv["store_capacity_units"] - inv["effective_stock"]).clip(lower=0)
inv["recommended_order_qty"] = np.minimum(inv["raw_order_qty"], inv["max_allowed"]).round().astype(int)

inv["stockout_risk"] = np.where(
    inv["effective_stock"] < inv["avg_daily_sales"] * inv["lead_time_days"], "High", "Low"
)

inv.to_csv("replenishment_plan.csv", index=False)

print(f"Store-SKU pairs evaluated: {len(inv):,}")
print(f"Pairs needing an order today: {(inv['recommended_order_qty'] > 0).sum():,}")
print(f"Pairs at High stockout risk: {(inv['stockout_risk']=='High').sum():,}")
print(f"Total units recommended to order across network: {inv['recommended_order_qty'].sum():,}")
print()
print(inv.sort_values('recommended_order_qty', ascending=False)
      [["store", "sku_id", "abc_class", "on_hand_units", "in_transit_units",
        "recommended_order_qty", "stockout_risk"]].head(10).to_string(index=False))
