# AIDA 1145 — Week 6 Graded Lab 3: Reproducible Delivery Pipeline

**Topic:** Pipeline orchestration and reproducibility
**Value:** 5% total — one lab folder, one private-repository push, one D2L submission
**Tools:** VS Code and Python 3.11+; Python standard library only
**Due date:** Use the date shown in the D2L Lab 3 assignment.
**Delivery:** Complete this lab remotely; follow the D2L instructions for the quiz and lab.

## What you will do

You will complete a small Python program that runs a fictional delivery-event file through three stages:

1. **Extract:** preserve a copy of the input and record its fingerprint.
2. **Transform:** validate rows, keep the newest repeated parcel record, and save rejected rows with reasons.
3. **Publish:** create a count summary and record the stage results in a run manifest.

You will run the same job twice, then practise a controlled failure and resume. You do not need a database, account, API key, online service, or software package beyond Python.

This 5% lab is one submission. The Part A (3%) and Part B (2%) rubric rows below are marking components, not separate D2L assignments. The data is fictional.

## Part 1 — Download the starter

1. Sign in to GitHub.
2. Open the private **AIDA_1145_Graded_Labs** repository.
3. Open `week-06`.
4. Open `lab-03-reproducible-delivery-pipeline`.
5. Download the complete folder to your computer. Keep the `data` and `outputs` folders in place.
6. Do not push work to the instructor repository. Your finished work goes into your own private AIDA 1145 repository.

## Part 2 — Open it in VS Code

1. Open VS Code.
2. Select **File → Open Folder**.
3. Select the downloaded `lab-03-reproducible-delivery-pipeline` folder.
4. Select **Terminal → New Terminal**.
5. Check the Explorer shows `starter_pipeline.py`, `data/delivery_events.csv`, and `decision_note_template.md`.

## Part 3 — Check Python and inspect the input

In the VS Code terminal, check Python:

**Windows:**

```powershell
py --version
```

**macOS:**

```bash
python3 --version
```

Python 3.11 or later is recommended. This lab uses only built-in Python modules, so you do not install packages.

Open `data/delivery_events.csv`. It contains fictional parcel events, including a repeated parcel ID, an invalid date, and a blank parcel ID. Do not change this source file.

## Part 4 — Complete TODOs 1–3: helper functions

Open `starter_pipeline.py`. Complete one TODO at a time and save the file.

1. **TODO 1 — file fingerprint:** read the file bytes, pass them to `hashlib.sha256(...)`, then return `.hexdigest()`. A checksum is a fingerprint used to notice a changed file.
2. **TODO 2 — paths:** create a folder for the run date under `work`. Return paths for `raw.csv`, `clean.csv`, `quarantine.csv`, `manifest.json`, and `outputs/delivery_summary.csv`.
3. **TODO 3 — manifest writer:** create the dated run folder if it does not exist. Save the manifest as indented JSON and end the file with a newline.

## Part 5 — Complete TODO 4: preserve the input

The `extract` stage must:

1. Calculate the SHA-256 fingerprint of the supplied `data/delivery_events.csv` file.
2. Make a byte-for-byte copy at the run's `raw.csv` path if no copy exists yet.
3. If `raw.csv` already exists, compare its fingerprint with the supplied source. If they differ, stop with a helpful `PipelineError`; do not silently overwrite the saved raw evidence.
4. Save the input fingerprint in the manifest.
5. Mark the extract stage `SUCCEEDED`.

## Part 6 — Complete TODO 5: validate and transform rows

Read `raw.csv` with Python's `csv.DictReader`. For each input record:

1. Add a `source_row` number. The header is line 1, so the first data row is line 2.
2. Check that `parcel_id` is not blank.
3. Check `event_date` using the exact `YYYY-MM-DD` format. A date such as `2026-10-42` is not valid.
4. Add a clear reason for every failed check. Do not delete a failed row; place it in the quarantine file with its reason.
5. For valid rows with the same `parcel_id`, keep the newest `source_updated_at`. If those timestamps are equal, keep the earlier source row. Put extra copies in the duplicate count or a separate duplicate file.
6. Write valid unique rows to `clean.csv` and rejected rows to `quarantine.csv`.
7. Record input, clean, quarantined, and duplicate-non-survivor counts in the manifest.
8. Calculate and store fingerprints for the clean and quarantine files.
9. Mark transform `SUCCEEDED`.

The following count equation must hold: `input = clean + quarantined + duplicate non-survivors`.

## Part 7 — Complete TODO 6: publish a summary

1. Before reading `clean.csv`, calculate its fingerprint.
2. Compare it with the clean-file fingerprint in the manifest.
3. If the fingerprints differ, stop. Do not publish a summary from an unexpected file.
4. Count clean parcels by `event_type`.
5. Write `outputs/delivery_summary.csv` with columns `event_type` and `parcel_count`.
6. Replace the output on each run; do not append another copy of the same totals.
7. Record the summary fingerprint and mark publish `SUCCEEDED`.

## Part 8 — Complete TODO 7: coordinate the run

The `run` function coordinates the stages. Implement both paths:

### Normal run

1. Validate that the run date uses `YYYY-MM-DD`.
2. Create a manifest with status `RUNNING` and all stages `PENDING`.
3. Run extract. Save the manifest.
4. Run transform. Save the manifest.
5. If the failure option was requested, mark the run and publish stage `FAILED`, save an explanatory error, write the manifest, then raise `PipelineError`.
6. Otherwise run publish, mark the run `SUCCEEDED`, save the manifest, and return it.
7. If any real error occurs, save `FAILED` and its explanation before stopping.

