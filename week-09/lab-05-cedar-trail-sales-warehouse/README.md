# AIDA 1145 — Week 9 Graded Lab 5: Cedar Trail Sales Warehouse

**Week 9 topic:** Data warehouses and analytical models  
**Assessment:** Graded Lab 5 — one lab worth 5% of the course grade  
**Part A:** Guided dimensional-modeling challenge — 3%  
**Part B:** Independent production extension — 2%  
**Submission:** One completed lab folder in your assigned private course repository and one D2L submission  
**Deadline:** Use the deadline shown in the D2L assignment.

## What you are building

Cedar Trail Outdoor Co-op sells outdoor equipment through three stores. Managers want a trustworthy report of completed sales by month, product category, and store region. They also want the average net value of a completed order.

You will turn order-line CSV data and small reference files into a star-schema-style sales model. You will define what one fact row means, build dimensions and a fact table, calculate sales measures, write analysis queries, and check whether the source and warehouse agree.

This is a **graded starter**. The data and code scaffold are provided; you must complete the model, code, checks, and decision. There is no completed solution in this folder.

## How the parts fit together

Part A creates and inspects a candidate warehouse using the initial product catalogue. Part B responds to a documented catalogue update, reruns the process, and evaluates whether the corrected model is ready for the requested reports. The parts use the same business case and stay together in this one Lab 5 folder. They are not separate submissions.

The source data include completed, cancelled, and pending order lines. One completed line has a product code that is missing from the initial product catalogue. The data package also includes a later, approved catalogue version and a release note. Your pipeline must make the missing mapping visible, preserve the sales line and its amount, and use the approved version only in Part B.

## Learning goals

By completing the lab, you will demonstrate that you can:

- state the grain of a fact table in plain business language;
- separate measurable business events from descriptive dimensions;
- select and use keys to join facts to dimensions;
- calculate gross sales, discount, and net sales without losing cents;
- distinguish sales-line count, order count, and unit count;
- aggregate amounts and averages at the right level;
- identify a missing dimension match without silently dropping a fact;
- validate row counts, distinct identifiers, joins, and control totals;
- rerun a small pipeline reproducibly and explain its release decision.

## Files supplied

| Path | What it contains |
|---|---|
| `data/order_lines.csv` | Sales order lines, including completed, cancelled, and pending statuses. |
| `data/product_catalog_candidate.csv` | Initial product reference file. It is intentionally incomplete for one completed line. |
| `data/product_catalog_approved_v2.csv` | Later product catalogue version for the independent extension. |
| `data/product_catalog_release_note.md` | Business context and version information for the updated catalogue. |
| `data/customer_catalog.csv` | Customer names and customer segments. |
| `data/store_catalog.csv` | Store names and regions. |
| `data/data_dictionary.md` | Field meanings, scope rules, and data assumptions. |
| `src/starter_pipeline.py` | Python scaffold with clearly marked TODO sections. |
| `docs/design_record.md` | Questions to answer before and while building the model. |
| `docs/test_plan.md` | A place to record the checks you design and perform. |
| `docs/decision_note.md` | A template for your evidence-based recommendation. |
| `sql/` | Save your completed schema and analysis queries here. |
| `outputs/README.md` | Required generated evidence and suggested file names. |

## Tools and setup

Use **Python 3.10 or later** and its built-in `csv`, `sqlite3`, `decimal`, and `unittest` modules. You do not need to install a package, connect to a database server, or use a cloud service.

1. Install or open a supported Python environment already used in this course.
2. Open a terminal in this `lab-05-cedar-trail-sales-warehouse` folder.
3. Check the Python version:

   ```text
   python --version
   ```

4. Complete the TODO sections in `src/starter_pipeline.py` and create the SQL files described below.
5. Run the pipeline from this folder so its relative data and output paths resolve correctly.

If your computer uses `py` to start Python, use `py -3` instead of `python` in the commands. If a command fails, read the full error message, confirm that your terminal is in the lab folder, and check the file name and path before changing code.

## Business rules you must follow

1. **Scope:** Only rows whose status is `COMPLETED` contribute to completed-sales reports. Keep cancelled and pending rows visible in your row ledger, but do not include them in completed-sales revenue or completed-order counts.
2. **Grain:** One accepted sales fact row represents one product line on one completed order. An order can therefore have more than one fact row.
3. **Identifiers:** `line_id` identifies an individual order line. `order_id` identifies an order and may repeat across lines.
4. **Product mapping:** Match each sale to a product using `sku`. Do not use product names as join keys and do not guess a missing mapping.
5. **Missing product in Part A:** Preserve the completed line in the candidate fact output with a clearly identified unknown product member (for example, key `0`). Write the unmatched source values to an exception output. Do not silently delete the row or invent a category.
6. **Part B catalogue:** Use the approved version named in `product_catalog_release_note.md`. Keep the candidate and approved runs distinguishable in your outputs and decision note.
7. **Money:** The source uses integer cents. Keep calculations in cents until you format a result for a person to read.
8. **Decision:** Recommend `HOLD` if a required report would hide or misclassify an unresolved product mapping, duplicated key, invalid source value, or other failed check. Recommend `ACCEPT` only when the required checks pass for the named input version and batch. State the evidence and scope of your recommendation.

