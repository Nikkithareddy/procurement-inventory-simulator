# Procurement Cycle & Inventory Working Capital Simulator

**Tech Stack:** Python, SQL, Power BI-style dashboard (Plotly), MS Excel-compatible CSV outputs

A simulated procurement analytics project that evaluates EOQ (Economic Order Quantity), holding
costs, and procurement trade-offs affecting working capital — then identifies slow-moving SKUs
and quantifies the working-capital improvement available by moving from actual historical
ordering behavior to an EOQ-optimal policy.

> **Note on data:** this project uses a synthetically generated dataset — 60 SKUs across 4
> categories (`src/generate_data.py`) with realistic demand, cost, and lead-time profiles, plus
> 2 years of purchase-order transaction history (856 POs) — so the full pipeline can be
> reproduced end-to-end.

## What it does

1. **Data validation & standardization** — checks the purchase-order dataset for missing
   values, duplicate PO IDs, non-positive quantities, and orphaned SKU references before any
   analysis runs.
2. **EOQ & holding-cost analysis** — computes the classic EOQ
   (`sqrt(2 * annual_demand * ordering_cost / holding_cost_per_unit)`) per SKU, then compares the
   optimal annual ordering + holding cost against the cost implied by actual historical ordering
   behavior.
3. **Working-capital quantification** — translates the gap between actual average order
   quantity and EOQ into dollars of inventory-related working capital that could be freed up.
4. **Slow-moving SKU detection** — flags the bottom quartile of SKUs by inventory turnover
   (`annual demand / avg stock on hand`) as candidates for demand-driven reordering or write-down review.

## Key results (from this run)

| Metric | Value |
|---|---|
| SKUs analyzed | 60 |
| Purchase orders analyzed | 856 |
| Data validation issues found | 0 |
| Total potential annual savings (EOQ vs. actual) | ~$986K |
| Total working capital freed (EOQ-optimal vs. actual) | ~$10.8M |
| Slow-moving SKUs flagged | 15 (25% of SKUs) |

*(All figures are illustrative outputs of the synthetic dataset, reproducible by re-running the
pipeline — see below.)*

## Project structure

```
data/                          generated & derived CSVs (SKU master, POs, EOQ analysis, slow movers)
src/generate_data.py           synthetic SKU master + 2-year purchase-order history generator
src/analysis.py                validation, EOQ/holding-cost analysis, working capital, slow-mover detection
src/load_to_sqlite.py          loads CSVs into SQLite and runs sql/queries.sql
sql/queries.sql                EOQ, actual-vs-optimal, working-capital, validation, and turnover SQL views
src/build_dashboard.py         builds the interactive HTML/Plotly dashboard
dashboard/dashboard.html       self-contained interactive dashboard (open directly in a browser)
```

## How to run

```bash
pip install -r requirements.txt
python src/generate_data.py       # 1. generate synthetic SKU master + purchase-order history
python src/analysis.py            # 2. run validation / EOQ / working-capital / slow-mover analysis
python src/load_to_sqlite.py       # 3. (optional) run the SQL views
python src/build_dashboard.py      # 4. build dashboard/dashboard.html
```

Then open `dashboard/dashboard.html` in any browser — it's fully self-contained.

## Why a Plotly dashboard instead of a `.pbix` file?

The dashboard reproduces the same core views a Power BI report would have (working capital by
category, savings opportunity by category, slow-moving SKUs, actual-vs-EOQ order quantities), as
a portable HTML file viewable without Power BI Desktop installed. The underlying `data/*.csv`
files are Power BI/Excel-ready if you want to load them into an actual `.pbix` report.

## Methodology notes

- **EOQ**: `sqrt(2 * D * S / H)` where `D` = annual demand, `S` = ordering cost per PO,
  `H` = holding cost per unit per year (`unit_cost * holding_cost_rate`).
- **Working capital (actual)** = `actual_avg_order_qty * unit_cost`; **(optimal)** =
  `(EOQ / 2) * unit_cost`, i.e. average cycle-stock investment under each policy.
- **Inventory turnover** = `annual_demand_units / avg_stock_on_hand`; SKUs in the bottom quartile
  are flagged as slow-moving.
