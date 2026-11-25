# AIDA 1145 - Week 12 Graded Lab 8
# Run Instructions

## 1. Requirements
- Windows PowerShell
- Python 3 installed
- No third-party Python packages required

## 2. Project folder
Run all commands from:

week-12/graded-lab-08-regional-service-revenue

## 3. Check Python syntax

py -m py_compile .\starter.py

## 4. Run the candidate reference

py .\starter.py .\data\service_entries.csv .\data\site_history_candidate.csv .\runs\candidate

Expected decision: HOLD.

The candidate reference contains overlapping S2 intervals and missing S3 coverage.

## 5. Run the approved reference

py .\starter.py .\data\service_entries.csv .\data\site_history_approved.csv .\runs\approved

Expected decision: PASS.

Expected result:
- 6 canonical entries
- 1 identical retransmission
- 6 released facts
- Revenue of 17,300 cents

## 6. Repeatability test

py .\starter.py .\data\service_entries.csv .\data\site_history_approved.csv .\runs\approved-repeat

Compare the SHA-256 hashes of facts.csv and regional_report.csv in the approved and approved-repeat folders.

## 7. Conflict test

py .\starter.py .\tests\conflict\service_entries_conflict.csv .\data\site_history_approved.csv .\runs\test-conflict

Expected decision: HOLD because E02 has conflicting values.

## 8. Date-boundary test

py .\starter.py .\tests\boundary\service_entries_boundary.csv .\data\site_history_approved.csv .\runs\test-boundary

Expected decision: PASS.

E07 dated 2026-11-10 must be assigned to West.

## 9. Output files

Every run produces:
- summary.json
- source_diagnostics.csv
- source_errors.csv
- replays.csv
- reference_diagnostics.csv
- match_diagnostics.csv

Passing runs also produce:
- facts.csv
- regional_report.csv
- reconciliation.json

Held runs do not produce a released fact table or regional report.

## 10. Important notes

Use a separate, empty output folder for each run.

Do not modify the supplied source files while performing tests.

All revenue amounts are stored as integer cents.
