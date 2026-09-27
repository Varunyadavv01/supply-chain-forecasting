# Supply Chain Replenishment & Demand Forecasting System

Simulates a 9-store quick-commerce ("dark store") network and builds an
end-to-end inventory decision pipeline: SKU rationalization, daily
replenishment, and FIFO-based picklists to cut expiry losses.

## What this does

1. **`generate_data.py`** — creates a realistic synthetic dataset: 90 days of
   sales across 9 stores × 30 SKUs, current inventory snapshots, in-transit
   stock, store capacity limits, and batch-level receiving data.

2. **`abc_velocity_analysis.py`** — classifies every SKU into A/B/C tiers by
   revenue contribution (Pareto analysis), and separately tags each SKU's
   sales velocity (High/Medium/Low). SKUs that are both C-class and
   low-velocity are flagged as slow-moving candidates for de-listing.

3. **`replenishment_model.py`** — for every store-SKU pair, calculates how
   much stock to order today. The order quantity is bounded by:
   - target stock level (based on lead time + a safety buffer that's larger
     for A-class SKUs than C-class)
   - stock already on hand + already in transit
   - the store's physical capacity for that SKU (never over-orders)

   It also flags pairs at **high stockout risk** — where current + in-transit
   stock won't cover demand through the next delivery.

4. **`fifo_picklist.py`** — orders every batch by received date (oldest
   first) so warehouse pickers always pull stock closest to expiry first,
   and flags batches that are **Urgent** (≤3 days to expiry), **Watch**
   (≤7 days), or **OK**.

5. **`dashboard.html`** — a standalone interactive dashboard (just open it in
   a browser, no server needed) summarizing revenue trends, ABC split,
   category/store performance, stockout risk, and expiry risk.

## Run it yourself

```bash
pip install pandas numpy
python3 generate_data.py
python3 abc_velocity_analysis.py
python3 replenishment_model.py
python3 fifo_picklist.py
python3 build_dashboard_data.py   # refreshes dashboard_data.json
```

Then open `dashboard.html` in any browser.

## Sample results (this run)

- 90-day network revenue: ₹11.2 Cr across 676K units
- 10 A-class SKUs drive 69% of total revenue
- 149 store-SKU pairs needed a reorder on the snapshot day; 21 were at high
  stockout risk
- 29 batches were within 3 days of expiry and needed urgent picking priority
- 8 SKUs flagged as slow-moving, candidates to de-list or discount

## Tech used

Python, pandas, NumPy for the data pipeline and modeling; Chart.js for the
dashboard visualization.
