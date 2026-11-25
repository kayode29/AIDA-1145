# AIDA 1145 - Week 11 Graded Lab 7: Service Hours Recovery

## Run Instructions

### 1. Requirements
- Windows PowerShell
- Python 3 available through the py command
- No third-party Python packages required

### 2. Project folder
Run commands from:
C:\Users\user\Downloads\AIDA-1145\week-11\graded-lab-07-service-hours-recovery

### 3. Check Python
py --version
py -m py_compile .\starter.py

### 4. Initial batch
Example command for a clean copy only:
py .\starter.py .\data\service_batches.csv .\data\batch_manifest.json .\runs\initial .\release

Expected result:
- Decision: HOLD
- Input rows: 8
- Selected: 5
- Superseded: 1
- Retransmitted: 1
- Exceptions: 1

### 5. Corrected batch
Example command for a clean copy only:
py .\starter.py .\data\corrections.csv .\data\batch_manifest.json .\runs\corrected-1 .\release

Expected result:
- Decision: RELEASE
- Input rows: 8
- Selected: 6
- Superseded: 1
- Retransmitted: 1
- Exceptions: 0

### 6. Published release
The corrected release contains:
- release\report.csv
- release\selected_records.csv
- release\release_metadata.json

Expected branch totals:
- East: 5 hours
- North: 4 hours
- West: 5 hours
- Total: 14 hours

### 7. Test evidence
Test files:
- tests\missing_column.csv
- tests\same_revision_conflict.csv

The missing-column test produces HOLD because a required column is absent.
The same-revision conflict test produces HOLD because identical ticket and revision identifiers have conflicting hours.

Every execution requires a new run folder. Never reuse an existing run folder.

### 8. Reproducibility
The corrected batch was run twice. SHA256 comparisons confirmed identical published report snapshots and selected-record snapshots.

Failed test runs did not overwrite the previously published release.

### 9. Final decision
The corrected batch passed the release gates. The final decision is RELEASE.

The completed lab includes the proposal, Python implementation, test evidence, release files, and final decision documentation.

IMPORTANT: These commands are examples for reproducing the work on a clean copy. Do not rerun them with run-folder names that already exist.
