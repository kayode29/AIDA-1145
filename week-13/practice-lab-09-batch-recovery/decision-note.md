# Practice Lab 9 — Decision Note

## 1. Initial batch decision

The initial batch received a HOLD decision even though both expected pages were visited. The batch contained 5 input rows: 3 accepted events, 1 identical replay, and 1 error.

Event A102 appeared twice with identical information. The second occurrence was correctly classified as a replay and was not counted twice. Event A104 contained negative units, so it was invalid. This caused the expected event set to be incomplete. The pipeline correctly withheld the depot totals.

## 2. Recovery and validation

The corrected input changed A104 to 2 units. The recovered run returned PASS.

The recovered batch recorded:
- Input rows: 5
- Accepted events: 4
- Identical replay rows: 1
- Error rows: 0
- Missing event IDs: none
- Unexpected event IDs: none
- Total units: 14

The depot totals were:
- North: 8 units
- South: 4 units
- West: 2 units

The page 1 hash and manifest hash remained unchanged, while the page 2 hash changed. This is evidence that the corrected page was different while page 1 and the manifest stayed the same.

## 3. Repeatability check

I ran the corrected batch a second time using a separate output folder. The second run also returned PASS and produced the same row counts, total units, page hashes, and manifest hash.

I compared the recovered and repeat depot_totals.csv files using Compare-Object. The command returned no differences, confirming that both reports were identical.

This demonstrates repeatability for these same local input files. It does not prove that the source data is accurate or that a live production system would behave identically.

## 4. Missing-page test and operator action

I copied the corrected input pages into a separate test folder and removed page2.json from that copy. The original corrected input was not changed.

The test returned HOLD because page2.json could not be found. Only page1 was visited, and the row evidence file recorded A101, A102, and A103. No depot_totals.csv file was created.

The operator should keep the HOLD evidence, request the missing page or corrected cursor sequence from the source owner, and rerun the batch in a new output folder after the issue is resolved. The operator should not invent missing records or publish incomplete totals. A cursor cycle should also result in HOLD and require investigation of the source pagination sequence.

## 5. One limitation

This lab uses saved JSON files and reads the pages locally. It does not demonstrate live API network retries, transactional publication, concurrent-writer locking, or persistent checkpoints. Page hashes help identify changes to input files, but they do not independently prove that the source data is authentic or accurate.
