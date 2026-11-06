# AIDA 1145 Week 10 Practice Lab 6: API Ingestion, Batch Processing, and Streaming Decisions

**Status:** Fully worked, ungraded practice lab
**Business case:** Harbourline Bike Share must decide whether its scheduled station-status batch is reliable enough for an operations dashboard.
**Tools:** Python 3.10 or later and the Python standard library. No package installation, internet connection, live API account, credential, or database is required.

## What you will learn

By working through this example, you will learn how to:

1. Explain the difference between an API (a way to request data) and a processing pattern (when and how the data is processed).
2. Follow API pagination until the source signals that there are no more pages.
3. Preserve a source response while validating the records it contains;
4. identify repeated records and make a batch safe to rerun;
5. calculate observation age, source coverage, usable coverage, and invalid-record rate;
6. apply a clear release rule and explain the evidence behind an ACCEPT or HOLD decision; and
7. choose between scheduled batch processing and streaming based on the business response time.

This is a worked example. The solution is included so you can read, run, compare, and learn from the complete process. Do not treat an ACCEPT result in any practice lab as proof that the design is ready for a real public service.

This practice lab is ungraded and has no D2L submission. Keep your changes in your own copy. Do not commit or push to this instructor example repository. If your instructor asks you to save practice work in Git, copy your completed folder into your assigned private AIDA 1145 student repository and push it there.

## Business request

Harbourline Bike Share operates five stations. Its operations team wants a station-availability snapshot every 15 minutes. The dashboard is used to plan staff rebalancing before the next reporting interval. The API returns a page of observations and may return a cursor that points to another page.

The operations manager asks:

> “Can I use this 10:00 a.m. snapshot to make a complete station-rebalancing plan?”

For this classroom decision, the approved rules are:

| Rule | Meaning |
|---|---|
| Expected station list | All five station IDs in `data/expected_stations.csv` should appear in the source batch. |
| Pagination | Follow each `next_cursor`; a batch is complete only when the cursor is `null`. |
| Record identity | `observation_id` identifies one observation. An exact repeated observation is one duplicate delivery, not a second event. |
| Value checks | Bike counts must be whole numbers, at least zero, and no greater than a positive dock capacity. |
| Freshness | An observation no more than 15 minutes old is acceptable. Exactly 15 minutes old passes; more than 15 minutes fails. |
| Release gate: coverage | At least 95% of expected stations must have a valid and fresh observation. |
| Release gate: invalid rate | No more than 2% of unique observations may fail value validation. |
| Decision | Release only if pagination is complete and every release gate passes. Otherwise, hold the snapshot and investigate. |

These thresholds are explicit teaching assumptions for the fictional case. A real organization must have its business owner approve its service levels and release rules.

## Important distinction: API, batch, and streaming

An **API** is an interface a program can use to request data. **Batch processing** collects and processes a group of records at an agreed time or interval. **Streaming** processes events continuously or soon after they arrive.

These ideas describe different parts of a design. A scheduled job can call an API every 15 minutes and process each response as a batch. The fact that the data came from an API does not, by itself, make the job a streaming system.

| Business need | Likely fit | Why |
|---|---|---|
| Staff make a station plan every 15 minutes | Scheduled API batch | A complete, checked snapshot is available at each agreed interval. |
| A safety team must be notified seconds after a dangerous event | Streaming or event-driven processing | Waiting for the next 15-minute batch could be too slow. |
| A catalogue changes a few times a day and is used each morning | Scheduled batch | Immediate processing adds complexity without meeting a stated need. |

The right choice depends on the required response time, acceptable data age, source limits, operating cost, and consequences of a late or incorrect result. Faster processing is not automatically better if the source data is still delayed or untrustworthy.

## Package map

