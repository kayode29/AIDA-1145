# AIDA 1145 — Week 11 Graded Lab 7: Service Hours Recovery

## Part B — Implementation, Test Evidence, and Final Decision

### 1. Objective

The purpose of this pipeline is to process service-hour batch records safely and determine whether the records are reliable enough to publish.

The pipeline validates the input data, identifies duplicate deliveries and revised records, detects exceptions and conflicts, reconciles row counts, checks release conditions, and publishes reports only when all required release gates pass.

The implementation uses Python's standard library.

### 2. Initial batch result

The original input file was `data/service_batches.csv`.

The pipeline processed 8 input rows and produced the following classifications:

| Classification | Count |
|---|---:|
| Selected | 5 |
| Superseded | 1 |
| Retransmitted | 1 |
| Exceptions | 1 |
| Total | 8 |

The initial batch decision was **HOLD**.

The invalid negative-hours record caused the exception gate to fail. The ticket-count requirement also did not pass because the expected six distinct tickets were not available as valid selected records.

The initial run evidence is stored in:

- `runs/initial/summary.json`
- `runs/initial/row_classifications.csv`

### 3. Corrected batch result

The corrected input file was `data/corrections.csv`.

The correction changed ticket T206 to a valid one-hour record at revision 2.

The corrected pipeline run processed 8 input rows:

| Classification | Count |
|---|---:|
| Selected | 6 |
| Superseded | 1 |
| Retransmitted | 1 |
| Exceptions | 0 |
| Total | 8 |

The corrected batch decision was **RELEASE**.

All required release gates passed, including schema validation, handoff completion, zero exceptions, zero conflicts, expected ticket count, expected branch coverage, and row reconciliation.

### 4. Published branch totals

The released report contains the following branch totals:

| Branch | Total hours |
|---|---:|
| East | 5 |
| North | 4 |
| West | 5 |
| **Grand total** | **14** |

The six selected records are:

| Ticket | Branch | Hours | Revision |
|---|---|---:|---:|
| T201 | East | 2 | 1 |
| T202 | West | 3 | 1 |
| T203 | East | 2 | 2 |
| T204 | North | 4 | 1 |
| T205 | West | 2 | 1 |
| T206 | East | 1 | 2 |

The published files are:

- `release/report.csv`
- `release/selected_records.csv`
- `release/release_metadata.json`

### 5. Rerun and reproducibility test

The corrected input was processed a second time using a separate run folder.

Both corrected runs produced the same published report and selected-record output.

SHA-256 comparison results:

| File | Result |
|---|---|
| Published report snapshots | Identical |
| Selected-record snapshots | Identical |

The matching hashes demonstrate that rerunning the same corrected input produced identical output files.

Evidence is stored in:

- `runs/corrected-1/`
- `runs/corrected-2/`

### 6. Negative test results

#### Missing-column test

A test CSV without the required `revision` column was processed.

The pipeline returned **HOLD** and identified the schema error. It did not publish a new release.

Evidence:

- `tests/missing_column.csv`
- `runs/test-missing-column-fixed-3/summary.json`
- `runs/test-missing-column-fixed-3/row_classifications.csv`

#### Same-revision conflict test

A test file containing two different values for the same ticket and revision was processed.

The pipeline returned **HOLD**. The conflicting records were classified as exceptions, and the conflict gate failed.

Evidence:

- `tests/same_revision_conflict.csv`
- `runs/test-conflict/summary.json`
- `runs/test-conflict/row_classifications.csv`

### 7. Protection of the previous release

Before running the negative tests, the SHA-256 hash of the published report was recorded.

After the missing-column and conflict tests, the report hash was checked again.

The before-and-after hashes matched. The PowerShell comparison returned `True`.

The release metadata still identified `corrected-2` as the successful release.

This confirms that failed test runs did not overwrite the previously published report or selected records.

### 8. Row reconciliation

The pipeline accounts for every input row.

Initial batch:

5 selected + 1 superseded + 1 retransmitted + 1 exception = 8 input rows.

Corrected batch:

6 selected + 1 superseded + 1 retransmitted + 0 exceptions = 8 input rows.

Both totals reconcile correctly.

### 9. Final decision

The original batch was correctly placed on **HOLD** because it contained an invalid negative-hours record.

After the correction, the pipeline successfully validated all six expected tickets and all three expected branches. The corrected batch passed every release gate and was approved for **RELEASE**.

The rerun produced identical output hashes, and the negative tests demonstrated that missing required columns and same-revision conflicts prevent release. The previous published release remained unchanged after those failed tests.

**Final recommendation: RELEASE the corrected service-hours batch.**

The pipeline provides validation, traceable classifications, reproducible outputs, and protection against failed runs overwriting a successful release.

