# Test plan and run evidence

| Check | What could go wrong? | What should your code do? | Evidence / observed result | Pass? |
|---|---|---|---|---|
| Required CSV columns | A required column is missing. | Detect missing required headers and stop processing. | Supplied source and catalogue CSV headers were inspected and matched the expected columns. Both pipeline runs completed. | PASS for supplied files |
| Blank or duplicate `line_id` | A line ID is missing or repeated. | Reject or flag invalid IDs and prevent duplicate fact IDs. | Unit test `test_duplicate_line_id_is_detected` passed. A separate blank-ID test was not recorded. | PARTIAL |
| Status scope | CANCELLED or PENDING records enter the fact table. | Include only COMPLETED records in the fact table. | Both runs: 12 input rows, 10 completed, 1 cancelled, 1 pending, and 10 fact rows. | PASS |
| Repeated `order_id` with different lines | Different lines from one order are incorrectly removed. | Keep each completed order line as a separate fact row. | 10 completed lines and 8 distinct completed orders. | PASS |
| Invalid quantity, price, or discount | Invalid sales values produce incorrect amounts. | Validate quantity, price, and discount before calculating sales. | Unit tests cover zero/negative quantity, negative price, discount above one, negative discount, and nonnumeric quantity. 21 tests passed. | PASS |
| Candidate product code with no match | A product SKU is missing from the candidate catalogue. | Use unknown product key 0, record an exception, and hold the release. | Candidate run: SKU-999 unresolved, 1 exception, release status HOLD. | PASS |
| Duplicate product business key | Duplicate SKUs create ambiguous product matches. | Detect duplicate product business keys and prevent an invalid release. | No separate duplicate-product-key test result was recorded. | NOT TESTED |
| Fact grain and unique line count | Fact rows do not represent one completed order line each. | Create one fact row per completed order line with unique line IDs. | Both runs produced 10 fact rows from 10 completed source lines. Unit tests passed. | PASS |
| Dimension key coverage / foreign keys | A fact row refers to a missing dimension key. | Ensure every fact foreign key resolves to a dimension record. | Approved-v2 run: foreign_keys_resolve was true. All validation checks passed. | PASS |
| Gross, discount, and net cents | Monetary calculations or rounding produce incorrect totals. | Store money as integer cents and ensure net equals gross less discount. | Both runs: gross 57,985 cents; discount 4,955 cents; net 53,030 cents. Rounding unit tests passed. | PASS |
| Source-to-fact row and amount controls | Fact rows or monetary totals do not reconcile with the source. | Reconcile completed source rows and sales amounts against the fact table. | Both runs produced 10 fact rows. Net sales were 53,030 cents in both runs. | PASS for recorded controls |
| Distinct order count and average order value | Orders are counted by line instead of by distinct order. | Count distinct completed orders and calculate average order value. | 8 distinct completed orders; net sales 53,030 cents; average order value 6,628.75 cents. | PASS |
| Repeated run / idempotency | Repeated execution changes results or creates duplicate records. | Produce consistent results when the same catalogue is run again. | Approved-v2 was run again and returned ACCEPT, 10 fact rows, and 0 exceptions. Unit tests: 21 passed. | PASS |

## Run record

| Catalogue version | Command | Python version | Output folder | Run status | Notes |
|---|---|---|---|---|---|
| Candidate | `py .\src\starter_pipeline.py --catalogue candidate` | Python 3.14.7 | `outputs\candidate` | HOLD | 10 fact rows; 1 unresolved SKU-999; 1 exception. |
| Approved v2 | `py .\src\starter_pipeline.py --catalogue approved-v2` | Python 3.14.7 | `outputs\approved-v2` | ACCEPT | 10 fact rows; 0 exceptions; all validation checks passed. |
| Approved v2 repeat run | `py .\src\starter_pipeline.py --catalogue approved-v2` | Python 3.14.7 | `outputs\approved-v2` | ACCEPT | Repeat run produced 10 fact rows and 0 exceptions. |