## Formulas and a small example

The discount rate is a decimal fraction: `0.10` means 10%.

```text
gross_cents    = quantity × unit_price_cents
discount_cents = round_half_up(gross_cents × discount_rate)
net_cents      = gross_cents − discount_cents
```

For example, 3 items at 2,500 cents each have gross sales of 7,500 cents. With a 10% discount, the discount is 750 cents and net sales are 6,750 cents ($67.50). Use the same documented cent-rounding rule every time.

For completed orders:

```text
average_order_value_cents = total_net_sales_cents ÷ distinct_completed_order_count
```

Do not divide by the number of fact rows: an order may contain multiple lines. Also keep these counts separate:

- fact rows count sales lines;
- distinct `order_id` values count orders;
- the sum of `quantity` counts units.

## Part A — Guided dimensional-modeling challenge (3%)

Complete Part A in the scheduled class activity. Read each step before coding. Save all work in this lab folder.

### Step 1 — Inspect the business request and files

1. Read `data/data_dictionary.md` and the headers in all CSV files.
2. Open `data/order_lines.csv`. Find examples of completed, cancelled, and pending rows.
3. Find an order ID that appears on more than one row. Explain why those rows are separate order lines rather than duplicate orders.
4. Compare every `sku` in the completed order lines with `product_catalog_candidate.csv`.
5. Record your observations in `docs/design_record.md`. Do not edit the supplied CSV files.

### Step 2 — Write the model plan before building it

Complete `docs/design_record.md` before relying on a report. In your own words, write:

- the fact-table grain;
- which source field identifies a line and which identifies an order;
- the measures you need and their units;
- the dimensions needed for month, product category, customer segment, and store region;
- the key used to join each source record to its dimension;
- how you will preserve and report a missing product match;
- what evidence would make the candidate output safe or unsafe to publish.

Use `docs/test_plan.md` to plan at least one normal check and one failure check for source scope, duplicate line identifiers, missing product matches, money calculations, fact-row counts, and report totals.

### Step 3 — Design the star schema

Create `sql/schema.sql`. Include:

- a date dimension;
- a product dimension;
- a customer dimension;
- a store dimension;
- a sales fact table that references the dimensions and stores line-level measures.

Use integer primary keys for warehouse dimension keys. Keep the source identifiers (such as `sku`, `customer_id`, and `store_code`) as unique business-key columns in their dimensions. Use foreign keys from the fact table to the dimensions. Add reasonable `NOT NULL`, `UNIQUE`, and non-negative-value checks where they protect the business rules.

Before you run SQL, sketch the relationships in `docs/design_record.md`. Many sales facts can reference one product, one customer, one store, and one date. A dimension key must not match multiple dimension rows in the same version.

### Step 4 — Complete the Python transformation

Complete the TODOs in `src/starter_pipeline.py`. Use small functions that each do one clear job. Your pipeline should:

1. read the supplied CSV files without changing them;
2. validate required columns and source values;
3. count rows by status and select completed rows for the sales facts;
4. create or load the dimensions and retain a mapping from each business key to its warehouse key;
5. calculate line gross, discount, and net sales in integer cents;
6. preserve a completed line with an unknown product key and record the unmatched SKU in an exception file;
7. load the fact rows into SQLite using the schema in `sql/schema.sql`;
8. write the evidence files listed in `outputs/README.md`.

Add comments where a business rule is being applied. A comment should explain why a row is in scope, why an unknown key is retained, or why a measure is calculated at the line grain.

### Step 5 — Write the analysis queries

Create and save these SQL queries under `sql/`:

1. `sales_by_month_category.sql` — net sales and units by calendar month and product category.
2. `sales_by_region.sql` — net sales and distinct completed orders by store region.
3. `order_value_summary.sql` — total net sales, distinct completed orders, and average order value.

Use joins through the dimension keys. Make the query scope explicit. Label an unknown product category clearly in the candidate report so it cannot be mistaken for a known category.

### Step 6 — Reconcile the candidate run

From the lab folder, run the candidate version:

```text
python src/starter_pipeline.py --catalogue candidate
```

The starter will not run successfully until you complete its TODO sections. After it runs, inspect the generated files in `outputs/candidate/`. Keep this run and its exceptions even if the result is `HOLD`.

For the candidate catalogue, compare the source and warehouse at the same scope. Record:

- source rows by status;
- completed source line count and distinct completed order count;
- candidate fact row count and distinct line count;
- unmatched completed lines and their source business keys;
- quantity, gross, discount, and net totals before and after loading;
- whether the category and region report totals reconcile to the completed-line total.

If a report differs, trace the difference. Check status filters, duplicated source identifiers, dimension-key uniqueness, unmatched keys, join row counts, formula order, and cent rounding. Do not manually alter a total to make it match.

