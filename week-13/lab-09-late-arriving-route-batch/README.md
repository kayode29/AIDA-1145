# Graded Lab 9: Recover a late-arriving route batch

**AIDA 1145 · Lab 9 · two mandatory parts · one submission**

A delivery operator prepares a 9:00 a.m. depot workload report. The source provides a snapshot of route events and later supplies updates. An event can occur before the reporting cutoff but arrive after the first snapshot. Some rows may also be retransmissions or later revisions. The operator needs a decision that is complete, reproducible, and explainable—not a report that silently counts a retry twice or overlooks a late arrival.

**Schedule:** This lab is remote; no in-class attendance is required. Complete Parts A and B and submit them together by **Thursday, November 26, 2026 at 11:59 p.m.** You may submit early. Keep both parts in one lab folder and make one D2L submission for this lab.

After reviewing final project progress, I have arranged Labs 9 and 10 for remote work so you can manage your time. I recommend completing both labs early, then focusing on your final project. Lab 9 is due November 26; Lab 10, the final lab, is due December 3.

## Files and business contract

| File | Purpose |
|---|---|
| `data/snapshot_initial.csv` and `manifest_initial.json` | The initial 09:00 snapshot and its expectations. |
| `data/snapshot_recovered.csv` and `manifest_recovered.json` | A later snapshot that includes additional arrivals for the same reporting batch. |
| `data/source_update.md` | Source-owner explanation of the later data. |
| `starter.py` | Optional, deliberately incomplete command-line scaffold. |

Use Python 3 and the supplied local files. No live service, API key, database server, or paid software is required. Do not modify the supplied inputs; create separate test copies.

### Rules to implement

1. The manifest identifies the reporting batch, **event-time cutoff**, snapshot **as-of time**, and exact expected event IDs. These are different concepts: `event_time_utc` says when the event occurred; `arrived_at_utc` says when the source received that version; the snapshot includes versions arriving no later than its as-of time. An arrival after the reporting cutoff can still represent an in-scope event. The source update explains why the second snapshot is later.
2. Validate required columns and nonempty event IDs and depots. `revision` must be a positive integer and `units` a non-negative integer. Parse timestamps in the supplied UTC `YYYY-MM-DDTHH:MM:SSZ` format. A valid row must have `event_time_utc <= reporting_cutoff_utc` and `arrived_at_utc <= snapshot_as_of_utc`. Classify invalid rows as errors; do not silently change their values.
3. Within each `(event_id, revision)`, exact repeats of **all supplied fields** are retransmissions. Count one candidate and classify each additional identical input row as a replay. If non-identical valid rows share the same event ID and revision, that ID is in conflict: classify all its distinct valid candidate rows as errors, classify identical extra copies as replays, select no version for that ID, and hold the run. Invalid rows remain errors independently.
4. For an event ID without a conflict, select the **highest valid revision** as the current event; classify the other distinct valid revisions as superseded. An error anywhere in the batch still causes a hold even if another valid revision exists. Never use input order as the revision rule.
5. Every input row must receive exactly one classification:

   ```text
   input rows = selected events + superseded rows + identical replays + error rows
   ```

   Compare the selected event-ID **set** with the manifest's expected set, and report missing and unexpected IDs separately. Matching counts alone are insufficient. Hold if there is any error or conflict, a missing or unexpected ID, an invalid manifest, or failed reconciliation. A held run produces evidence but no released depot report.
6. A passing report sums the selected units by depot. Keep attempts in separate output folders so a held run cannot be mistaken for a new passing report. Identify the source and manifest for each run. A repeated run on the same inputs must not append the same events a second time.

## Part A — technical solution proposal

Create `part-a-proposal.md`. This is a design proposal; finished code is not required for Part A. Include:

1. A diagram or ordered description of the stages, their inputs and outputs, and the dependency that prevents a held batch from being released.
2. Your interpretation of event time, arrival time, cutoff, and snapshot time. Explain why an event arriving after the cutoff may still belong in the report.
3. The classification and revision logic, including exact replay versus same-revision conflict, the row-accounting equation, and the expected-ID set check.
4. A test table with **at least six** cases: identical replay, higher revision, same-revision conflict, missing expected ID, an event exactly at the cutoff, and an arrival after the cutoff but within the later snapshot. State the input or change, expected decision, and evidence for each.
5. Your recovery and repeatability approach, including how you will retain the initial attempt and show that a rerun does not double-count; identify one limitation.

Keep the original proposal in your final lab folder. If you change your design during Part B, document the change rather than rewriting the proposal.

## Part B — implement, test, and explain

Use the optional starter or write your own documented program. If using the starter interface, implement its placeholders and run commands in this form:

```bash
python starter.py data/manifest_initial.json data/snapshot_initial.csv runs/initial
python starter.py data/manifest_recovered.json data/snapshot_recovered.csv runs/recovered
```

On Windows, `py` may replace `python`. Your implementation may use another interface if you provide clear reproducible commands in `run-instructions.md`.

1. Process the **initial** snapshot. Save a machine-readable summary naming the manifest and source, snapshot and cutoff, classification counts, missing and unexpected IDs, status, and reasons. Save row-level evidence with source row, event ID, revision, classification, and reason. Explain whether the operator can release a complete report at 09:00.
2. Process the **recovered** snapshot in a separate run folder. Save the same evidence and, only if the gate passes, a depot-units report. Explain what changed for J03 and J04 and why the later snapshot can include them without changing the event-time cutoff.
3. Run the recovered snapshot again in another folder. Compare selected event IDs and revisions, counts, and depot totals to demonstrate repeatability; retain both attempts and do not append duplicate output.
4. In **separate copies** of the input, create and retain (a) a conflicting same-event/same-revision row and (b) an event exactly at the cutoff whose arrival is within the snapshot. Run each test in its own folder. Show that the conflict is held and that the boundary event is handled according to the inclusive cutoff. Choose a test ID and manifest adjustment for the boundary case that makes the expected set explicit; explain the adjustment in your test notes.
5. In `run-instructions.md`, provide setup and exact commands for all runs and tests. In `part-b-decision.md`, compare both snapshots, cite your evidence, explain the time and revision decisions, reconcile the passing totals, describe any change from Part A, and state at least one limitation.

## Deliverables and one submission

Your lab folder must include `part-a-proposal.md`, executable code, supplied inputs, your test copies, `run-instructions.md`, initial/recovered/repeat/test summaries and row evidence, the passing depot report, and `part-b-decision.md`. Name files so another person can reproduce your decisions. Do not include credentials or unrelated data.

Copy the graded starter into your assigned **private student course repository**, complete both parts in the same lab folder, make meaningful commits and push. Verify the pushed files, then submit **one** private repository link in the D2L Lab 9 assignment. Do not push student work to either instructor source repository. Part A and Part B are components of one graded lab, not separate D2L submissions. The instructor will apply the existing approved assessment criteria and grade item.
