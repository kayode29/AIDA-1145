# Part A: Technical Solution Proposal
## AIDA 1145 – Lab 9: Recover a Late-Arriving Route Batch

### 1. Pipeline design and release gate

The proposed workflow processes route-event snapshots using a controlled pipeline. Each stage produces evidence for the next stage. A depot report can only be released after all validation, reconciliation and completeness checks pass.

Pipeline stages:

1. **Read manifest:** Load the batch ID, reporting cutoff, snapshot as-of time and expected event IDs.
2. **Validate manifest:** Check required fields, timestamp formats and expected IDs.
3. **Read source snapshot:** Load the CSV and preserve the original input.
4. **Validate rows:** Check required columns, event IDs, depot names, revisions, units and timestamps.
5. **Classify rows:** Identify invalid rows, identical replays, same-revision conflicts, superseded revisions and selected events.
6. **Reconcile:** Compare selected event IDs against the expected event-ID set and verify the row-accounting equation.
7. **Apply release gate:** HOLD if any validation, conflict, completeness or reconciliation check fails.
8. **Publish report:** Only a passing batch produces a depot-units report.

Pipeline dependency:

Manifest and source snapshot
→ Manifest and row validation
→ Replay and revision classification
→ Expected-ID comparison
→ Row reconciliation
→ HOLD or PASS
→ Depot report only after PASS.

A held run retains its summary and row-level evidence but must not produce a released depot report.

### 2. Event time, arrival time, reporting cutoff and snapshot time

The four time concepts have different purposes:

- **Event time:** The UTC time when a route event actually occurred.
- **Arrival time:** The UTC time when the source received a particular event version.
- **Reporting cutoff:** The latest event time allowed in the 09:00 depot workload report.
- **Snapshot as-of time:** The latest arrival time included in a particular source snapshot.

An event is eligible when its event time is less than or equal to the reporting cutoff and its arrival time is less than or equal to the snapshot as-of time.

The event-time cutoff is inclusive. An event occurring exactly at 09:00 is therefore eligible.

An event can arrive after 09:00 and still belong to the report if it occurred at or before 09:00 and arrived by the snapshot as-of time.

For this batch:

- Reporting cutoff: 2026-11-25 09:00 UTC.
- Initial snapshot as-of time: 2026-11-25 09:00 UTC.
- Recovered snapshot as-of time: 2026-11-25 09:30 UTC.

J03 revision 2 arrived at 09:05 and J04 arrived at 09:10. Both events occurred before the reporting cutoff. The recovered snapshot can therefore include them without changing the reporting cutoff.

### 3. Classification, revision and reconciliation logic

Every input row must receive exactly one classification.

**Validation**

The program will check:

- Required CSV columns are present.
- Event IDs and depot names are nonempty.
- Revision is a positive integer.
- Units are a non-negative integer.
- Both timestamps use the supplied UTC format.
- Event time is no later than the reporting cutoff.
- Arrival time is no later than the snapshot as-of time.

Invalid rows are classified as errors. Their values will not be silently corrected.

**Identical replays**

Rows sharing an event ID and revision are compared across all supplied fields. If every field is identical, one candidate is retained and every additional identical row is classified as a replay.

**Same-revision conflicts**

If valid rows share an event ID and revision but have different supplied values, the event ID is considered conflicted. All distinct valid candidate rows for that ID are errors, while identical additional copies are replays. No version of that event ID is selected, and the run is held.

**Revision selection**

For an event ID without a conflict, the highest valid revision is selected. Lower distinct valid revisions are classified as superseded. Input row order will never determine the selected revision.

Any error in the batch causes a HOLD, even if another valid revision exists.

**Row accounting**

The program will reconcile every input row using:

Input rows = Selected events + Superseded rows + Identical replays + Error rows.

The selected event-ID set will also be compared with the manifest's expected event-ID set.

Missing IDs and unexpected IDs will be reported separately. Matching counts alone are not sufficient.

### 4. Proposed test cases

| Test | Input or change | Expected decision | Evidence |
|---|---|---|---|
| Identical replay | Add an exact duplicate of an existing event and revision | PASS if all other checks pass; duplicate classified as replay | Row evidence and replay count |
| Higher revision | Include J03 revision 1 and revision 2 | PASS if other checks pass; revision 2 selected and revision 1 superseded | Selected revision and classification summary |
| Same-revision conflict | Add a different valid J01 row with revision 1 | HOLD; no J01 version selected | Conflict errors and held summary |
| Missing expected ID | Remove J04 while retaining it in the manifest | HOLD; J04 reported missing | Missing-ID list and summary |
| Inclusive cutoff | Add a new event occurring exactly at 09:00 with arrival before the snapshot as-of time | PASS if the adjusted expected-ID set and all other checks pass | Boundary event selected in row evidence |
| Late arrival | Include J03 revision 2 and J04 with arrivals after 09:00 but before 09:30 | PASS if all checks pass | Selected events, arrival timestamps and depot totals |

For the inclusive-cutoff test, a separate test copy will be used. A new event ID will be added to the CSV and the expected event-ID list in the test manifest will be adjusted to include that ID. This makes the expected set explicit without changing the original supplied manifests.

Each test will have its own input copy and output folder.

### 5. Recovery, repeatability and limitation

The initial snapshot will be processed first and its summary and row evidence retained in a separate `runs/initial` folder. A held initial attempt will not be overwritten.

The recovered snapshot will be processed independently in `runs/recovered`. Its manifest will retain the same reporting cutoff but use the later snapshot as-of time of 09:30 UTC.

A second run of the recovered snapshot will be saved in `runs/repeat`. The selected event IDs, revisions, classification counts and depot totals will be compared between both recovered runs.

Each attempt will use a new output directory. The program will not append events to an earlier report or overwrite previous evidence.

Test inputs will be copied separately so that the supplied CSV files and manifests remain unchanged.

**Limitation:** This solution is designed for local batch processing using the supplied CSV files. It does not provide transactional publication, concurrent-writer locking or automatic recovery from failures in a live source system. Matching file hashes and repeatable totals demonstrate consistent processing of the same inputs but do not prove that the original source data is factually correct.

---

**End of Part A – Technical Solution Proposal**
