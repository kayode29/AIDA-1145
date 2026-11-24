# Decision note - Cedar Trail sales warehouse

## Candidate catalogue run

- Catalogue file and run identifier: `data/product_catalog_candidate.csv`; command: `py .\src\starter_pipeline.py --catalogue candidate`.
- Source row count by status: 12 input rows: 10 COMPLETED, 1 CANCELLED, 1 PENDING, and 0 other-status rows.
- Completed line count and distinct completed order count: 10 completed lines and 8 distinct completed orders.
- Candidate fact-row count and distinct `line_id` count: 10 fact rows and 10 distinct line IDs.
- Unmatched or invalid rows: 1 unmatched product mapping. Line `L1005-01` uses SKU-999, which is missing from the candidate catalogue. The pipeline uses unknown product key 0 and records an exception.
- Gross, discount, and net sales control totals (integer cents): Gross = 57,985 cents; discount = 4,955 cents; net = 53,030 cents.
- Dimension-key and join checks: Fact dimension keys resolve, including unknown product key 0. However, product mapping completeness fails because one completed sales line has no approved product match.
- Candidate decision (`ACCEPT` or `HOLD`): HOLD.
- Evidence supporting the decision: The candidate run produced 10 fact rows and 1 exception. The `no_unresolved_product_mappings` validation check was false. The unresolved SKU requires investigation before release.

## Approved-v2 run

- Catalogue file and run identifier: `data/product_catalog_approved_v2.csv`; command: `py .\src\starter_pipeline.py --catalogue approved-v2`.
- Validation checks performed: Unique fact line IDs, completed source-to-fact row counts, unique dimension keys, foreign-key resolution, non-negative monetary values, net sales calculation, and product mapping completeness.
- Completed line count, fact-row count, and distinct completed order count: 10 completed lines, 10 fact rows, and 8 distinct completed orders.
- Exception count and disposition: 0 exceptions. SKU-999 is included in the approved-v2 product catalogue and maps to a valid product dimension key.
- Gross, discount, and net sales control totals (integer cents): Gross = 57,985 cents; discount = 4,955 cents; net = 53,030 cents.
- Query/report checks: The pipeline generated the SQL-based sales reports. Average order value is 6,628.75 cents, based on 8 distinct completed orders.
- Final decision (`ACCEPT` or `HOLD`): ACCEPT.
- Evidence supporting the decision: The approved-v2 run produced 10 fact rows and 0 exceptions. All validation checks passed, including product mapping completeness and foreign-key resolution. The run summary reported ACCEPT.

## Reproducibility and limitation

- What happened when you reran the approved-v2 pipeline? The repeat run again returned ACCEPT, produced 10 fact rows, and recorded 0 exceptions. The unit test suite ran successfully with 21 tests passing and 0 failures.
- What limitation remains even if the required checks pass? Passing the checks confirms that this sample dataset satisfies the implemented rules. It does not prove that every real-world sales record is complete, accurate, authorized, or suitable for business reporting. Business assumptions such as discount rules and catalogue approval still need confirmation.
- What would you ask the business owner before using a real sales dataset? I would ask the business owner to confirm the meaning of each order status, the approved product catalogue and SKU mappings, discount and rounding rules, how returns and refunds should be handled, and who is authorized to approve a warehouse release.
