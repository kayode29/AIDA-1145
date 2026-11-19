# Practice Lab 8: Can the sales model support the report?

**AIDA 1145 · fully worked, ungraded practice · analytical models and pipeline checks**

A regional retailer wants a category-level sales report for its November planning meeting. One product changed category during the month. The transaction feed also contains a retransmitted order line. A join can run successfully and still produce the wrong answer: if two category records match the same line, the line—and its revenue—can be counted twice.

Your job is to inspect two attempts, explain why the first is held, and verify why the second is suitable for this specific report. The code is complete; the thinking matters. Run it, inspect the evidence, and follow the reasoning below.

## What you will produce and learn

You will create a held-run summary and join diagnostics, a passing-run summary, a fact table, and a category report. You will explain the fact grain, distinguish retransmitted lines from multiple lines in one order, interpret date-effective reference data, reconcile revenue, and write a short release decision. Practice is ungraded; retain the evidence for your own review.

## Before you start

Use Python 3.10 or later; SQLite comes with Python. No package installation, credentials, database server, or network access is needed. Open a terminal **inside this practice folder**. On Windows, use `py` instead of `python` if that is how Python is installed. The supplied data is fictional.

| File | Role |
|---|---|
| `data/order_lines.csv` | Event data: one intended business event per `line_id`; identical repeated rows are retransmissions. |
| `data/catalog_candidate.csv` | The first reference version, with overlapping dates. |
| `data/catalog_corrected.csv` | A source-owner correction defining non-overlapping effective dates. |
| `pipeline.py` | Complete Python and SQLite workflow, including checks and report generation. |
| `expected/` | Reference outputs for comparison; hashes and path separators can differ across operating systems. |

Each attempt writes to a **new** output directory and will refuse to overwrite one. If you have already used a directory name, choose a new one; do not delete another student's or a previous run's evidence.

## 1. Decide what a fact row represents

The fact grain is **one distinct completed order line**. `line_id` identifies that line; `order_id` identifies the order, which can have more than one line. Here O01 legitimately has two different lines, L01 and L02. L02 appears twice with identical values because the source retransmitted it. Retain one copy and account for the extra row as a replay. If the same line ID arrives with different values, the workflow holds the batch instead of guessing which version is correct.

The input row equation is:

```text
input rows = canonical lines + identical replays + source-error rows
           = 5 + 1 + 0 = 6
```

That equation checks row accounting. It does not prove that the original source is complete or that a value is factually true. The source is a snapshot for this exercise; no external expected-order manifest is supplied.

For each distinct order line:

```text
net_cents = quantity × unit_cents
```

For example, L03 is two units at 1,500 cents each: `2 × 1,500 = 3,000 cents`. This case has no discounts, tax, or returns. Integer cents avoid floating-point rounding for these calculations. The sum of canonical line amounts is 7,900 cents. This is a diagnostic source total until the model and reference checks pass.

## 2. Understand effective dates before joining

A catalog row is valid from `valid_from` **inclusive** until `valid_to` **exclusive**. This is a half-open interval:

```text
valid_from <= sale_date < valid_to
```

Under the candidate catalog, P2 is Essentials from November 1 through the day before November 15, and Accessories from November 10 onward. The periods overlap from November 10–14. L03, dated November 12, matches **both** P2 rows. L02, dated November 3, matches only Essentials.

A plain join on `product_id` alone is even less reliable: it matches P2 to both historical versions regardless of date. A date condition reduces the candidate matches, but still cannot choose a category when intervals overlap. Never hide this by choosing the first row or by using `DISTINCT` after summing.

## 3. Run the candidate catalog and inspect the HOLD

```bash
python pipeline.py data/order_lines.csv data/catalog_candidate.csv runs/candidate
```

Open `runs/candidate/summary.json` and `runs/candidate/join_diagnostics.csv`. Expected evidence:

- Six input rows; five canonical lines; one replay; no source-error rows.
- Source total: **7,900 cents**.
- L03 has **2** matching catalog rows; every other line has **1**.
- `ambiguous_lines` is **1**, `unmatched_lines` is **0**, and status is **HOLD**.
- No `fact_sales.csv` or `category_report.csv` is released for this attempt.

