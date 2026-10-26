# Implementation and verification guide

Use this guide alongside the top-level `README.md`. The implementation, design notes, tests, generated files, and release decision are all evidence for the same integrated Lab 4. Keep them in this one folder.

## 1. Read and map the inputs

Read `contracts/registration_contract.json` first. It is the stated source of the required columns, field types, key, row meaning, batch, scope, join relationship, and acceptance conditions. Then read `data/catalogue_release_note.md` to identify the approved reference version. Inspect the candidate and reference CSV snapshots without changing them.

Complete `docs/design-work/interface_map.md` in your own words. Make clear:

- what one registration row represents;
- which identifier must be unique;
- which batch and statuses are in scope;
- which field links a registration to the catalogue;
- what join relationship is expected; and
- what one row in the accepted view must represent.

This map helps you decide what the pipeline must check before it processes records.

## 2. Validate the source contract before transforming data

Read each CSV with its expected header. Reject an unexpected schema rather than silently guessing how a renamed or reordered field should be interpreted. Check required values, parse integer fields explicitly, validate the allowed statuses, confirm that registration IDs are present and unique, and confirm that each source record belongs to the declared batch.

The source contract describes one row per `registration_id`. If an ID is blank or repeated, stop before joining: downstream counts and totals would no longer describe the declared records reliably. Report the offending field or record in a useful error message; do not quietly drop the row.

## 3. Apply scope explicitly and keep a row ledger

Only active registrations belong in the accepted view. Cancelled registrations still need to be accounted for in the ledger so a reviewer can reconcile the source to the in-scope records.

Use these relationships to check the scope calculation:

```text
source rows = active rows + cancelled rows
active fee total = sum(fee_cents for active registrations)
```

Do not exclude a registration because its program code fails to match. Scope is decided from the documented status and batch rules; a missing program match is a separate data-quality issue that must remain visible.

## 4. Profile the candidate catalogue and identify unmatched registrations

Count each `program_code` in the candidate catalogue. Any code with a count greater than one is duplicated. Then compare the active registration program codes with the catalogue codes. An anti-join (or equivalent key-set check) should return the active registrations for which no candidate catalogue row exists.

Preserve both findings. They describe different risks:

- A duplicate catalogue key can create more than one joined row for a registration. This is join fan-out.
- A missing catalogue key means an active registration has no program details. A left join keeps the registration but leaves catalogue fields blank.

Do not choose the first duplicate, remove a row, fabricate a program, or otherwise repair the supplied snapshots. The release note and the separate reference snapshot provide the case's approved correction path.

## 5. Build a candidate preview and check the join grain

Use a left-join preview for the candidate so that all active registrations remain inspectable. Preserve every match, including duplicates, and retain one row with empty catalogue fields when no match exists. This preview is diagnostic evidence; it is not the accepted view.

The expected relationship is many registrations to one catalogue row per `program_code`. For the accepted view, verify all of the following:

```text
accepted row count = active registration count
distinct accepted registration IDs = active registration count
```

The first check catches row-count changes. The second checks record identity. Matching counts alone are not enough: duplicated IDs and missing IDs can offset one another and still produce a plausible total.

## 6. Reconcile fees and preserve integer precision

Keep all monetary calculations in integer cents. Compute the active source total and compare it with the accepted-view total:

```text
active_fee_cents = sum(fee_cents for active registrations)
accepted_fee_cents = sum(fee_cents in the accepted view)
fee_difference_cents = accepted_fee_cents - active_fee_cents
```

The required fee reconciliation passes when the difference is zero. If you display dollars, convert only after calculating the integer-cent totals. State which rows and stage each total represents.

Fee reconciliation is one control, not a substitute for key, match, and grain checks. A total can agree even if the wrong registrations are present.

## 7. Apply the approved-reference acceptance gate

Read the release note and use the catalogue version it identifies. Check that its program codes are unique and that every active registration has a catalogue match. Build the accepted view only after those reference checks pass. Then verify the accepted-view grain, distinct registration IDs, and fee total against the active source records.

Record an **ACCEPT** decision only when every required acceptance condition in `contracts/registration_contract.json` passes. Otherwise record **HOLD**, identify each failed condition, and preserve the diagnostics. Do not label a partial output as accepted.

An approved source version identifies which reference snapshot to evaluate; it does not remove the need to validate that snapshot against the contract.

## 8. Write the evidence files

Generate these files under `outputs/`:

- `row_ledger.json` — clearly labelled source, active, cancelled, matched, unmatched, join-row, distinct-ID, and fee counts/totals;
- `candidate_join_preview.csv` — candidate join rows that expose duplicated and unmatched catalogue matches;
- `accepted_registrations.csv` — the accepted view, written only when the acceptance checks pass;
- `run_summary.json` — source batch, catalogue versions, named check results, and the final HOLD/ACCEPT decisions.

Use consistent field names and explicit labels. A reviewer should be able to tell whether a count describes the source, candidate join, or accepted view without inferring it from context.

Complete the `docs/decision_record.md` with the exact command and Python version, input files, batch and catalogue versions, key counts, fee totals in cents, decision, and reproducibility observation. In `docs/design-changes.md`, explain meaningful implementation choices and their evidence. Complete `docs/ai-use-declaration.md` honestly, including any independent verification you performed.

## 9. Run twice and compare

From the Lab 4 folder, check your Python version and run the pipeline twice:

```text
py --version
py src/starter_pipeline.py
py src/starter_pipeline.py
```

If the `py` launcher is unavailable, use `python` for both commands. Use Python 3.12 or later. The lab uses the standard library only; no database, framework, external package, credentials, or internet connection is required.

Compare the generated files from both runs. Record whether the same inputs produced the same evidence. If a run stops with a validation or acceptance failure, record the message and the stage where it occurred; do not suppress the failure to force an accepted output.

## 10. Submit the complete lab once

Keep all work in the `lab-04-community-program-reconciliation` folder. Commit meaningful progress to your assigned private course repository and push the completed folder there. Then make **one** submission in the D2L Lab 04 assignment: provide one link to the repository and the commit containing this folder. Do not send separate links or uploads for the map, test plan, code, outputs, or decision record. Do not push student work to either instructor source repository.