- `data/expected_stations.csv` — the approved list of stations that should be represented.
- `data/api_page_01.json` and `data/api_page_02.json` — saved example API responses. They make the activity reproducible without making a live request.
- `run_lab.py` — complete solution: reads both pages, validates and classifies observations, applies release gates, and writes reports.
- `outputs/accepted_observations.csv` — records that pass value and freshness checks.
- `outputs/quarantine.csv` — records held for a specific reason; the source files remain unchanged.
- `outputs/release_gates.csv` — one row per release rule, with its observed result and pass/fail status.
- `outputs/retry_policy_examples.csv` — sample retry decisions for HTTP responses.
- `outputs/run_summary.json` — the key batch counts, percentages, and overall decision.
- `decision_note.md` — a completed evidence-based business note for this data.

Generated files are included so you can compare them with a fresh run. Running `run_lab.py` rewrites the output files using the supplied data.

## Step 1 — Open the lab and check Python

1. Download or clone the instructor's AIDA 1145 Practical Lab Examples repository, then open the `week-10/practice-lab-06-api-batch-streaming` folder in VS Code.
2. In VS Code, choose **Terminal → New Terminal**. The terminal should be open in this lab folder.
3. Check that Python is available:

   ```text
   py --version
   ```

   If your computer does not recognize `py`, try:

   ```text
   python --version
   ```

4. Use Python 3.10 or later. This lab uses only built-in modules, so you do not need to install `requests`, `pandas`, or any other package.

If the terminal opens in a different folder, use `cd` to move into `practice-lab-06-api-batch-streaming` before running the commands. The path displayed by the terminal should end with that folder name.

## Step 2 — Inspect the inputs before running the solution

Open `data/expected_stations.csv`. It lists five station IDs. This is the reference list used to assess source coverage.

Next, inspect both JSON files. Each response has three parts:

- `retrieved_at` — the time this batch was collected;
- `items` — the observations in this page; and
- `next_cursor` — a pointer to another page, or `null` when there are no more pages.

The first page ends with `"next_cursor": "page-02"`. The second page ends with `"next_cursor": null`. The same observation, `OBS-1003`, appears at the end of page 1 and the beginning of page 2. This represents a common page-boundary overlap. The stable `observation_id` lets the code identify the repeated delivery.

Before running the code, predict:

1. How many raw rows will the two pages deliver in total?
2. How many unique observation IDs should remain after exact duplicate handling?
3. Is a record with 13 bikes available at a station with capacity 10 plausible?
4. Is an observation from 9:45 a.m. fresh enough at 10:00 a.m. under the inclusive 15-minute rule?
5. Will every station have a valid **and fresh** record, even if every station ID appears in the input?

## Step 3 — Run the complete worked pipeline

In the terminal, run:

```text
py run_lab.py
```

If `py` is not available, run:

```text
python run_lab.py
```

The program should print a summary similar to this:

```text
Harbourline Bike Share API batch summary
Pages read: 2; pagination complete: True
Records received: 6; unique observations: 5; duplicate deliveries ignored: 1
Expected station source coverage: 100.0% (5/5)
Usable and fresh coverage: 60.0% (3/5)
Invalid rate: 20.0% (1/5); stale observations: 1
Idempotency check: unique keys remain 5 after a simulated rerun
Release decision: HOLD
Open outputs/ to inspect the accepted rows, quarantine, gates, retry examples, and run summary.
```

The result is intentionally not a clean ACCEPT. A strong data workflow makes defects visible and gives a decision-maker enough evidence to act. Do not alter the sample to force an ACCEPT.

## Step 4 — Follow how pagination works

The function `retrieve_all_pages()` begins with `api_page_01.json`. It then:

1. reads the page's records;
2. reads `next_cursor`;
3. uses the cursor-to-file mapping in `CURSOR_TO_FILE` to load page 2;
4. repeats the process; and
5. stops only when `next_cursor` is `null`.

The local file mapping simulates the response a real API client would request. In a live service, the program would send the cursor in its next request. The important logic is the same: do not treat a successful first-page response as proof that the full result was retrieved.

The code also protects against a repeated cursor and an unknown cursor. A repeated cursor could make a client loop forever; an unknown cursor means the client cannot prove it reached the end. Either condition stops the run rather than quietly reporting a partial batch as complete.

