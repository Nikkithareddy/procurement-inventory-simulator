-- Procurement Cycle & Inventory Working Capital Simulator
-- Run against data/purchase_orders.csv and data/sku_master.csv loaded into SQLite
-- (see src/load_to_sqlite.py) as tables `po` and `sku`.

-- 1. Economic Order Quantity (EOQ) inputs & holding cost per SKU
SELECT
    s.sku_id,
    s.category,
    s.annual_demand_units,
    s.unit_cost_usd,
    s.ordering_cost_usd,
    ROUND(s.unit_cost_usd * s.holding_cost_rate, 2) AS holding_cost_per_unit,
    ROUND(SQRT((2.0 * s.annual_demand_units * s.ordering_cost_usd)
               / (s.unit_cost_usd * s.holding_cost_rate)), 0) AS eoq_units
FROM sku s
ORDER BY s.annual_demand_units DESC;

-- 2. Actual ordering behavior vs. EOQ-implied order count per SKU
SELECT
    s.sku_id,
    s.category,
    COUNT(p.po_id) AS actual_po_count_2yr,
    ROUND(AVG(p.order_qty), 1) AS actual_avg_order_qty,
    ROUND(s.annual_demand_units /
        SQRT((2.0 * s.annual_demand_units * s.ordering_cost_usd)
             / (s.unit_cost_usd * s.holding_cost_rate)), 1) AS eoq_orders_per_year
FROM sku s
JOIN po p ON p.sku_id = s.sku_id
GROUP BY s.sku_id
ORDER BY actual_po_count_2yr DESC;

-- 3. Working capital tied up in inventory, by category
SELECT
    s.category,
    COUNT(DISTINCT s.sku_id) AS sku_count,
    ROUND(SUM(avg_qty.actual_avg_order_qty * s.unit_cost_usd), 2) AS working_capital_actual_usd
FROM sku s
JOIN (
    SELECT sku_id, AVG(order_qty) AS actual_avg_order_qty
    FROM po
    GROUP BY sku_id
) avg_qty ON avg_qty.sku_id = s.sku_id
GROUP BY s.category
ORDER BY working_capital_actual_usd DESC;

-- 4. Purchase-order data validation checks
SELECT 'duplicate_po_ids' AS check_name, COUNT(*) - COUNT(DISTINCT po_id) AS issue_count FROM po
UNION ALL
SELECT 'zero_or_negative_qty', COUNT(*) FROM po WHERE order_qty <= 0
UNION ALL
SELECT 'orphan_sku_not_in_master', COUNT(*) FROM po WHERE sku_id NOT IN (SELECT sku_id FROM sku);

-- 5. Slow-moving SKUs: lowest inventory turnover (annual demand / avg stock on hand)
SELECT
    s.sku_id,
    s.category,
    s.annual_demand_units,
    ROUND(AVG(p.stock_on_hand_at_order), 1) AS avg_stock_on_hand,
    ROUND(s.annual_demand_units / NULLIF(AVG(p.stock_on_hand_at_order), 0), 2) AS inventory_turnover
FROM sku s
JOIN po p ON p.sku_id = s.sku_id
GROUP BY s.sku_id
ORDER BY inventory_turnover ASC
LIMIT 15;
