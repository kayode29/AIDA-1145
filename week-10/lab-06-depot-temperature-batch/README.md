# AIDA 1145 — Week 10 Graded Lab 6: Depot Sensor Batch

**Topic:** APIs, batch processing, and streaming concepts  
**Value:** 5% of the course grade: Part A 3%, Part B 2%  
**Submission:** One completed lab folder in your assigned private course repository, with one link submitted in D2L. Use the deadline shown in D2L.

## What you will do

The fictional Northbank Food Depot has five temperature sensors. A manager wants a checked set of the latest readings for a report reviewed every 15 minutes. An API provides the readings in pages. Your job is to read the supplied example responses, check the data, and decide whether the batch is complete enough to release.

In **Part A**, you will write the processing logic for an initial batch and explain your result. In **Part B**, you will process a later retry batch, check that rerunning it does not create duplicates, and compare scheduled batch and streaming approaches. Both parts stay in this folder and form one submission.

This is a starter: the data and function structure are supplied; you write the processing logic and interpretation. The files simulate API responses. You do not need an internet connection, API account, database, or additional Python packages to run the lab.

## Files provided

| File or folder | Purpose |
|---|---|
| `data/expected_sensors.csv` | List of the five sensor IDs expected in each batch. |
| `data/initial/` | Two saved pages for Part A. |
| `data/retry/` | Two saved pages for Part B, collected later. |
| `src/starter.py` | Starter functions for your code. |
| `outputs/` | Save generated files here, in separate `initial` and `retry` folders. |
| `decision-note.md` | Prompts for your explanations in both parts. |
| `rubric.md` | The marking guide. |

## Set up

1. Pull or clone the private **AIDA 1145 Graded Labs** instructor repository. Copy `week-10/lab-06-depot-temperature-batch` into your assigned private AIDA 1145 student repository. Work in your own copy.
2. Open the copied lab folder in VS Code. Select **Terminal → New Terminal**. If the terminal is elsewhere, use `cd` to move to the lab folder.
3. Check Python with `python --version`. Use Python 3.10 or later. If your computer uses the Windows Python launcher, use `py -3` in place of `python` in the commands below.
4. Open `src/starter.py`, the two initial JSON files, and `data/expected_sensors.csv`. Read the rules below before writing code.
5. Run `python src/starter.py` after you begin completing the TODOs. The supplied starter raises `NotImplementedError` until you complete those sections; this is expected.

## Rules for this exercise

These rules are fictional teaching assumptions, not food-safety limits.

1. Each row is one sensor reading. `reading_id` identifies a reading; `sensor_id` identifies its sensor.
2. Start at `page_01.json`. A `next_cursor` of `page_02` points to `page_02.json`; `null` means the final page. If a cursor is unknown or repeated, stop and report that the batch is incomplete. Check that both pages have the same `retrieved_at` time.
3. Exact repeated rows with the same `reading_id` are duplicate deliveries: keep one copy and count each extra delivery. If the same ID has different content, record the conflict and HOLD the batch; do not silently select a version.
4. A valid reading has an expected sensor ID, a numeric `temperature_c` from **-10 through 30**, inclusive, and a valid UTC timestamp no later than `retrieved_at`. Treat a failed check as invalid. Keep the original row and a reason in the quarantine output; do not change the source data to make it pass.
5. Calculate age as `(retrieved_at - observed_at)` in minutes. A valid reading aged **15 minutes or less** is fresh. A valid reading older than 15 minutes is stale and belongs in quarantine. An invalid reading is counted as invalid even if it is also old; give its validation reason.
6. **Source coverage** is the number of distinct expected sensors present in unique readings, divided by 5. **Usable and fresh coverage** is the number of distinct expected sensors with at least one valid, fresh reading, divided by 5. Multiply each by 100 for a percentage.
7. **Invalid-reading rate** is the number of unique readings failing a value, ID, or timestamp check divided by the number of unique readings, multiplied by 100. Exact duplicate deliveries do not increase the denominator. Stale but otherwise valid readings are not invalid for this rate.
8. Release is **ACCEPT** only when pagination finishes, no conflicting IDs exist, usable and fresh coverage is at least 95%, and the invalid-reading rate is at most 2%. Otherwise use **HOLD**. If there are no unique readings, HOLD and record the invalid rate as `null` instead of dividing by zero.

For example, if a reading is observed at 13:45 and the batch is retrieved at 14:00, its age is 15 minutes and it passes the freshness boundary. A reading at 13:44 is 16 minutes old and is stale. Use the full date and UTC time in your code, not the minute portion alone.

## Part A — Guided in-class work (3%)

### Step 1: Inspect the inputs