### Resume path

1. Open the existing manifest for the chosen date.
2. Resume only if the earlier run is `FAILED` and transform is `SUCCEEDED`.
3. Recalculate the clean file's fingerprint and compare it to the manifest.
4. If it does not match, stop with an error. Do not resume from changed evidence.
5. If it matches, run only the publish stage, update the manifest, and finish `SUCCEEDED`.

## Part 9 — Run and inspect the successful pipeline (Part A)

Run from the VS Code terminal in this lab folder.

**Windows:**

```powershell
py starter_pipeline.py --run-date 2026-10-10
```

**macOS:**

```bash
python3 starter_pipeline.py --run-date 2026-10-10
```

Open `work/2026-10-10/manifest.json` and confirm that all stages succeeded. Open `raw.csv`, `clean.csv`, `quarantine.csv`, and `outputs/delivery_summary.csv`. Confirm every quarantined row has a reason and the row-count equation balances. Record your observed counts in `decision_note.md`.

Run the same successful command a second time. Check that the summary has not grown by appending duplicate rows. Note what you compared.

## Part 10 — Practise a controlled failure and recovery (Part B)

First, make the program intentionally stop after transform.

**Windows:**

```powershell
py starter_pipeline.py --run-date 2026-10-10 --fail-after-transform
```

**macOS:**

```bash
python3 starter_pipeline.py --run-date 2026-10-10 --fail-after-transform
```

The command should display a failure message and exit with code 2. This is the planned test, not a bug. Open `manifest.json` and check that transform succeeded, publish failed, and the clean-file fingerprint is recorded.

Now resume from the verified clean file.

**Windows:**

```powershell
py starter_pipeline.py --run-date 2026-10-10 --resume
```

**macOS:**

```bash
python3 starter_pipeline.py --run-date 2026-10-10 --resume
```

Reopen the manifest. Record the final run and stage statuses in `decision_note.md`. Explain what the checksum check prevents.

## Part 11 — Finish the decision note

1. Copy `decision_note_template.md` and name the copy `decision_note.md`.
2. Open `decision_note.md` in VS Code.
3. Replace each prompt with your own short, clear answer.
4. Include the evidence you observed. Do not invent counts or claim a successful run if your manifest says `FAILED`.
5. State one limitation before similar code is used on real data.

## Part 12 — Final folder check

Your private-repository copy must include:

```text
lab-03-reproducible-delivery-pipeline/
├── README.md
├── starter_pipeline.py
├── decision_note_template.md
├── decision_note.md
├── data/delivery_events.csv
├── outputs/README.md
└── work/2026-10-10/
    ├── raw.csv
    ├── clean.csv
    ├── quarantine.csv
    ├── manifest.json
    └── outputs/delivery_summary.csv
```

The manifest must show the final recovered run as `SUCCEEDED`. Keep the source CSV unchanged.

## Part 13 — Push your one lab folder to your private repository

1. Open your own private AIDA 1145 repository folder in VS Code.
2. Copy `lab-03-reproducible-delivery-pipeline` into its `week-06` folder. Create `week-06` if it does not exist.
3. Select the **Source Control** icon on the left side of VS Code.
4. Check that the listed changes are your Lab 3 files.
5. Enter the commit message `Complete AIDA 1145 Lab 3`.
6. Select **Commit**.
7. Select **Sync Changes** or **Push**.
8. In a browser, open your private repository and confirm the Week 6 lab files are visible.

Alternatively, in the terminal opened in your private repository, run:

```powershell
git status
git add week-06/lab-03-reproducible-delivery-pipeline
git commit -m "Complete AIDA 1145 Lab 3"
git push
```

Never run these push commands in the instructor repository.

## Part 14 — Submit once in D2L

1. Open the **AIDA 1145 Lab 3** assignment in D2L.
2. Open the Week 6 lab folder in your private GitHub repository.
3. Copy that folder's browser address.
4. Paste the address into the D2L submission area and select **Submit**.
5. Confirm D2L shows the submission and that the link opens the correct folder.

Submit one link for the entire 5% lab. Part A and Part B are not separate submissions. Complete the quiz separately only if D2L shows it as a separate course assessment.

## Small rubric — 5% total

| Evidence | Weight |
|---|---:|
| Part A: extract/transform/publish stages, validation, outputs, and row reconciliation | 1.5% |
| Part A: manifest, fingerprints, successful run, and repeat-run evidence | 1.5% |
| Part B: controlled failure, safe resume, evidence-based note, and limitation | 2.0% |
| **Total, submitted once** | **5.0%** |

## Troubleshooting

- **`NotImplementedError`:** a TODO is not complete yet. Read its comment and the matching README part.
- **`FileNotFoundError`:** check that VS Code opened this lab folder and `delivery_events.csv` remains under `data`.
- **Failure command exits with code 2:** this is expected for `--fail-after-transform`.
- **Resume is refused:** verify the manifest records a failed run with transform successful and that `clean.csv` has not been changed.
- **Git push is rejected:** verify you copied into your private student repository and accepted its invitation.
- Include the exact command and full error when asking for help. Never share a token or password.
