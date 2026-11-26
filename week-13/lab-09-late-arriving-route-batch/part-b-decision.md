# Part B — Recovery Decision Note

## 1. Final decision

The recovered route batch ROUTE-20261125 is approved for release.

The initial snapshot is placed on HOLD because event J04 is missing from the expected event set. The recovered snapshot contains all four expected event IDs and passes the validation, revision, replay, conflict, and row-accounting checks.

## 2. Initial snapshot assessment

The initial snapshot contains 4 input rows.

Classification:
- Selected: 3
- Superseded: 0
- Replay: 1
- Error: 0

Event J04 is missing. Therefore, the initial snapshot receives HOLD status and no depot totals report is released.

## 3. Recovered snapshot assessment

The recovered snapshot contains 6 input rows.

Classification:
- Selected: 4
- Superseded: 1
- Replay: 1
- Error: 0

Selected events:
- J01, revision 1, East, 6 units
- J02, revision 1, West, 4 units
- J03, revision 2, East, 5 units
- J04, revision 1, West, 2 units

J03 revision 2 replaces revision 1 because it is the highest valid revision. The identical retransmission of J02 is classified as a replay and is not counted twice.

All expected event IDs are present. Row accounting passes: 6 input rows equal 6 accounted rows.

## 4. Released depot totals

| Depot | Units |
|---|---:|
| East | 11 |
| West | 6 |
| Total | 17 |

The recovered snapshot receives PASS status and its depot totals report is released.

## 5. Repeatability test

The recovered input was processed again using a separate output directory.

The repeat run produced the same:
- Selected event IDs and revisions
- Classification counts
- Manifest and source hashes
- Depot totals

East remained 11 units and West remained 6 units. No additional units were added by the repeat run.

## 6. Conflict test

A separate test copy was created with two different J01 revision 1 records.

The records contained 6 units and 8 units respectively.

Both conflicting records were classified as errors. The system identified J01 as a same-revision conflict, placed the batch on HOLD, and did not release a depot totals report.

All 7 input rows were accounted for.

## 7. Inclusive cutoff test

A separate test copy included event J05 with:
- Event time: 2026-11-25T09:00:00Z
- Arrival time: 2026-11-25T09:20:00Z
- Units: 1
- Depot: East

The reporting cutoff was 2026-11-25T09:00:00Z.

The event was accepted because the event-time rule is inclusive: event time must be less than or equal to the reporting cutoff. Its arrival time was also within the snapshot as-of time.

The test passed with:
- Selected: 5
- Superseded: 1
- Replay: 1
- Error: 0
- East: 12 units
- West: 6 units
- Total: 18 units

## 8. Final recommendation

Release the recovered snapshot, not the initial snapshot.

The initial snapshot is incomplete, while the recovered snapshot satisfies the expected event set and all release checks.

The conflict test confirms that ambiguous same-revision records are not silently accepted. The inclusive cutoff test confirms that events occurring exactly at the reporting cutoff are valid.

## 9. Limitations

This solution validates the supplied manifests and CSV snapshots. It does not independently retrieve missing events from an external source. A missing event or unresolved conflict must be investigated and corrected in a new source snapshot before release.

## 10. Evidence references

The following generated files provide evidence for the decisions and results described above.

- Initial snapshot:
  - `runs/initial/summary.json`
  - `runs/initial/row_evidence.csv`

- Recovered snapshot:
  - `runs/recovered/summary.json`
  - `runs/recovered/row_evidence.csv`
  - `runs/recovered/depot_totals.csv`

- Repeatability test:
  - `runs/repeat/summary.json`
  - `runs/repeat/row_evidence.csv`
  - `runs/repeat/depot_totals.csv`

- Same-revision conflict test:
  - `runs/conflict/summary.json`
  - `runs/conflict/row_evidence.csv`

- Inclusive cutoff test:
  - `runs/cutoff/summary.json`
  - `runs/cutoff/row_evidence.csv`
  - `runs/cutoff/depot_totals.csv`

The summary files contain the run status, classification counts, expected and selected event IDs, and release results. The row evidence files show how individual input rows were classified. Depot totals files provide the released aggregation for passing runs.

## 11. Changes from the original proposal

The implementation follows the proposed validation, classification, accounting, and release-gate approach.

The implementation also includes separate conflict and inclusive-cutoff test runs using copied input files. The cutoff test uses an adjusted test manifest that includes J05 in the expected event IDs. The original supplied manifests and snapshots remain unchanged.

The implementation produces separate output directories for each run so that repeatability can be checked without overwriting earlier evidence.