1. Open the expected-sensor CSV and record how many sensor IDs are expected.
2. Open `data/initial/page_01.json` and `page_02.json`. Find `retrieved_at`, `items`, and `next_cursor` in each page.
3. In `decision-note.md`, state the manager's question and what one reading represents. Identify the repeated reading ID by inspecting the pages.

### Step 2: Follow the pages

1. In `src/starter.py`, complete `read_pages(batch_dir)`. Read the first page, follow its cursor, and combine the `items` lists in delivery order.
2. Return three values: the combined list, the common `retrieved_at` value, and the number of pages read. If the cursor is repeated or unknown, or the retrieval times disagree, raise a clear error and do not report the batch as complete.
3. Print the number of pages and delivered rows so you can check the run. Do not change the JSON files.

### Step 3: Check and classify the readings

1. Complete `process(readings, retrieved_at, expected)`. Keep one copy of each exact `reading_id` and count extra deliveries. Check for a conflicting ID before removing duplicates.
2. Apply rules 4 and 5 to each unique reading. Keep valid, fresh readings in an accepted list. Put invalid and stale readings in a separate quarantine list with a clear reason.
3. Calculate source coverage, usable and fresh coverage, and invalid-reading rate using the rules above. Count distinct sensors for coverage and unique readings for the invalid rate.
4. Apply the release rules and return the lists, counts, percentages, and ACCEPT or HOLD decision to `run_batch`.

### Step 4: Save and inspect the initial result

Complete `run_batch('initial')` and run `python src/starter.py`. Create these files:

| File | Required contents |
|---|---|
| `outputs/initial/accepted.csv` | `reading_id`, `sensor_id`, `observed_at`, `temperature_c`, `age_minutes` for each accepted reading. |
| `outputs/initial/quarantine.csv` | The same fields plus `reason` for each invalid or stale reading. If timestamp parsing fails, leave `age_minutes` blank and state why in `reason`. |
| `outputs/initial/summary.json` | Pages read, delivered row count, unique reading count, duplicate delivery count, expected sensor count, source coverage %, usable and fresh coverage %, invalid rate %, pagination completion, conflict count, and decision. Use clear field names. |

Open each output. Confirm every unique reading is accounted for in accepted or quarantine, and explain any conflict separately. Check one age calculation by hand. In `decision-note.md`, complete all Part A prompts using your own results and the release rules. Do not interpret the temperature range as proof that food is safe.

## Part B — Independent extension (2%)

1. Preserve `outputs/initial/`. Add `run_batch('retry')` to the program and run the retry data through the **same** rules. Save `accepted.csv`, `quarantine.csv`, and `summary.json` under `outputs/retry/`, with the same columns and measures as Part A.
2. Run the program again without changing the inputs. Record the unique reading count and accepted-row count from both retry runs in `decision-note.md`. Explain why an output that appends another copy on each run would be misleading. Your rerun must produce the same counts and must not add duplicate rows; overwriting a batch's generated report is acceptable.
3. Compare initial and retry results in the decision note. State which gates passed or failed in each batch and whether the decision changed. Cite the percentages you calculated.
4. Answer the two processing-choice prompts in the decision note. Explain why an API is the way data is requested, while batch and streaming describe when data is processed. Describe one limitation of the streaming option you suggest.

## Before you submit

- [ ] `src/starter.py` contains your runnable code for both batches.
- [ ] `outputs/initial/` and `outputs/retry/` each contain the three named files. Initial outputs remain available after the retry run.
- [ ] `decision-note.md` contains the calculations, decisions, rerun check, and Part B comparison.
- [ ] You have not altered the supplied input files or included `.venv`, credentials, or unrelated work.

In a terminal opened in your copied lab folder, run:

```text
git status
git add -- .
git status
git commit -m "Complete Lab 6 sensor batch analysis"
git push
```

Check the second `git status` to make sure only your intended lab files are staged. If Git says the branch has no upstream, follow the `git push --set-upstream` command it displays. Check your files on GitHub, then submit **one link to the lab folder in your assigned private repository** in the D2L Lab 6 assignment. Parts A and B are not separate submissions. Ask the instructor for help if your repository link cannot be accessed.

## If you get stuck

- **File not found:** Check the folder name and run the command from the copied lab folder. The starter uses paths relative to its own location.
- **Time error:** The timestamps end in `Z`, meaning UTC. For Python 3.10, `datetime.fromisoformat(value.replace('Z', '+00:00'))` parses these supplied timestamps. Parse both timestamps as UTC before subtracting them; compare the full date and time.
- **Duplicate totals look wrong:** Compare complete rows with the same `reading_id` before counting a delivery as an exact duplicate.
- **A percentage is unexpected:** Write down its numerator and denominator. Source coverage and usable coverage answer different questions.
- **A page cannot be followed:** Report the cursor problem. Do not label a partial batch complete.

See `rubric.md` for how the work is assessed.