If L03 were joined twice and then summed, its extra 3,000 cents would inflate the total to **10,900 cents**. That is a diagnosis of the naive result, not a report produced by the held run. The program groups join matches by line ID **before** building the fact table and requires exactly one match for every canonical line.

## 4. Apply the source-owner correction and rerun

The source owner confirms that P2 changed category on November 10. The corrected catalog ends Essentials on November 10 and starts Accessories on that same date. Because the end is exclusive, those intervals meet without overlap. Keep the original attempt and use a separate folder:

```bash
python pipeline.py data/order_lines.csv data/catalog_corrected.csv runs/corrected
```

Open the three outputs in `runs/corrected/`. Every line has one match; status is **PASS**. The fact table contains five rows and the category report contains:

| Category | Lines | Units | Net cents |
|---|---:|---:|---:|
| Accessories | 1 | 2 | 3,000 |
| Essentials | 1 | 1 | 1,500 |
| Hardware | 2 | 3 | 3,000 |
| Service | 1 | 1 | 400 |
| **Total** | **5** | **7** | **7,900** |

The model has **four distinct orders**, not five: O01 contains two lines. For this dataset the average completed order value is `7,900 / 4 = 1,975 cents` ($19.75). Dividing by five lines answers a different question. The program reports the distinct-order count; this average is calculated here for interpretation.

## 5. Follow the SQL and verify the gate

Open `pipeline.py` and trace these stages:

1. Validate fields and separate canonical lines, identical replays, and source errors. A conflicting ID or invalid field causes a hold.
2. Load canonical rows and the selected reference into an in-memory SQLite database. The canonical `line_id` is the fact grain.
3. Use a **left join** with the effective-date condition and `COUNT(c.product_id)` per source line. A left join retains unmatched lines with a count of zero; an inner join could silently drop them.
4. Require exactly one reference match per canonical line. If any has zero or multiple matches, save diagnostics and hold.
5. Only then create the fact table and category aggregation. Confirm the fact row count equals canonical lines and the category total equals source cents before returning `PASS`.

The summary stores SHA-256 hashes of each input, so you can tell which bytes were used. A hash is not proof that a source value is correct. The workflow uses a new output folder for each attempt and does not append duplicate facts on a rerun. It is a classroom batch, not an automated scheduler or a concurrent publishing service.

## 6. Test your understanding

Rerun the corrected command with a new folder such as `runs/repeat`; compare fact rows, totals, and source hashes. Then copy the corrected catalog, change P3's start to `2026-11-13`, and run the copy into `runs/missing-reference`. L04 has **zero** matches on November 12; the batch must be held. Keep the supplied catalog unchanged. A missing reference is not the same as a zero-value sale.

For a boundary check, note that a P2 sale on November 10 matches the Accessories row in the corrected catalog, not Essentials. No supplied P2 transaction occurs on that boundary, so this is a reasoning check; add a separate test row in a copy if you want to demonstrate it.

## Deliverables and model decision

Keep the candidate and corrected summaries, both diagnostic files, the passing fact table and report, and the repeat and missing-reference evidence for your review. Write a short note addressing (1) the fact grain and replay, (2) the overlap and its financial effect, (3) why the corrected output passes, and (4) one limitation.

**Example decision:** Hold the candidate catalog because L03 matches two category versions; aggregating it twice could add 3,000 cents to the 7,900-cent source amount. After the source-owner date correction, all five canonical lines have one match, the report reconciles to 7,900 cents, and four distinct orders are represented. Release the corrected report for this case, subject to source completeness and the stated no-tax/no-return scope.

## Troubleshooting

If Python is not recognized, try `py --version`. If a path is missing, confirm the terminal is in this folder and copy the command exactly. If the output folder already exists, choose a new name. If the summary says a column is missing or a reference is ambiguous, inspect that input and the saved diagnostics; do not silently alter the original file. For a separate graded lab, use your assigned private course repository, not the instructor repository.
