# AIDA 1145 — Week 13 Graded Lab 9
## Late-Arriving Route Batch Recovery

## 1. Requirements

- Windows PowerShell
- Python 3
- No third-party Python packages required

## 2. Project folder

Run all commands from:

C:\Users\user\Downloads\AIDA-1145\week-13\lab-09-late-arriving-route-batch

## 3. Compile the program

py -m py_compile .\starter.py

## 4. Initial snapshot test

py .\starter.py .\data\manifest_initial.json .\data\snapshot_initial.csv .\runs\initial

Expected result:
- Status: HOLD
- Input rows: 4
- Selected: 3
- Replay: 1
- Missing ID: J04
- No depot totals report released

## 5. Recovered snapshot test

py .\starter.py .\data\manifest_recovered.json .\data\snapshot_recovered.csv .\runs\recovered

Expected result:
- Status: PASS
- Input rows: 6
- Selected: 4
- Superseded: 1
- Replay: 1
- Error: 0
- East: 11 units
- West: 6 units

## 6. Repeatability test

py .\starter.py .\data\manifest_recovered.json .\data\snapshot_recovered.csv .\runs\repeat

Expected result:
- Status: PASS
- Same classifications and selected revisions as recovered
- Same depot totals: East 11, West 6

## 7. Conflict test

The conflict test uses separate copies of the recovered input files.

The test adds a second J01 revision 1 record with 8 units, while the original has 6 units.

Run:

py .\starter.py .\test-inputs\conflict\manifest_conflict.json .\test-inputs\conflict\snapshot_conflict.csv .\runs\conflict

Expected result:
- Status: HOLD
- J01 identified as a same-revision conflict
- Two error rows
- No depot totals report released

## 8. Inclusive cutoff test

The cutoff test uses separate copies of the recovered input files.

It adds J05 with event time exactly equal to the reporting cutoff:

2026-11-25T09:00:00Z

Its arrival time is:

2026-11-25T09:20:00Z

Run:

py .\starter.py .\test-inputs\cutoff\manifest_cutoff.json .\test-inputs\cutoff\snapshot_cutoff.csv .\runs\cutoff

Expected result:
- Status: PASS
- Selected: 5
- Superseded: 1
- Replay: 1
- Error: 0
- East: 12 units
- West: 6 units

## 9. Output files

Each successful or held run creates:
- summary.json
- row_evidence.csv

Only a PASS run releases:
- depot_totals.csv

Each run must use a separate output directory. The program refuses to overwrite an existing output directory.

## 10. Evidence locations

- Initial: runs/initial/
- Recovered: runs/recovered/
- Repeatability: runs/repeat/
- Conflict: runs/conflict/
- Inclusive cutoff: runs/cutoff/

## 11. Important rules

- Event time must be less than or equal to the reporting cutoff.
- Arrival time must be less than or equal to the snapshot as-of time.
- Identical retransmissions are classified as replays.
- The highest valid revision is selected.
- Lower valid revisions are superseded.
- Different records with the same event ID and revision cause a conflict and HOLD.
- Missing or unexpected event IDs prevent release.
- Every input row must be accounted for.
- Depot totals are released only when all release checks pass.
