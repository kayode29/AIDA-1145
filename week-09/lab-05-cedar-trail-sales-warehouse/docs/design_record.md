# Design record — Cedar Trail sales warehouse

## 1. Business question and scope

Cedar Trail Outdoor Co-op managers require sales reports showing completed sales by month, product category, and store region. They also need the average net value of a completed order.

Only records with status `COMPLETED` will be included in the sales fact table and completed-sales reports. Records with status `CANCELLED` and `PENDING` will be excluded from sales measures but retained in the row ledger for audit and reconciliation purposes.

This approach ensures that cancelled and pending transactions are not incorrectly reported as completed sales. All original source records will be preserved.

## 2. Grain and identifiers

The grain of `fact_sales` is one row for each product line on one completed customer order.

- `line_id` identifies one unique source order line.
- `order_id` identifies the complete customer order and may repeat because one order can contain multiple product lines.
- Each completed source line should produce exactly one fact row, including lines with unmatched products.
- Completed order counts must use `COUNT(DISTINCT order_id)`.
- Completed line counts must use `COUNT(*)` or `COUNT(DISTINCT line_id)` after confirming line uniqueness.

The fact table will retain `order_id` as a degenerate identifier and `line_id` as the unique source line identifier.

## 3. Dimensions and keys

| Dimension | Purpose | Business key | Attributes needed | Fact relationship |
|---|---|---|---|---|
| Date | Supports monthly and date-based sales analysis | order_date | Full date, year, month, month name | date_key |
| Product | Supports product and category analysis | sku | Product name, category | product_key |
| Customer | Identifies customers and their segments | customer_id | Customer name, customer segment | customer_key |
| Store | Identifies stores and their regions | store_code | Store name, region | store_key |

The warehouse will use integer surrogate primary keys for the dimension tables. Each dimension will also enforce uniqueness on its source business key.

The fact table will store the four corresponding foreign keys: `date_key`, `product_key`, `customer_key`, and `store_key`.

The Python pipeline will load dimension records and create lookup dictionaries that translate source business keys into warehouse surrogate keys.

If a completed sales line contains a product SKU that cannot be matched, the pipeline will assign an explicitly identified unknown product dimension member. The original source SKU will be retained for traceability, and an exception record will identify the unmatched product. The transaction will not be silently removed or assigned to an invented product.

For the candidate catalogue, SKU-999 is expected to be unmatched. The approved-v2 catalogue documents its product mapping.

## 4. Measures and formulas

The sales measures will be calculated using integer cents.

- Gross sales: `quantity * unit_price_cents`
- Discount: `round_half_up(gross_cents * discount_rate)`
- Net sales: `gross_cents - discount_cents`

Discount calculations will use consistent round-half-up rounding to the nearest whole cent.

The fact table will contain these measures:

- `quantity`
- `gross_cents`
- `discount_cents`
- `net_cents`

Quantity, gross sales, discount, and net sales can be summed across the appropriate reporting scope.

Average order value is an order-level measure. It must be calculated as:

`SUM(net_cents) / COUNT(DISTINCT order_id)`

It must not be calculated by dividing net sales by the number of fact rows because an order can contain multiple sales lines.

## 5. Join and quality reasoning

Dimension business keys must be unique. If a dimension contains duplicate business keys, the pipeline must report the problem and prevent an unreliable warehouse load.

The pipeline will validate the following:

- Required source fields are present.
- Source line IDs are unique.
- Order dates use the required ISO format.
- Quantities are positive whole numbers.
- Prices and discount rates are valid.
- Only completed lines enter the sales fact table.
- Cancelled and pending lines remain visible in the row ledger.
- Customer and store references match their catalogues.
- Product matches are checked against the selected catalogue version.
- Missing product matches are preserved and reported as exceptions.
- Gross, discount, and net calculations are correct.
- Fact row counts agree with the completed source-line counts.
- Warehouse totals reconcile with independently calculated source totals.

The reconciliation will compare:

- Total input rows.
- Completed, cancelled, and pending rows.
- Completed source lines and warehouse fact rows.
- Distinct completed order counts.
- Total completed units.
- Gross sales, discounts, and net sales in cents.
- Missing product mappings and exception counts.

A HOLD decision will be appropriate if required fields are invalid, business keys are duplicated, foreign-key relationships are unreliable, sales lines are lost, money calculations are incorrect, or warehouse totals do not reconcile.

A documented unmatched product in the candidate catalogue will also be reported as a limitation and evaluated separately from the approved-v2 run.

## 6. Limitations

This is a small classroom sales warehouse based on the supplied fictional CSV files.

The model assumes that each source line represents one product line, each line has one selling store and customer, and the supplied catalogue attributes are suitable for the reporting period.

The model does not currently address inventory balances, supplier purchases, product returns, taxes, shipping charges, payment methods, or historical changes in customer and product attributes.

The model is designed for completed-sales reporting and basic reconciliation rather than a full enterprise sales and inventory system.