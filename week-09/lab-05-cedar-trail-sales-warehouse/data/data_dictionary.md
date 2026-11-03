# Data dictionary and business rules

## `order_lines.csv`

| Field | Meaning | Rule |
|---|---|---|
| `line_id` | Unique source identifier for one order line. | Must be present and unique. |
| `order_id` | Identifier for the full customer order. | May repeat because an order can contain multiple lines. |
| `order_date` | Business date when the order was placed. | ISO format: `YYYY-MM-DD`. |
| `store_code` | Source key for the selling store. | Match to `store_catalog.csv`. |
| `customer_id` | Source key for the customer. | Match to `customer_catalog.csv`. |
| `sku` | Source product code. | Match to the selected product catalogue version. |
| `quantity` | Number of units on this line. | Positive whole number. |
| `unit_price_cents` | Unit price in integer cents. | Example: `3499` means $34.99. |
| `discount_rate` | Fractional discount applied to gross line sales. | `0.10` means 10%. Store/parse as a decimal, not a whole-number percent. |
| `status` | Order-line business status. | Only `COMPLETED` is included in completed-sales reports. `CANCELLED` and `PENDING` are out of scope for those measures. |

## Reference files

- `product_catalog_candidate.csv` is the initial candidate version. It does not map `SKU-999`.
- `product_catalog_approved_v2.csv` is the later approved version for Part B and includes the documented product mapping.
- `customer_catalog.csv` maps `customer_id` to customer name and segment.
- `store_catalog.csv` maps `store_code` to store name and region.

All source records are fictional and contain no personal or confidential information. Do not change the supplied inputs. If you discover a source defect, preserve it as evidence and report it.

## Grain and reporting definitions

- Source grain: one source CSV row is one order line.
- Fact grain: one warehouse fact row is one completed order line.
- Completed order count: count distinct `order_id` values after filtering to completed rows.
- Completed line count: count fact rows or distinct `line_id` values.
- Units sold: sum `quantity` over completed rows.
- Net sales: sum line-level net sales over the explicitly stated scope.
- Average order value: completed net sales divided by distinct completed `order_id` count.
