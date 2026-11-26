# Practice Lab 9: Recover a paginated depot batch

**AIDA 1145 · fully worked, ungraded practice · pipeline design and recovery**

A delivery company collects depot observations from an API and uses them in an 8:00 a.m. planning report. The source returns observations across pages. The team needs to know whether it received the whole batch, whether each expected observation is valid and counted once, and whether a corrected run can be reproduced without quietly replacing earlier evidence.

The pages in this lab are saved JSON files representing API responses. You do **not** need a live API, account, credentials, network connection, or server. The supplied code is complete. Your work is to run and inspect it, trace the logic, and explain the release decision—not just copy the commands.

## Your deliverables

For your own review, retain:

1. The initial held-run summary and row evidence.
2. The corrected summary, row evidence, and depot totals.
3. A second corrected-run summary and totals to demonstrate repeatability.
4. A missing-page or cursor-cycle test input and its held-run evidence.
5. A short decision note explaining the failure, recovery, checks, and one limitation.

Practice is ungraded. Follow the instructor's directions if a practice push is requested. The separate graded lab uses a distinct business case and asks you to design and implement the logic yourself.

## What you need and where to work

Use Python 3.10 or later. The program uses only Python's standard library. If you already have the instructor practice repository, pull its current version and open `week-13/practice-lab-09-batch-recovery`. Otherwise, after accepting your course invitation, clone the private instructor repository and enter this folder:

```bash
git clone https://github.com/stem-ai-studio-classroom/AIDA_1145_Practical_Lab_Examples.git
cd AIDA_1145_Practical_Lab_Examples/week-13/practice-lab-09-batch-recovery
```

If you keep an existing clone, use `git pull` **inside that repository** after checking for your own local changes. Students may pull the instructor material but do not push to the instructor repository. Open a terminal **inside the lab folder** for the commands below. On Windows, substitute `py` for `python` if needed. All data is fictional.

| File | Purpose |
|---|---|
| `data/manifest.json` | Batch ID, first cursor, expected page IDs, expected event IDs, and reporting cutoff. |
| `data/initial/page1.json`, `page2.json` | The first attempt, including one invalid event and one retransmission. |
| `data/corrected/page1.json`, `page2.json` | A source-owner correction for the same expected batch. |
| `pipeline.py` | Complete runnable solution. |
| `expected/` | Reference run summaries, row evidence, and the passing depot report. Paths and file hashes can vary if line endings or paths differ. |

Each run writes to a **new** output folder and refuses to overwrite an existing one. Keep earlier attempts; use a different folder name if you repeat a command.

## 1. Understand the business contract

The manifest names the two pages expected for this batch and the four expected event IDs. `first_page` is `page1`; each page names the next page, or `null` when the chain ends. Every page must identify the same batch and its own page ID. The workflow follows the chain and checks the **set of visited pages**, rather than assuming that one successful page contains everything.

Each valid event has a nonempty ID and depot, a non-negative integer `units`, and an observation timestamp at or before the manifest cutoff. Timestamps use UTC, for example `2026-11-25T07:30:00Z`. This case has one observation per expected ID. A later byte-for-byte equivalent event is a retransmission; a different event with an already accepted ID is a conflict and causes a hold. Invalid rows are recorded rather than silently repaired.

The row ledger is:

```text
input rows = accepted distinct events + identical replays + error rows
```

The batch is released only when the expected page set is present, every expected event is accepted, there are no unexpected events or errors, and the row ledger reconciles. A `HOLD` produces evidence but **no depot report**. An event-ID set check is stronger than comparing only counts: a missing ID and an unexpected ID can offset one another numerically.

## 2. Inspect and run the first attempt

Open the manifest and both files in `data/initial/`. `page1` points to `page2`. The event A102 occurs on both pages with the same values. A104 has a negative unit count, which violates the contract.

```bash
python pipeline.py data/manifest.json data/initial runs/initial
```

Open `runs/initial/summary.json` and `runs/initial/row_evidence.csv`. You should see two visited pages and five input rows: three accepted events, one identical replay, and one error. A104 appears in the manifest but is not accepted, so the summary lists it as missing from the **accepted event set**. The run is `HOLD`; `depot_totals.csv` is absent.

```text
5 input rows = 3 accepted + 1 replay + 1 error
```