## Step 5 — Understand the validation and duplicate rules

The program builds a dictionary keyed by `observation_id`. When the same ID and all the same fields appear again, it records one duplicate delivery and keeps one copy. This is useful when pages overlap or when a batch is repeated after a temporary failure.

The unique observation is checked for:

- a known station ID;
- integer bike and dock counts;
- a non-negative bike count;
- a positive dock capacity;
- bikes available not exceeding capacity; and
- a parseable observation timestamp that is not in the future.

The record with 13 bikes available and capacity 10 fails the value rule. The code does not change 13 to 10, because that would invent a source value. It keeps the record in `outputs/quarantine.csv` with the reason `AVAILABLE_EXCEEDS_CAPACITY`.

An exact duplicate does not add a second station observation. If the same ID arrived with different values, a robust workflow would not choose one silently; this solution classifies conflicting IDs as a data issue and holds them.

## Step 6 — Calculate data age and understand the inclusive boundary

Data age is the difference between the time the API response was retrieved and the time the station observation was recorded:

```text
age in minutes = (retrieved_at − observed_at) in seconds ÷ 60
```

For `OBS-1005`:

```text
retrieved_at = 10:00 a.m.
observed_at  =  9:45 a.m.
age          = 15 minutes
```

Because the rule says **no more than 15 minutes**, this record passes. The comparison in the code is `age_minutes > 15`, not `age_minutes >= 15`.

For `OBS-1004`:

```text
retrieved_at = 10:00 a.m.
observed_at  =  9:40 a.m.
age          = 20 minutes
```

This record is too old for the dashboard snapshot, so it is quarantined as `STALE_OBSERVATION`. It may still be useful as historical evidence, but it should not be presented as the current station state.

## Step 7 — Read the output tables and calculate the measures

Open `outputs/accepted_observations.csv`. It should contain three stations: ST-01, ST-03, and ST-05. The availability percentage is:

```text
station availability percentage = bikes_available ÷ dock_capacity × 100
```

For ST-03:

```text
6 bikes ÷ 10 docks × 100 = 60.0%
```

The accepted output should show ST-01 at 33.3%, ST-03 at 60.0%, and ST-05 at 33.3%. A percentage helps compare stations with different capacities, but it does not replace the underlying counts. A station at 60% capacity with 6 bikes is not the same absolute inventory as a much larger station at 60%.

Open `outputs/quarantine.csv`. It should show:

| Observation | Issue | Why it is not used as the current dashboard value |
|---|---|---|
| OBS-1002 | `AVAILABLE_EXCEEDS_CAPACITY` | 13 available bikes cannot fit in a 10-dock station under the stated rule. |
| OBS-1004 | `STALE_OBSERVATION` | Its observation is 20 minutes old, beyond the 15-minute limit. |

The source response files remain unchanged. Quarantine is a separate review output; it does not mean that the original evidence was deleted.

## Step 8 — Separate source coverage from usable coverage

Two percentages answer different questions.

**Source coverage** asks whether an expected station ID appeared in the unique source observations:

```text
source coverage = distinct expected station IDs received ÷ expected station count × 100
                = 5 ÷ 5 × 100
                = 100%
```

**Usable and fresh coverage** asks how many expected stations have a record that also passes validation and the freshness rule:

```text
usable fresh coverage = distinct stations with valid, fresh observations ÷ expected station count × 100
                      = 3 ÷ 5 × 100
                      = 60%
```

All station IDs arrived, but two of their readings cannot be used as current operational values. Reporting only 100% source coverage would hide the actual business limitation.

The invalid-record rate is:

```text
invalid rate = unique observations that fail value validation ÷ unique observations × 100
             = 1 ÷ 5 × 100
             = 20%
```

The exact repeated `OBS-1003` is not counted twice in the denominator. The stale record is counted in usable coverage but not as a value-validation error; it fails a different quality check. Keeping the measures separate makes the reason for each failure clear.

