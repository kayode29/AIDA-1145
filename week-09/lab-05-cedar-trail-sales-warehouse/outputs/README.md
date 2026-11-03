# Required generated evidence

Generate outputs from your own completed pipeline. Do not edit generated totals by hand. Keep candidate and approved-v2 run files separate so that one run cannot overwrite evidence from the other.

Suggested files under `outputs/candidate/` and `outputs/approved-v2/`:

- `run_summary.json` — input filenames/version, row counts, control totals, check results, and release status;
- `row_ledger.json` — source, completed, cancelled, pending, fact, and distinct-order counts;
- `candidate_fact_sales.csv` or `fact_sales.csv` — one row per completed source order line, with dimension keys and line measures;
- `exception_rows.csv` — unmatched or invalid source records and the reason each needs review;
- `sales_by_month_category.csv` — completed net sales and units by month and product category;
- `sales_by_region.csv` — completed net sales and distinct completed orders by region;
- `order_value_summary.csv` — net sales, distinct order count, and average order value;
- `cedar_trail_warehouse.sqlite` — your local SQLite database, if you use the supplied scaffold approach.

Keep money values in integer cents in machine-readable totals. If you also provide a human-readable dollar amount, label it separately. Retain an output even when its decision is HOLD; the evidence explains why the run is not ready for the stated report.
