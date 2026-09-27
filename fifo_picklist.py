"""
FIFO-based picklist: for each store-SKU, orders batches oldest-first so pickers
always pull the batch closest to expiry, reducing wastage risk.
"""
import pandas as pd
from datetime import datetime

batches = pd.read_csv("batch_data.csv")
batches["received_date"] = pd.to_datetime(batches["received_date"])
batches["days_held"] = (datetime(2026, 6, 29) - batches["received_date"]).dt.days
batches["days_to_expiry"] = batches["shelf_life_days"] - batches["days_held"]
batches["expiry_risk"] = batches["days_to_expiry"].apply(
    lambda d: "Urgent" if d <= 3 else ("Watch" if d <= 7 else "OK")
)

# FIFO pick order: oldest batch (received first / closest to expiry) picked first
picklist = batches.sort_values(["store", "sku_id", "received_date"]).copy()
picklist["pick_sequence"] = picklist.groupby(["store", "sku_id"]).cumcount() + 1

picklist = picklist[["store", "sku_id", "batch_id", "pick_sequence", "quantity",
                      "received_date", "days_to_expiry", "expiry_risk"]]
picklist.to_csv("fifo_picklist.csv", index=False)

print(f"Batches processed: {len(picklist):,}")
print(picklist["expiry_risk"].value_counts())
print()
print("Sample picklist (oldest picked first):")
print(picklist.sort_values("days_to_expiry").head(10).to_string(index=False))