## Step 9 — Understand the idempotent rerun

An **idempotent** batch can be run again without creating extra copies of the same business event. In this example, the stable `observation_id` is the key. The code simulates processing the unique keys twice:

```text
unique observation keys after the first run  = 5
unique observation keys after a simulated rerun = 5
```

The same records remain one observation each. In a production warehouse, a database `UPSERT` or an equivalent merge on a stable key can implement this behavior. Appending every retry to a table without a stable key could inflate counts and distort station or event totals.

## Step 10 — Read the retry examples

Open `outputs/retry_policy_examples.csv`. It demonstrates response handling without contacting an API or actually waiting:

| Response | Sensible action in this example |
|---|---|
| HTTP 503 with `Retry-After: 60` | Wait the requested 60 seconds, then retry within the attempt limit. |
| HTTP 429 with `Retry-After: 30` | Respect the rate-limit wait; reduce request pressure and retry within the limit. |
| HTTP 503 without `Retry-After`, third retry | Use bounded exponential backoff: `min(cap, base × 2^(retry number − 1))`. With base 2 and retry 3, wait `min(60, 2 × 2^2) = 8` seconds. |
| HTTP 401 | Stop and check the credential securely. Repeating the same unauthorized request will not repair an expired or incorrect credential. |

Retries need a limit. Unbounded retries can overload a source and keep a failed job running indefinitely. A live service may also add random **jitter** to spread out retries from many clients. Never print or commit access tokens, passwords, or secret keys.

## Step 11 — Apply the release gates

Open `outputs/release_gates.csv`. The batch meets the pagination and source-coverage rules. It fails the two quality gates:

| Gate | Observed | Rule | Result |
|---|---:|---:|---|
| Pagination reached a terminal cursor | True | Must be true | Pass |
| Expected station source coverage | 100.0% | At least 95% | Pass |
| Usable and fresh station coverage | 60.0% | At least 95% | Fail |
| Invalid-record rate | 20.0% | At most 2% | Fail |

The decision is **HOLD** because release requires every gate to pass. This is not a judgment that the API is useless. It is a conclusion that this particular batch does not meet the stated requirements for a complete current dashboard.

## Step 12 — Write the business conclusion

Read `decision_note.md`. A useful decision note answers four things:

1. What action is recommended?
2. Which measured evidence supports that action?
3. What should the operations team do next?
4. What is not known from this small batch?

For this run, keep the source evidence, publish a HOLD status to the operator, investigate the impossible count for ST-02, and request a fresh reading for ST-04. Do not silently change 13 bikes to 10. Do not present a 20-minute-old observation as current. The team can use the three passing station values with clear labels only if the dashboard's owner has approved a partial-view workflow; this lab's release rule does not authorize describing the full snapshot as complete.

## Step 13 — Change one assumption and reason about the result

Make a copy of the lab folder before experimenting so that you can restore the supplied answer. Then try one change at a time:

1. **Pagination check:** Change page 1's cursor to an unknown value. Rerun. Explain why the program stops instead of calling the batch complete.
2. **Freshness boundary:** Change `OBS-1004` from 9:40 to 9:45. Rerun. It should pass the inclusive 15-minute check if its values still pass.
3. **Value validation:** Change ST-02's available bikes from 13 to 9. Rerun. Explain which quality gate changes and why.
4. **Required station list:** Remove ST-05 from the source pages (in a copy). Explain the difference between source coverage and usable coverage.
5. **Release policy:** Consider whether a business owner should allow partial station coverage. State a numeric threshold, the user who approves it, the operational consequence, and how the dashboard must label unavailable values.

After each change, rerun `py run_lab.py` and compare the output files. Do not change a quality threshold merely to make the sample pass; a threshold must come from an approved business requirement.

## Step 14 — Connect batch processing to streaming

Draw or write the two flows below and identify where validation and monitoring occur.

**Scheduled batch**

