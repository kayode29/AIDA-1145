# Extension: release a complete multi-depot batch safely

The delivery director needs a report for **all three depots** before the morning planning meeting. A row can be valid on its own while the batch is incomplete. A source manifest reports the expected unique event count and signals that the handoff is complete. A separate reference identifies the depots that must appear. The business agrees that *any* rejected row, missing depot, incomplete handoff, or count mismatch holds the new release.

## Files and decisions

- `data/initial.csv` and `data/corrected.csv` are two versions of the event data. `data/manifest_initial.json` and `data/manifest_corrected.json` are their matching manifests; `data/expected_depots.csv` is the reference. Never pair a manifest with a different source version in real operations without verifying their relationship.
- `advanced_pipeline.py` records hashes of all three input files, a batch ID, rejected-row reasons, missing depots, counts, and the release decision. A hash identifies bytes; it does not prove who sent them or that they are correct.
- Each attempt gets a **new** run folder. The command refuses to overwrite an existing one. The `release/` folder represents the last successfully published report. A held run does not replace it; a passing run stages and promotes a report.

## Step 1: Diagnose the initial run

From the practice folder run:

```bash
python advanced_pipeline.py data/initial.csv data/manifest_initial.json data/expected_depots.csv runs/adv-initial release
```

Inspect `runs/adv-initial/summary.json` and `rejected.csv`. There are five input rows, two accepted, three rejected, and four distinct nonempty IDs. The unique-ID count matches the manifest, yet the run is **HOLD**: invalid rows exist and West is not represented in accepted records. This is why a row-count match is not a completeness guarantee. If there was no previous passing run, `release/current_report.csv` does not exist.

Row accounting and coverage are different checks:

```text
input rows = accepted rows + rejected rows = 2 + 3 = 5
missing depots = expected depots − depots represented by accepted rows = {West}
```

Count each input once even when a row has multiple reasons. A duplicate can make raw row count larger than unique IDs; a rejected row can contribute an ID but not valid depot coverage.

## Step 2: Recover and check the result

```bash
python advanced_pipeline.py data/corrected.csv data/manifest_corrected.json data/expected_depots.csv runs/adv-recovered release
```

The new run has four accepted rows, zero rejects, four distinct IDs, and all three expected depots. Inspect `summary.json` and `release/current_report.csv`: North 10, South 5, West 4. The status is `PASS`. The initial attempt remains in its own folder. Compare the hashes and batch IDs across summaries, then explain how the records show which input produced the released report.

## Step 3: Test the recovery design

Run the corrected input again using `runs/adv-rerun` as a new run folder. Compare the published hash and branch totals to the recovered run. The output is replaced, not appended. Now repeat the initial command with `runs/adv-held-again` and confirm the prior passing `release/current_report.csv` remains unchanged: the new held attempt did not publish a partial report. Do not confuse the old report with fresh data; consumers must check the batch/run evidence.

For a schema failure, copy the corrected source, remove the `units` header and its values, and run it in `runs/adv-schema`. Read `summary.json`: status stays `HOLD` with a missing-column failure. The last passing release remains in place. If you attempt to reuse `runs/adv-recovered`, the program stops before changing that evidence.

## Technical review and deliverables

Keep the four run summaries, the first rejection file, and the released totals for your own review. Write a short operational note: identify the failure, explain why the manifest count alone was insufficient, cite the corrected evidence, and state whether a consumer can use the last known good report. Distinguish *available* from *current*.

The release uses a temporary file in the release directory and `os.replace` for local promotion. It does not implement concurrent writer locking, cross-machine transactional guarantees, input authentication, or automatic alerting. The unique count includes IDs on invalid rows; that is intentional here and must be interpreted alongside rejection and coverage checks. An empty batch is not inherently valid for this case because the contract expects four events and three depots. For production, define these expectations per batch and test empty or changed schedules.
