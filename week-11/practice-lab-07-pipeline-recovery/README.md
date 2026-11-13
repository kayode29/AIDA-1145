# Practice Lab 7: Find, explain, and recover a failed pipeline

**Worked practice · ungraded · AIDA 1145**

A regional delivery team uses a daily file to report units by location. A dashboard is about to use the totals, but the latest batch contains suspicious records. Your job is to see why the pipeline holds the report, then use a corrected source and confirm that the recovery is repeatable. This example is fully worked: run it, inspect it, and explain what happened.

## What you will practise

- Identify the source and follow the order: read → validate → separate rows → reconcile → release or hold.
- Interpret a run summary and rejected-row evidence rather than assuming that a completed program means trustworthy output.
- Recover from source errors and verify that rerunning does not append duplicates.

## What you need

Python 3 and a terminal. No additional packages, database, API key, or network connection are required. Open a terminal in this folder. On Windows use `py` in place of `python` if needed. The files in `data/` are fictional and are supplied with this exercise.

## 1. Inspect the source and rules

Open `data/initial.csv`. Each row represents one event. `event_id` must be present and unique, `location` must be present, and `units` must be a non-negative integer. The pipeline retains the first occurrence of an ID and rejects later occurrences, even if the first is invalid. That policy is deliberate: an ID conflict needs investigation, not silent replacement. It writes rejected rows with source line numbers and reasons. This exercise uses a strict release gate: **any rejected row holds the report**.

## Understand the operational decision before running

The team promises managers a complete daily location report, not a partial estimate. A successful script process and a usable report therefore answer different questions. The process can finish and still set the release decision to `HOLD` because some records failed the business rules. In a production setting, the team would agree on an acceptable rejection threshold and exception process in advance; for this case it is zero rejects.

Here is the evidence chain. Each stage depends on the preceding stage's result:

```text
source file → schema check → row checks → accepted / rejected
            → row reconciliation → release gate → location totals
```

| Decision point | Evidence | Consequence |
|---|---|---|
| Can we read the expected fields? | The header contains all three required names. | Stop if a required column is absent. |
| Can a row be counted? | ID, location, integer units and duplicate checks. | Accept or reject the row, with reasons. |
| Did we account for the batch? | Input count equals accepted plus rejected. | Investigate if the equation fails. |
| Is the report ready? | Reconciliation holds and no rows were rejected. | Publish totals only on `PASS`. |

The example records a source path, not a cryptographic hash or immutable source version. A path can point to different contents on different days, so it is useful but insufficient on its own for full traceability. In a real system, record a source version or hash, acquisition time, and unique run ID as well.

## 2. Run the initial batch

```bash
python pipeline.py data/initial.csv runs/initial
```

Open `runs/initial/run_summary.json` and `runs/initial/rejected.csv`. Expect 5 input rows, 2 accepted, 3 rejected, 13 accepted units, and `HOLD`. Lines 4, 5, and 6 identify a negative quantity, a missing location, and a duplicate ID. No `published_totals.csv` should exist in this run folder. The accepted total is diagnostic only; it is not the released business total.

The reconciliation check is:

```text
input rows = accepted rows + rejected rows
5 = 2 + 3
```

This accounts for rows; it does **not** prove the accepted values are factually correct. Read `pipeline.py` and locate the validation, reconciliation, and release decision. An assertion catches a programming error if the counts fail to reconcile.

### Follow the logic for individual rows

Open `runs/initial/rejected.csv`. `source_line` refers to the physical CSV line, including the header. The first E102 is accepted, so the second E102 is rejected as a duplicate. E103 fails because its unit count is negative; E104 fails because its location is empty. A row can have more than one reason but is counted only once in the rejected total. These choices matter: adding the number of rejection reasons would not necessarily give you the number of rejected rows.

Why retain the first ID even if it is invalid? This is an explicit conservative policy in the exercise, not a universal cleaning rule. It flags subsequent use of that ID for investigation instead of silently treating a later record as a correction. A different source contract could authorize a timestamp-based correction rule, but the pipeline would need to document and test it.

The summary's acceptance rate is a diagnostic measure:

