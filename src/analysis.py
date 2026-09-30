"""
Procurement Cycle & Inventory Working Capital Simulator
------------------------------------------------------------
1. Evaluate EOQ, holding costs, and procurement trade-offs affecting working capital.
2. Standardize/validate procurement datasets for operational analysis.
3. Identify slow-moving SKUs and quantify potential working-capital improvements.
"""
import json
import numpy as np
import pandas as pd

sku = pd.read_csv("data/sku_master.csv")
po = pd.read_csv("data/purchase_orders.csv", parse_dates=["order_date"])

# ---------- Data validation / standardization ----------
issues = []
issues.append(("missing_values", int(po.isna().sum().sum())))
issues.append(("duplicate_po_ids", int(po["po_id"].duplicated().sum())))
issues.append(("negative_or_zero_qty", int((po["order_qty"] <= 0).sum())))
issues.append(("orphan_skus_in_po_not_in_master", int((~po["sku_id"].isin(sku["sku_id"])).sum())))
validation_report = pd.DataFrame(issues, columns=["check", "count"])
validation_report.to_csv("data/validation_report.csv", index=False)

# ---------- 1. Economic Order Quantity (EOQ) & holding cost ----------
def eoq(annual_demand, ordering_cost, holding_cost_per_unit):
    return np.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)

sku["holding_cost_per_unit"] = sku["unit_cost_usd"] * sku["holding_cost_rate"]
sku["eoq_units"] = eoq(sku["annual_demand_units"], sku["ordering_cost_usd"], sku["holding_cost_per_unit"]).round(0)
sku["orders_per_year_optimal"] = (sku["annual_demand_units"] / sku["eoq_units"]).round(1)
sku["annual_ordering_cost_optimal"] = (sku["orders_per_year_optimal"] * sku["ordering_cost_usd"]).round(2)
sku["annual_holding_cost_optimal"] = (sku["eoq_units"] / 2 * sku["holding_cost_per_unit"]).round(2)
sku["total_annual_cost_optimal"] = (sku["annual_ordering_cost_optimal"] + sku["annual_holding_cost_optimal"]).round(2)

# ---------- Compare against actual historical ordering behavior ----------
actual_stats = (po.groupby("sku_id")
                  .agg(actual_avg_order_qty=("order_qty", "mean"),
                       actual_orders_per_2yr=("po_id", "count"))
                  .reset_index())
actual_stats["actual_orders_per_year"] = (actual_stats["actual_orders_per_2yr"] / 2).round(1)

merged = sku.merge(actual_stats, on="sku_id", how="left")
merged["actual_annual_ordering_cost"] = (merged["actual_orders_per_year"] * merged["ordering_cost_usd"]).round(2)
merged["actual_annual_holding_cost"] = (merged["actual_avg_order_qty"] / 2 * merged["holding_cost_per_unit"]).round(2)
merged["actual_total_annual_cost"] = (merged["actual_annual_ordering_cost"] + merged["actual_annual_holding_cost"]).round(2)
merged["potential_annual_savings"] = (merged["actual_total_annual_cost"] - merged["total_annual_cost_optimal"]).round(2)
merged.to_csv("data/eoq_analysis.csv", index=False)

# ---------- 2. Working capital tied up in inventory ----------
merged["working_capital_actual_usd"] = (merged["actual_avg_order_qty"] * merged["unit_cost_usd"]).round(2)
merged["working_capital_optimal_usd"] = (merged["eoq_units"] / 2 * merged["unit_cost_usd"]).round(2)
merged["working_capital_freed_usd"] = (merged["working_capital_actual_usd"] - merged["working_capital_optimal_usd"]).round(2)

# ---------- 3. Slow-moving SKU detection ----------
# Slow-moving = bottom quartile of (annual demand / avg on-hand stock) turnover ratio
stock_stats = po.groupby("sku_id")["stock_on_hand_at_order"].mean().rename("avg_stock_on_hand").reset_index()
merged = merged.merge(stock_stats, on="sku_id", how="left")
merged["inventory_turnover"] = (merged["annual_demand_units"] / merged["avg_stock_on_hand"].replace(0, np.nan)).round(2)
turnover_q1 = merged["inventory_turnover"].quantile(0.25)
merged["slow_moving"] = merged["inventory_turnover"] <= turnover_q1

merged.to_csv("data/inventory_working_capital.csv", index=False)
slow_movers = merged[merged["slow_moving"]].sort_values("inventory_turnover")
slow_movers.to_csv("data/slow_moving_skus.csv", index=False)

summary = {
    "total_skus_analyzed": int(len(merged)),
    "total_pos_analyzed": int(len(po)),
    "validation_issues_found": int(validation_report["count"].sum()),
    "avg_potential_annual_savings_per_sku_usd": round(merged["potential_annual_savings"].mean(), 2),
    "total_potential_annual_savings_usd": round(merged["potential_annual_savings"].sum(), 2),
    "total_working_capital_freed_usd": round(merged["working_capital_freed_usd"].sum(), 2),
    "slow_moving_sku_count": int(merged["slow_moving"].sum()),
    "slow_moving_sku_share_pct": round(100 * merged["slow_moving"].mean(), 1),
    "slow_moving_working_capital_usd": round(slow_movers["working_capital_actual_usd"].sum(), 2),
}
with open("data/summary_metrics.json", "w") as f:
    json.dump(summary, f, indent=2)

print(json.dumps(summary, indent=2))
print("\nTop 5 SKUs by potential annual savings:\n",
      merged.sort_values("potential_annual_savings", ascending=False)
            [["sku_id", "category", "potential_annual_savings", "working_capital_freed_usd"]]
            .head(5).to_string(index=False))
