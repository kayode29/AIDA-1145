# AIDA 1145 — Week 5 Graded Lab 2: Clean Donation Pickup Records

**Topic:** Data profiling, cleaning, and transformation
**Value:** 5% total — one lab, one private-repository push, one D2L submission
**Tools:** VS Code, Python 3.11+, pandas
**Due date:** Use the date shown in the D2L Lab 2 assignment.

## Your task

A fictional food-support organization receives donation pickup records. You will write and run a small Python program that checks the rows, keeps usable records, saves records needing correction with reasons, and identifies an extra copy of a repeated donation ID.

This lab has two marking parts, but they are submitted together in one folder:

- **Part A (3%):** build the cleaning program and show its baseline outputs.
- **Part B (2%):** compare two reasonable policies for a missing pickup site and explain which you recommend.

The values are fictional teaching data. Do not add real personal or sensitive information.

## Part 1 — Download the starter folder

1. Sign in to GitHub with the account you use for AIDA 1145.
2. Open the private **AIDA_1145_Graded_Labs** repository.
3. Open `week-05`.
4. Open `lab-02-cleaning-donation-records`.
5. Download this complete folder to your computer. Keep its internal folders together.
6. Do not edit or push to the instructor repository. Your finished work goes in your own private AIDA 1145 repository.

## Part 2 — Open your copy in VS Code

1. Open VS Code.
2. Select **File → Open Folder**.
3. Choose the downloaded `lab-02-cleaning-donation-records` folder.
4. Select **Terminal → New Terminal**. A command area appears at the bottom.
5. In the Explorer file list, confirm that you can see `starter_cleaning.py`, `requirements.txt`, and the `data` folder.

## Part 3 — Prepare Python

Check Python in the VS Code terminal.

**Windows:**

```powershell
py --version
```

**macOS:**

```bash
python3 --version
```

You need Python 3.11 or newer. Create a private environment for this lab.

**Windows:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

When activated, the terminal usually shows `(.venv)`. Install the package listed in `requirements.txt`:

**Windows:**

```powershell
py -m pip install -r requirements.txt
```

**macOS:**

```bash
python3 -m pip install -r requirements.txt
```

## Part 4 — Inspect the supplied data

1. In VS Code, open `data/donation_pickups.csv`.
2. Read the first row. It contains the column names.
3. Each later line is one incoming record.
4. Notice that the file includes examples of an invalid date, an unknown status, a missing pickup site, a negative quantity, and a repeated donation ID.
5. Open `decision_note_template.md`. You will complete this at the end.

## Part 5 — Complete the starter code (Part A)

Open `starter_cleaning.py`. Complete the TODOs from top to bottom. Save the file after each small change.

1. **Read the file:** use `pd.read_csv` with `dtype="string"` and `keep_default_na=False`. This keeps the original values as text and makes blank cells easy to detect.
2. **Keep row evidence:** add a `source_row` number starting at 2 because line 1 is the CSV header.
3. **Check each record:** for every row, check for a missing donation ID, a real `YYYY-MM-DD` date, a known status, and a whole-number quantity greater than zero.
4. **Use reason codes:** examples include `MISSING_DONATION_ID`, `INVALID_DATE`, `UNMAPPED_STATUS`, and `INVALID_QUANTITY`. A row may have more than one reason.
5. **Standardize known statuses:** use the supplied `STATUS_MAP`. Do not invent a replacement for an unknown status.
6. **Apply the baseline site rule:** when `site_policy` is `flag`, keep a row with no pickup site if its other required values are valid, and mark its site quality as `missing`.
7. **Separate rows:** rows with a required-field reason go to the rejected output; valid rows continue to the duplicate check.
8. **Choose a duplicate survivor:** for repeated `donation_id` values, keep the row with the newest `source_updated_at`. If timestamps tie, keep the earlier source row. Save extra copies separately.
9. **Write the baseline output:** create the output directory if needed, then save the clean rows, rejected rows, duplicate rows, and a summary JSON.
10. **Check the summary:** include `input_rows`, `clean_rows`, `rejected_rows`, `duplicate_non_survivors`, and `site_policy`.

Run the baseline after completing the TODOs:

**Windows:**

```powershell
py starter_cleaning.py --site-policy flag --output outputs/baseline
```

**macOS:**

```bash
python3 starter_cleaning.py --site-policy flag --output outputs/baseline
```

If you see `NotImplementedError`, at least one TODO is still incomplete. If you see a different error, read its last line first; it usually names the issue.

## Part 6 — Review your baseline evidence