```text
acceptance rate = accepted rows / input rows × 100
                = 2 / 5 × 100 = 40%
```

A high acceptance rate would not override the zero-rejection gate. For an empty batch, do not divide by zero: investigate whether an empty batch is expected and apply the agreed business rule. This demonstration accepts a valid empty file, so it cannot by itself distinguish an expected empty batch from a missing delivery.

## 3. Recover using a corrected source

The source owner supplied `data/corrected.csv`. It removes the repeated event and corrects the two invalid records. Keep the initial evidence and run the corrected file in a separate folder:

```bash
python pipeline.py data/corrected.csv runs/recovered
```

Expect 4 input rows, 4 accepted, 0 rejected, 19 accepted units, and `PASS`. Open `runs/recovered/published_totals.csv`: North has 10 units, South 5, and West 4. Compare both summaries and explain why the second output is fit for release under the stated rules. A corrected file is an input to a new run, not a quiet overwrite of the original evidence.

## 4. Check repeatability

Run the recovery command again. Confirm that the recovered summary and totals still contain 4 events and 19 units. This implementation replaces run files rather than appending them, so rerunning the same input in the same folder does not double the totals. It is a simple local demonstration; it does not establish safe concurrent writes or protect historical runs if you reuse a folder for different inputs.

Try a negative test in a copy of the source: remove a required column and run against a **new empty** output folder. The program reports the missing column instead of publishing a result. The example does not implement atomic writes or full crash recovery; use a fresh output folder per attempt.

## 5. Read the code as a design review

Open `pipeline.py` and trace these decisions:

1. `csv.DictReader` reads each input record using the header. The required-field check rejects a missing column before row processing; it does not verify that the units in the source have the correct real-world meaning.
2. The loop collects all rule failures for a row. `seen` contains nonempty IDs already encountered. The ID is recorded even when that row has another error, so a later occurrence is flagged.
3. Accepted and rejected lists are written separately. The assertion compares their lengths to the input count. This is a useful development check; production systems should use explicit failure handling rather than depend on assertions that can be disabled.
4. `PASS` requires zero rejects. The location totals are calculated only then. A previous `published_totals.csv` in the same output directory is removed if a later successfully parsed run is held.

**Important boundary:** a schema error occurs before the stale-report removal step. Always use a new empty output folder for each attempt, as the commands above do. Do not treat this example as a safe publisher when a folder is reused after a schema failure or crash. In a production design, validate into an isolated staging area and atomically promote a passing report; capture failure status even when parsing stops. Test those behaviors before relying on them.

## 6. Troubleshoot your run

- **Python is not recognized:** try `py --version` and use `py` in the commands, or select the course-supported Python installation.
- **File not found:** check that your terminal is in this practice folder and that the path matches the command. `data/initial.csv` is relative to that folder.
- **Missing column error:** inspect the header in a copy of the input. Keep the original file and use a new run folder for the next attempt.
- **Totals differ:** check which input and output folders you used, inspect the rejection reasons, and rerun the supplied files without modifying them. The reference files under `expected/` show the expected results; source path separators may vary by operating system.

## Advanced multi-source recovery

Continue with [the advanced walkthrough](ADVANCED-WALKTHROUGH.md). It adds a source manifest, expected-depot coverage, input hashes, isolated run evidence, a last-known-good report, and failure-safe promotion. Complete its runs and technical review before the graded lab.

## Practice deliverables and model interpretation

For your own review, retain both summaries, the initial rejection file, and recovered totals. Write two or three sentences explaining the hold, the correction, and one limitation. Practice is ungraded; a push is optional unless your instructor requests it.

**Model decision note:** Hold the initial report because three of five input rows failed the stated rules; the partial 13-unit total is not complete. The corrected file passes all checks and reconciles to four accepted events and 19 units, so it can be released under this exercise's gate. Validation cannot establish whether a source value is true, and a separate run folder is needed to preserve earlier evidence.

For the separate graded lab, copy its starter into your assigned private student repository, work there, push meaningful commits, and submit the requested repository link through D2L. Never push student work to the instructor source repositories.