### Step 7 — Write the candidate decision

Complete a candidate-run section in `docs/decision_note.md`. Choose `HOLD` or `ACCEPT` based on the documented rules and evidence. Explain what the candidate can and cannot support. An unknown product category must not disappear from a report or be described as a known category.

## Part B — Independent production extension (2%)

Use the later approved catalogue version to respond to the business change. Do not change the Part A candidate files or erase its evidence.

### Step 8 — Load the approved catalogue release

1. Read `data/product_catalog_release_note.md`.
2. Add a command-line option or a clearly documented setting that selects either the candidate catalogue or the approved version.
3. Run the pipeline with the approved catalogue from the lab folder:

   ```text
   python src/starter_pipeline.py --catalogue approved-v2
   ```

   The scaffold already provides this command-line option; retain it or clearly document an equivalent. Keep the output in the separate `outputs/approved-v2/` folder so it cannot overwrite the candidate evidence.
4. Confirm that each completed sales line still appears once in the fact table and that each product business key resolves to one dimension row.
5. Do not treat “the file is called approved” as the only quality check. Validate its headers, unique SKU keys, required values, and completed-line coverage.

### Step 9 — Add production-quality checks

Write and run your own tests in `tests/`. At minimum, test that:

- cancelled and pending lines are excluded from completed-sales facts;
- multiple lines for one order remain separate fact rows;
- distinct order count is not replaced by fact-row count;
- gross, discount, and net amounts use the documented cent rule;
- an unmatched SKU is retained and reported in the candidate run;
- duplicate product keys or duplicate line IDs are detected and cannot produce an `ACCEPT` decision;
- running the approved version twice produces the same business outputs and does not append duplicate facts.

Run your tests from the lab folder with:

```text
python -m unittest discover -s tests -v
```

Create the `tests/` folder and test files yourself. If you use a different test runner, record its installation or setup, exact command, and results in `docs/test_plan.md`.

Record the test names, commands, results, and any remaining limitation in `docs/test_plan.md`. Do not claim that a check passed unless you ran it and kept evidence of the result.

### Step 10 — Make the final recommendation

Complete `docs/decision_note.md` with separate sections for the candidate run and the approved-v2 run. For the final recommendation, state:

- which catalogue version and input batch you evaluated;
- the completed-line, order, and fact-row counts;
- the exception count and disposition;
- the sales control totals and whether they reconcile;
- the checks you ran and their results;
- an `ACCEPT` or `HOLD` recommendation;
- one limitation that remains even if the checks pass.

Your conclusion is about this fictional batch and the stated classroom reports only. Do not claim that a small exercise certifies a real financial warehouse.

## Required submission evidence

Keep all work in this one lab folder. Submit these items as part of the single Lab 5 folder:

- completed `docs/design_record.md`;
- completed `sql/schema.sql` and the three analysis queries;
- completed `src/starter_pipeline.py` (rename it to `src/warehouse_pipeline.py` if you prefer, and update your instructions);
- candidate and approved-v2 run outputs, including an exception report and run summary;
- your tests and completed `docs/test_plan.md`;
- completed `docs/decision_note.md`;
- a short `docs/ai_use_declaration.md` stating whether and how you used generative or automated tools, as required by course expectations.

Suggested generated files are listed in `outputs/README.md`. Keep outputs small and relevant. Do not commit Python cache files, virtual environments, credentials, unrelated data, or personal information.

## Submission workflow — one lab folder, one submission

1. Copy this complete `lab-05-cedar-trail-sales-warehouse` folder from the private instructor **AIDA_1145_Graded_Labs** repository into your assigned private AIDA 1145 student repository.
2. Work only in your copy in your assigned student repository. Keep the folder name and internal structure clear.
3. Make meaningful commits as you complete the model, pipeline, checks, and decision note. Push the completed folder to your assigned private repository.
4. Submit **one link** to your private repository and the commit containing the complete Lab 5 folder in the single D2L Lab 5 assignment.
5. Submit by the D2L deadline. Keep a local backup of your work.

Do not push student work to either instructor repository. Do not create separate D2L submissions for Part A and Part B. Both parts are assessed together as one 5% lab.

## Before you submit

- [ ] My code runs from the lab folder using only the documented Python environment.
- [ ] I stated the grain and used it consistently.
- [ ] I retained all completed sales lines, including the candidate line with no product match.
- [ ] I kept cancelled and pending rows out of completed-sales measures.
- [ ] I used integer cents and a documented rounding rule.
- [ ] My fact count, distinct line count, distinct order count, and unit count have clear labels.
- [ ] My queries do not multiply measures through duplicate dimension matches.
- [ ] I validated the approved-v2 catalogue; I did not assume it passed without checking.
- [ ] My tests and run evidence support the decision I wrote.
- [ ] My folder is in my assigned private student repository, with meaningful commits pushed.
- [ ] I made one D2L submission for the complete Lab 5 folder.