The page chain is complete, but the business batch is not ready. Do not add the invalid `-2` to the report or replace it with `2` without a source correction. The ledger accounts for every received row; it does not establish that accepted source values reflect real-world truth.

## 3. Recover with the corrected source version

The source owner supplies the files under `data/corrected/`. A104 now reports two units. Preserve the initial output and run the corrected files into a different folder:

```bash
python pipeline.py data/manifest.json data/corrected runs/recovered
```

The expected result is five input rows, four accepted events, one replay, no errors, and `PASS`. The report contains North **8**, South **4**, and West **2** units, for **14 units** overall. A102 contributes four units **once**, although it appeared on two pages. Compare the page hashes and input paths in the two summaries: the second page changed, while the first did not. A hash identifies file bytes; it does not authenticate the source or prove its contents are correct.

## 4. Demonstrate a repeatable run

```bash
python pipeline.py data/manifest.json data/corrected runs/repeat
```

Compare `runs/recovered/depot_totals.csv` and `runs/repeat/depot_totals.csv`, their accepted counts, and the page hashes. They should agree. The program creates a new output folder and writes a complete report there; it does not append the batch to a prior report. This demonstrates a repeatable local batch for identical inputs, not a guarantee about concurrent processes or an external API's behavior.

## 5. Trace the stages and their dependencies

Read `pipeline.py` alongside this flow:

```text
manifest → follow and validate page chain → validate/classify rows
         → compare visited pages and accepted IDs with manifest
         → reconcile row ledger → HOLD or depot totals
```

1. The program validates the manifest and follows its first cursor. It records visited pages and a hash for each page read. It checks each page's batch and page identity.
2. Page cursors are limited to names such as `page1`. The workflow detects repeated cursors and unexpected page IDs, rather than looping indefinitely or following an arbitrary file path.
3. Each row is accepted, marked as a replay, or marked as an error. The first **valid accepted** event establishes an ID. A later identical event is a replay; a different one is a conflict. An invalid row is an error even if another row for the ID is later valid.
4. It compares the accepted IDs with the expected IDs and reconciles the row ledger. Successful file parsing alone does not authorize release.
5. Only a passing run writes `depot_totals.csv`. A missing or malformed page causes a held summary and preserves the row evidence collected before the failure. A held run does not release a partial report.

The example reads each page into memory and is appropriate for this small case. For a larger workload, consider bounded page-by-page processing, checkpointing, and failure-safe publication based on the actual scale and latency needs. This demonstration does not implement retries against a network, a transactional publisher, concurrent-writer locking, or persistent checkpoints. Do not claim it does.

## 6. Run a failure test

Make a copy of the `data/corrected` folder named, for example, `test-missing-page`, and remove `page2.json` **from that copy only**. Leave the supplied files unchanged. Run:

```bash
python pipeline.py data/manifest.json test-missing-page runs/missing-page
```

The run holds with a file-read failure and no depot totals. Inspect its summary and the row evidence collected from page 1. The program returns after writing the held summary; inspect `status` and `failures`, not only the process exit code, to determine whether the report passed. Alternatively, in a separate copy, change page 2's `next_page` to `page1`. A cycle must hold the run. The page-chain failure summary may not contain final row counts because the chain did not finish; use the saved row evidence to inspect the partial attempt.

## 7. Write the decision note

In your own words, answer these questions:

- Why did receiving both pages not make the initial batch fit for release?
- Which evidence shows that the correction was processed and A102 was not counted twice?
- Which comparisons support repeatability, and what do they **not** prove?
- What should an operator do when a page is missing or a cursor cycles?

**Model note:** Hold the initial batch: A104 fails the non-negative units rule, even though both pages were read. The corrected input has four accepted expected IDs, one replay, no errors, and 14 total units. A repeat with the same inputs gives the same report and hashes. If a page is missing, retain the held evidence, obtain the missing or corrected source, and rerun under a new attempt. The example does not prove that the source values are true or that a production retry is concurrency-safe.

## Troubleshooting

If Python is not recognized, try `py --version`. If a file is not found, check the current folder and the paths in your command. If an output folder already exists, choose a new name. If the summary says a cursor is invalid or a page is missing, inspect the manifest and page chain in a **copy** of the files. Do not push student work to the instructor repositories.