```text
Every 15 minutes → call API → follow all pages → validate → deduplicate → apply release gates → update dashboard
```

**Streaming or event-driven design**

```text
New event arrives → validate the event → update station state → monitor event delay → alert an operator when a rule is met
```

For this fictional planning workflow, the 15-minute batch fits the stated interval if its data passes the gates. For a seconds-level safety alert, a 15-minute schedule could be too slow; a streaming design may fit better, but it still needs validation, monitoring, retry handling, and a safe response plan.

An observation can arrive late even in a streaming system. A production design should preserve both **event time** (when the station reading happened) and **processing time** (when the system received it). Otherwise, a delayed old reading could appear to be a new one simply because it just arrived.

## Step 15 — Beginner glossary

| Term | Plain-language meaning in this lab |
|---|---|
| API | A defined way for one program to request data from another program. |
| Batch | A group of records collected and processed together at a planned interval. |
| Streaming | A design that processes events continuously or soon after they arrive. |
| Page | One portion of a larger API result. |
| Cursor | A value that tells the client how to request the next page. |
| Observation | A measurement of one station's state at one time. |
| Duplicate delivery | The same source observation arriving more than once. |
| Idempotent | Safe to run again without adding a second copy of the same event. |
| Quarantine | A separate holding area for a record that needs investigation. |
| Freshness | How much time has passed since the source observation was made. |
| Coverage | The share of expected stations represented in the data. Always state which kind of coverage you mean. |
| Release gate | A rule that must pass before a report is described as ready for its intended use. |
| Retry-After | A server response hint that tells a client when it may try again. |
| Exponential backoff | A retry delay that grows after each failed attempt, subject to a maximum. |

## Reflection questions

Answer each question using at least one specific input, output, formula, code behavior, or business rule from the lab.

1. Why does using an API not automatically mean that a system is streaming? Identify the interface and the processing cadence in this case.
2. What evidence proves that the two-page response is complete? What does the code do if the cursor is unknown or repeats?
3. How many raw records arrived, how many unique observations remained, and why are those counts different?
4. Why does a stable observation ID help when a batch is retried after a temporary failure?
5. Calculate the age of `OBS-1005`. Why does the inclusive wording “no more than 15 minutes” allow it to pass?
6. Why should `OBS-1002` be quarantined rather than silently changed from 13 bikes to 10?
7. Explain why source coverage is 100% but usable and fresh coverage is only 60%.
8. What are the numerator and denominator of the invalid rate in this run? Why is the repeated delivery excluded from the denominator?
9. Which release gates pass and fail? How does the “all gates must pass” rule produce HOLD?
10. A manager proposes displaying ST-04's 20-minute-old value as if it were current. What risk does that create, and what clear label or alternative would you recommend?
11. When would the 15-minute batch be preferable to streaming? Give a business reason related to response time, operational cost, or source constraints.
12. Describe a business case where waiting for the next batch would be too slow. What extra monitoring and response safeguards would that streaming workflow require?
13. If HTTP 429 returns `Retry-After: 30`, why should the client not immediately retry? What could happen with unbounded retries?
14. Why is HTTP 401 handled differently from HTTP 503? What secure action should an operator take?
15. If the business owner changes the usable-coverage threshold from 95% to 60%, should the system automatically treat this run as safe? Explain what else must be approved and communicated.

## Model decision

The sample's completed decision is in `decision_note.md`. Compare your reasoning with the note after you have read the output files. A different conclusion is acceptable only if you clearly identify a changed, approved business rule and explain how the evidence supports it.

## Limits and responsible use

The saved JSON files simulate API pages; they are not a live connection and contain no real public-service data. The retry table demonstrates decisions but does not make network calls, wait, authenticate, or guarantee that the source will recover. The release thresholds are fictional classroom rules. A real deployment needs an approved data owner, authenticated and protected credentials, a documented source contract, rate-limit controls, monitoring, audit logs, privacy and security review, and a recovery plan. The HOLD conclusion applies only to this sample and its stated checks.
