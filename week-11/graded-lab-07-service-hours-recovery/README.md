# Graded Lab 7: Recover a service-hours reporting pipeline

**AIDA 1145 · remote · one lab with two mandatory parts**

A field-service company uses a daily batch of ticket updates to plan staffing by branch. Tickets may be retransmitted or corrected. A report that double-counts retransmissions or silently accepts a bad revision can misdirect the next day's staffing. Your task is to propose and implement a recovery workflow that distinguishes those cases and provides evidence for its release decision.

**Due: Thursday, November 12, 2026 at 11:59 p.m. Mountain Time.** Both parts are remote and are due together. Allow approximately one hour for the Part A technical proposal; Part B is your implementation and evidence. Keep both in one folder and make one D2L submission.

## Source files and contract

Use `data/service_batches.csv` for the first run, `data/corrections.csv` for a corrected source, and `data/batch_manifest.json` for both. Each row is a version of a ticket, identified by `ticket_id` and integer `revision`. `hours` is a non-negative integer; `branch` must be one of the manifest's expected branches. The manifest states whether the handoff is complete, the expected number of distinct tickets, and the branches that must be represented. Treat these supplied rules as the source contract.

A ticket can occur more than once. Apply these rules in order, and document each decision:

1. Validate required columns and each row's ticket ID, branch, hours, and positive integer revision. An invalid row must be reported, even if a different row for that ticket is valid.
2. Rows identical in all four fields with the same ticket and revision are **retransmissions**: retain one candidate and account for each additional row separately; do not count their hours twice.
3. If valid rows share a ticket and revision but disagree in branch or hours, classify that revision as a conflict and hold the batch. Do not guess which value is correct.
4. For each ticket without a conflict, choose the highest valid revision as the current candidate and classify lower valid revisions as superseded. Invalid rows remain exceptions; they cannot be used to replace an older row silently.
5. Reconcile every input row exactly once as selected, superseded, retransmitted, or exception. The formula is `input = selected + superseded + retransmitted + exceptions`. Classify each distinct conflicting row for that ticket/revision as an exception; identical extra copies remain retransmissions. If a ticket has a conflict at any revision, do not select a current row for that ticket; classify its other valid, nonduplicate rows as exceptions too. Explain the reasons so no row is counted twice.
6. Release only if the handoff is complete, there are no exceptions or conflicts, selected ticket count matches the expected distinct-ticket count, and selected rows cover every expected branch. An incomplete or failed run must not replace a previously passing report. Record whether a previous report remains available and clearly identify its batch or run.

Do not assume that a matching count proves the selected records are correct. Keep the original and corrected source files unchanged and identify the source version used for each run.

## Part A — one-hour technical solution proposal

Write `part-a-proposal.md` (allow approximately one hour):

- Draw or describe the stages and dependencies, including the point at which a candidate becomes a published report.
- Explain your classification order, how you distinguish a retransmission from a conflicting same-revision update, and how you select the current ticket version.
- Show the row-accounting formula and describe the separate completeness and coverage checks.
- Provide a test table with at least **six** cases: identical retransmission, valid revision, invalid value, same-revision conflict, missing column, and successful recovery. State input, expected classification or release decision, and evidence to inspect.
- Explain how you will preserve the first run, prevent a failed run replacing a good report, and demonstrate a safe rerun. Identify one limitation.

Retain your original proposal alongside your completed implementation.

## Part B — implement, test, and explain

Use Python 3 and the provided files; no external services are required. `starter.py` is optional and deliberately incomplete; before you implement it, running it will raise `NotImplementedError`. The starter uses only the Python standard library. If you use its command-line interface, pass the source, manifest, a **new** run-evidence folder, and a release folder, in that order. For example, after implementing it:

```bash
python starter.py data/service_batches.csv data/batch_manifest.json runs/initial release
```

Your own implementation may use a different interface if `run-instructions.md` documents it. Create clear commands and implement the contract above.

1. Run the initial source and preserve a machine-readable run summary plus row-level classification evidence. Report the input and category counts, source identifier, expected and observed distinct tickets, expected and observed branches, and reasons for the release decision. A held run must not publish a new report.
2. Process the corrected source in a separate run folder. If the gate passes, produce total selected hours by branch. Preserve the initial evidence and explain how the corrected revision affects the result.
3. Repeat the corrected source using a new run identity. Show that the selected records and totals are unchanged and no rows were appended to the report. Retain both attempts.
4. Demonstrate a missing-column test and a same-ticket/same-revision conflict in separate test inputs. Both must hold and must not replace your last passing report. Save the test inputs and observed results.
5. Write `part-b-decision.md` comparing the observed runs, each gate, the correction and rerun; cite the evidence files, explain any change from your proposal, and describe one limitation. Include `run-instructions.md` with commands another student can follow.

## Deliverables and one submission

Your single lab folder must contain the original proposal, code, supplied inputs, any test inputs, run instructions, row-level evidence and summaries for both source runs and the two failure tests, a passing report, rerun evidence, and the decision note. Keep any instructor-only answer material out of your submission.

Copy the starter into your assigned private student course repository. Work there, commit and push meaningful changes, verify the required files on GitHub, and submit **one repository link** in the D2L Lab 7 assignment. Both parts are mandatory components of this one submission. Do not push to an instructor repository.

Part A assesses your technical proposal; Part B assesses the implementation, evidence, recovery, repeatability, and explanation. Your instructor applies the existing approved assessment criteria.