Open the files created inside `outputs/baseline`:

- `clean_pickups.csv` — valid records after status cleanup and duplicate handling;
- `rejected_pickups.csv` — records that failed required checks, with reasons;
- `duplicate_rows.csv` — extra copies not selected as the survivor; and
- `summary.json` — counts for this run.

Check that:

1. The repeated donation ID has only one row in `clean_pickups.csv`.
2. The chosen row is the most recently updated copy.
3. Every rejected row has a reason.
4. A missing site is labelled `missing` in the baseline instead of being silently removed.
5. The count equation holds: `input_rows = clean_rows + rejected_rows + duplicate_non_survivors`.

## Part 7 — Compare a second missing-site policy (Part B)

The second policy treats a missing pickup site as a reason to reject the row. This is a policy comparison, not a change to the original input file.

1. Run the same program with `site_policy` set to `reject` and use a different output folder.

   **Windows:**

   ```powershell
   py starter_cleaning.py --site-policy reject --output outputs/reject-missing-site
   ```

   **macOS:**

   ```bash
   python3 starter_cleaning.py --site-policy reject --output outputs/reject-missing-site
   ```

2. Confirm that this run creates its own four output files.
3. Compare `outputs/baseline/summary.json` with `outputs/reject-missing-site/summary.json`.
4. Identify the donation ID affected by this rule change.
5. Complete `decision_note.md` using `decision_note_template.md` as a guide. State your policy, evidence, recommendation, and one limitation.

Do not overwrite the baseline results. Both policy runs are required evidence.

## Part 8 — Final folder check

Your submitted folder must contain:

```text
lab-02-cleaning-donation-records/
├── README.md
├── starter_cleaning.py
├── requirements.txt
├── decision_note.md
├── data/donation_pickups.csv
└── outputs/
    ├── baseline/
    │   ├── clean_pickups.csv
    │   ├── rejected_pickups.csv
    │   ├── duplicate_rows.csv
    │   └── summary.json
    └── reject-missing-site/
        ├── clean_pickups.csv
        ├── rejected_pickups.csv
        ├── duplicate_rows.csv
        └── summary.json
```

Also confirm that `decision_note.md` is completed and that the input CSV has not been changed.

## Part 9 — Save and push to your private student repository

1. Open your assigned private AIDA 1145 repository folder in VS Code. This is the repository where you have write access.
2. Copy the completed `lab-02-cleaning-donation-records` folder into `week-05` in your private repository. Create `week-05` if needed.
3. In VS Code, select the **Source Control** icon on the left. It looks like a branch.
4. Review the changed files. Make sure they are your Lab 2 files.
5. Enter a message such as `Complete AIDA 1145 Lab 2`.
6. Select **Commit**.
7. Select **Sync Changes** or **Push**.
8. Open your private repository in a browser and confirm the Lab 2 files are visible.

If using a terminal instead, open it in your private student-repository folder and run:

```powershell
git status
git add week-05/lab-02-cleaning-donation-records
git commit -m "Complete AIDA 1145 Lab 2"
git push
```

If Git says there is nothing to commit, check that you copied the folder into your private repository and saved your changes. Never run `git push` from the instructor repository.

## Part 10 — Submit once in D2L

1. Open the **AIDA 1145 Lab 2** assignment in D2L.
2. In GitHub, open your private repository and navigate to `week-05/lab-02-cleaning-donation-records`.
3. Copy the browser address for that folder.
4. Return to the D2L assignment and paste the link into the submission area.
5. Select **Submit**.
6. Check that D2L confirms your submission and that the link opens your Lab 2 folder.

Submit **one link** for the complete lab. Part A and Part B are components of one 5% lab, not two assignments.

## Rubric — 5% total

| Evidence | Weight |
|---|---:|
| Part A: required checks, status cleanup, row reasons, and deterministic duplicate handling | 1.5% |
| Part A: correct outputs, summary, row reconciliation, and traceable source rows | 1.5% |
| Part B: both site-policy runs, evidence-based comparison, recommendation, and limitation | 2.0% |
| **Total, submitted once** | **5.0%** |

## Help

- **`ModuleNotFoundError: pandas`:** activate `.venv`, then repeat the install command.
- **`NotImplementedError`:** return to `starter_cleaning.py` and complete the TODOs.
- **`FileNotFoundError`:** confirm VS Code is open to the lab folder and the CSV remains in `data`.
- **Git push fails:** confirm you are in your private student repository and have accepted the organization invitation.
- When asking for help, include the command and full error text. Never send a password or GitHub token.
