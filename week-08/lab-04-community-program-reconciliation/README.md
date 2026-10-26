# Week 8 — Lab 4: Community Program Pipeline Reconciliation

**Course:** AIDA 1145

**Assessment:** one integrated graded lab, worth 5% of the course grade

**Submission:** one lab folder in your assigned private course repository and one D2L submission

**D2L deadline:** Wednesday, October 21, 2026 at 5:30 p.m. The D2L assignment deadline is authoritative.

## Purpose

Build and explain a small, reproducible data pipeline that reconciles community recreation registrations with a program catalogue. This is the Week 8 cumulative pipeline-build activity. It brings together data contracts, file and schema checks, explicit scope rules, joins, data-quality checks, reproducible processing, and release evidence from earlier course topics.

This is one continuous Lab 4 worth 5% of the course grade. Keep every required document, code file, and output in this same lab folder. Submit the folder once through your assigned private course repository and make one D2L submission. Do not create separate submissions or separate lab folders.

The approved course outline identifies a guided pipeline-build criterion worth 3% and a production-quality criterion worth 2%. Both are demonstrated through this one continuous pipeline workflow and together make up the 5% Lab 4 assessment. They do not require separate folders or submissions.

## Scenario

A community recreation office receives registrations and joins them to a program catalogue before preparing a fee and attendance view. The candidate catalogue intentionally duplicates one program code and omits another in-scope code. A separate release note identifies an authoritative reference version. Your pipeline must show why the candidate is unsafe and whether the documented reference can be accepted.

## What to do

1. **Understand the case before coding.** Read `contracts/registration_contract.json` and `data/catalogue_release_note.md`. Inspect all three CSV files. The registration file is the source; the candidate catalogue is deliberately unsafe; the release note identifies the approved reference snapshot. Do not edit supplied input records, silently remove a catalogue row, or invent a missing program.
2. **Describe the data flow.** Complete `docs/design-work/interface_map.md`. State what one source row represents, identify the keys and batch, explain which statuses are in scope, describe the expected join relationship, and define what one accepted output row represents.
3. **Plan the checks.** Complete `docs/design-work/test_plan.md` before relying on the output. Include normal and failure cases for the source contract, duplicate catalogue keys, missing program codes, join fan-out, row counts, distinct registration IDs, fee totals, invalid status, and wrong-batch records. For each check, state what condition you will examine and what evidence will show the result.
4. **Implement the pipeline.** Complete `src/starter_pipeline.py` or provide a clearly documented replacement in this folder. Use Python 3.12+ and its standard library. Keep `fee_cents` as integer cents throughout calculations; convert to dollars only for display, if needed.
5. **Inspect the candidate without hiding defects.** Count duplicate catalogue keys, find unmatched active registrations, preserve a candidate join preview, and record row and fee controls. A left join preview should retain unmatched registrations and every duplicate match so the diagnostics remain visible.
6. **Evaluate the approved reference separately.** Use the version named in the release note. Build the accepted view only after the required checks pass. If a check fails, record a HOLD decision and its evidence; do not label a partial or unsafe result as accepted.
7. **Keep the evidence together.** Write the required outputs and complete `docs/decision_record.md`, `docs/design-changes.md`, and `docs/ai-use-declaration.md` in this same Lab 4 folder.
8. **Re-run and explain.** Run the pipeline twice from this folder. Compare the generated outputs, record whether they are reproducible, and use the evidence to explain the final release recommendation.

## Required evidence

Your one lab folder must include:

- a repeatable run command and the Python version used;
- source, excluded, eligible, matched, and unmatched counts in a row ledger;
- evidence of duplicate catalogue keys and unmatched in-scope program codes;
- candidate join row count, distinct registration IDs, and fee control total;
- an explanation of why the candidate should be held;
- the authoritative reference version and checks for unique keys and full in-scope coverage;
- an accepted view with one row per active registration and a reconciled fee total, if all checks pass;
- a concise ACCEPT or HOLD decision with supporting evidence.

The row ledger should make the stages understandable: source, excluded, active, matched, and unmatched records; candidate join rows and distinct registration IDs; and fee totals before and after processing. Label each number so a reviewer can tell which file and stage it describes.

Generate these outputs under `outputs/`: `row_ledger.json`, `run_summary.json`, `candidate_join_preview.csv`, and `accepted_registrations.csv` (or clearly documented equivalents). Keep the candidate diagnostics even when the decision is HOLD.

## Submission instructions

1. Copy this complete `lab-04-community-program-reconciliation` folder from the instructor Graded Labs repository into your assigned private course repository.
2. Complete and save all work inside that folder. Keep the interface map, test plan, code, generated outputs, and decision evidence together. Make meaningful commits as you work.
3. Push the completed folder to your assigned private repository by the D2L deadline above.
4. In the single D2L Lab 04 assignment, submit **one link** to your private repository and the commit containing this Lab 4 folder. This is one submission for the complete lab, not separate links or uploads for individual documents or tasks.

Do not push your work to the instructor Practical Lab Examples or Graded Labs repositories. Do not submit separate links or uploads for any individual task or evidence file. Do not include credentials, tokens, personal data, or unrelated files.

## Tools

Use Python 3.12+ and its standard library. No database, framework, or external package is required.

## Help with the pipeline reasoning

- **Grain** means what one row represents. Here, the contract requires one source row per `registration_id` and one accepted output row per active registration.
- **Join key** means the value used to match records. Here, registrations match catalogue rows through `program_code`.
- **Many-to-one** means many registrations may use the same program, while each program code must identify at most one catalogue row in the selected catalogue version.
- A duplicate catalogue key can make a registration appear more than once after a join. A missing catalogue key can leave an active registration without program details. Preserve evidence of both conditions.
- A **control total** is a business quantity compared before and after processing. For this case, add eligible `fee_cents` values and compare the total with the accepted-view total. Equal totals are useful evidence, but they do not by themselves prove that the same registrations are present.
- An **anti-join** identifies active registrations whose `program_code` has no catalogue match. Use it as a diagnostic; do not discard the unmatched registrations silently.
- An **ACCEPT** decision applies only to the supplied batch and approved catalogue version after every required condition in the contract passes. Otherwise, record **HOLD** and state which condition failed.

## Folder map

- `contracts/` — registration data contract.
- `data/` — supplied registration and catalogue snapshots and the catalogue release note.
- `docs/design-work/` — interface-map and test-plan templates.
- `docs/implementation/` — implementation and verification guide.
- `src/starter_pipeline.py` — intentionally incomplete starter scaffold.
- `outputs/` — student-generated run evidence; retain the README and add your outputs.
- `docs/` — decision record, design notes, and AI-use declaration.

This instructor starter does not contain a completed student solution or answer key.
