
-- ============================================================
-- AIDA 1145 - Week 9 Graded Lab 5
-- Completed Order Value Summary
--
-- Fact grain: one completed sales order line.
-- AOV = total completed net sales / distinct completed orders.
-- ============================================================

SELECT
    SUM(net_cents) AS total_completed_net_sales_cents,

    COUNT(DISTINCT order_id) AS completed_order_count,

    ROUND(
        1.0 * SUM(net_cents) /
        NULLIF(COUNT(DISTINCT order_id), 0),
        2
    ) AS average_order_value_cents

FROM fact_sales;

