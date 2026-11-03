
-- ============================================================
-- AIDA 1145 - Week 9 Graded Lab 5
-- Sales by Calendar Month and Product Category
--
-- Fact grain: one completed sales order line.
-- Net sales are stored in integer cents.
-- ============================================================

SELECT
    d.calendar_year AS sales_year,
    d.calendar_month AS sales_month,
    d.month_name AS month_name,
    p.category AS product_category,

    SUM(f.net_cents) AS completed_net_sales_cents,

    SUM(f.quantity) AS completed_units_sold

FROM fact_sales AS f

INNER JOIN dim_date AS d
    ON f.date_key = d.date_key

INNER JOIN dim_product AS p
    ON f.product_key = p.product_key

GROUP BY
    d.calendar_year,
    d.calendar_month,
    d.month_name,
    p.category

ORDER BY
    d.calendar_year,
    d.calendar_month,
    p.category;
