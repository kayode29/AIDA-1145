# AIDA 1145 — Week 13 Graded Lab 9
## Test Notes — Late-Arriving Route Batch Recovery

### Purpose

These tests verify snapshot completeness, event revision handling, replay detection, conflict handling, cutoff rules, row accounting, and repeatability.

Test modifications were made to separate copies of the supplied input files. The original data files were preserved.

### Test 1 — Initial Snapshot

Command:

py .\starter.py .\data\manifest_initial.json .\data\snapshot_initial.csv .\runs\initial

Actual result:
- Status: HOLD
- Input rows: 4
- Selected: 3
- Replay: 1
- Superseded: 0
- Error: 0
- Missing event ID: J04
- Depot totals report: Not released

Reason: The initial snapshot is missing expected event J04.

### Test 2 — Recovered Snapshot

Command:

py .\starter.py .\data\manifest_recovered.json .\data\snapshot_recovered.csv .\runs\recovered

Actual result:
- Status: PASS
- Input rows: 6
- Selected: 4
- Superseded: 1
- Replay: 1
- Error: 0
- Missing event IDs: None
- East: 11 units
- West: 6 units
- Total: 17 units
- Depot totals report: Released

J03 revision 2 was selected over revision 1. The identical J02 retransmission was classified as a replay.

### Test 3 — Repeatability

Command:

py .\starter.py .\data\manifest_recovered.json .\data\snapshot_recovered.csv .\runs\repeat

Actual result:
- Status: PASS
- Input rows: 6
- Selected: 4
- Superseded: 1
- Replay: 1
- Error: 0
- Depot totals: East 11, West 6
- Manifest and source hashes: Same as the recovered run

The separate repeat run produced the same result without adding duplicate units.

### Test 4 — Same-Revision Conflict

Command:

py .\starter.py .\test-inputs\conflict\manifest_conflict.json .\test-inputs\conflict\snapshot_conflict.csv .\runs\conflict

Actual result:
- Status: HOLD
- Input rows: 7
- Selected: 3
- Superseded: 1
- Replay: 1
- Error: 2
- Conflict event ID: J01
- Missing event ID: J01
- Depot totals report: Not released

Two different J01 revision 1 records were detected. Both were classified as errors rather than choosing one arbitrarily.

### Test 5 — Inclusive Reporting Cutoff

Command:

py .\starter.py .\test-inputs\cutoff\manifest_cutoff.json .\test-inputs\cutoff\snapshot_cutoff.csv .\runs\cutoff

Actual result:
- Status: PASS
- Input rows: 7
- Selected: 5
- Superseded: 1
- Replay: 1
- Error: 0
- East: 12 units
- West: 6 units
- Total: 18 units
- Depot totals report: Released

J05 was accepted because its event time was exactly equal to the reporting cutoff (09:00 UTC). Its arrival time (09:20 UTC) was within the snapshot as-of time (09:30 UTC).

### Overall Test Conclusion

All five tests produced their expected results.

The recovered snapshot passed the release checks. The initial snapshot and the conflict test correctly received HOLD status.

Every input row was accounted for, and depot totals were released only for snapshots that passed the release checks.

### Test Manifest Adjustment — Inclusive Cutoff

The inclusive cutoff test uses separate copies of the recovered manifest and snapshot.

The copied manifest was adjusted as follows:

- `expected_event_ids` was changed from `["J01","J02","J03","J04"]` to `["J01","J02","J03","J04","J05"]`.
- `reporting_cutoff_utc` remained `2026-11-25T09:00:00Z`.
- `snapshot_as_of_utc` remained `2026-11-25T09:30:00Z`.

The copied snapshot was given an additional J05 record:

- Event ID: J05
- Revision: 1
- Depot: East
- Units: 1
- Event time: 2026-11-25T09:00:00Z
- Arrival time: 2026-11-25T09:20:00Z

This adjustment allowed the test to verify that an event exactly at the reporting cutoff is accepted while its arrival remains within the snapshot as-of time.

The original files in `data/` were not changed. The adjusted files are preserved in:

- `test-inputs/cutoff/manifest_cutoff.json`
- `test-inputs/cutoff/snapshot_cutoff.csv`
