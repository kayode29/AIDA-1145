
-- ============================================================
-- AIDA 1145 - Week 9 Graded Lab 5
-- Completed Sales by Store Region
--
-- Fact grain: one completed sales order line.
-- Count distinct orders to avoid counting multi-line
-- orders more than once.
-- ============================================================

SELECT
    s.region AS store_region,

    SUM(f.net_cents) AS completed_net_sales_cents,

    COUNT(DISTINCT f.order_id) AS completed_order_count

FROM fact_sales AS f

INNER JOIN dim_store AS s
    ON f.store_key = s.store_key

GROUP BY
    s.region

ORDER BY
    s.region;

