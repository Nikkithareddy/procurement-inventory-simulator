"""Generate synthetic purchase-order / SKU data for a procurement & inventory working-capital study."""
import numpy as np
import pandas as pd

np.random.seed(23)

n_skus = 60
categories = ["Raw Materials", "Packaging", "MRO Supplies", "Finished Components"]

skus = []
for i in range(n_skus):
    cat = categories[i % 4]
    annual_demand = np.random.randint(500, 20000)
    unit_cost = round(np.random.uniform(2, 250), 2)
    ordering_cost = round(np.random.uniform(35, 120), 2)      # cost to place 1 PO
    holding_cost_rate = round(np.random.uniform(0.15, 0.30), 3)  # % of unit cost per year
    lead_time_days = np.random.randint(3, 45)
    skus.append({
        "sku_id": f"SKU-{1000+i}",
        "category": cat,
        "annual_demand_units": annual_demand,
        "unit_cost_usd": unit_cost,
        "ordering_cost_usd": ordering_cost,
        "holding_cost_rate": holding_cost_rate,
        "lead_time_days": lead_time_days,
    })
sku_master = pd.DataFrame(skus)
sku_master.to_csv("data/sku_master.csv", index=False)

# ---- Purchase order transaction history (2 years) ----
rows = []
po_id = 1
for _, s in sku_master.iterrows():
    # simulate historical PO cadence: roughly annual_demand / avg_order_qty orders/year
    avg_order_qty = max(10, int(s["annual_demand_units"] / np.random.randint(4, 12)))
    n_orders = max(2, int(s["annual_demand_units"] / avg_order_qty * 2))  # 2 years
    order_dates = pd.to_datetime(
        np.random.choice(pd.date_range("2024-01-01", "2025-12-31"), size=n_orders, replace=True)
    )
    for d in sorted(order_dates):
        qty = max(1, int(np.random.normal(avg_order_qty, avg_order_qty * 0.25)))
        current_stock = max(0, int(np.random.normal(avg_order_qty * 0.6, avg_order_qty * 0.3)))
        rows.append({
            "po_id": f"PO-{po_id:05d}",
            "sku_id": s["sku_id"],
            "category": s["category"],
            "order_date": d.date(),
            "order_qty": qty,
            "unit_cost_usd": s["unit_cost_usd"],
            "stock_on_hand_at_order": current_stock,
            "lead_time_days": s["lead_time_days"],
        })
        po_id += 1

po_df = pd.DataFrame(rows)
po_df.to_csv("data/purchase_orders.csv", index=False)
print("SKUs:", len(sku_master), "| POs:", len(po_df))
