
# Lab 6 — Depot Sensor Batch Decision Note

## Part A — Initial Batch

### Manager's question

Can Northbank Food Depot trust the initial sensor batch to provide a reliable temperature report for all five expected sensors?

### Batch results

The initial batch contained:

- Pages read: 2
- Pagination completed: Yes
- Delivered rows: 6
- Unique readings: 5
- Duplicate deliveries: 1
- Expected sensors: 5
- Sensors found: 5

### Data quality and coverage

- Source coverage: 5/5 = 100%
- Usable and fresh coverage: 3/5 = 60%
- Invalid readings: 1/5 = 20%
- Conflicting readings: 0
- Accepted rows: 3
- Quarantined rows: 2

Reading R02 was quarantined because its temperature was 55.0°C, outside the permitted range of -10°C to 30°C.

Reading R04 was quarantined because it was 20 minutes old, exceeding the 15-minute freshness limit.

The duplicate delivery of R03 was counted once because both copies contained identical information.

### Decision

**HOLD**

The initial batch must not be released as a trusted temperature report. Although source coverage was 100%, usable and fresh coverage was only 60%, below the required 95%. The invalid-reading rate was 20%, above the permitted 2%.

### Recommended next action

Investigate the invalid temperature reading and stale sensor reading. Request or wait for fresh sensor data, then process the retry batch before releasing the report.

## Part B — Retry Batch and Production Extension

### Retry results

The retry batch contained:

- Pages read: 2
- Pagination completed: Yes
- Delivered rows: 6
- Unique readings: 5
- Duplicate deliveries: 1
- Source coverage: 5/5 = 100%
- Usable and fresh coverage: 5/5 = 100%
- Invalid readings: 0/5 = 0%
- Conflicting readings: 0
- Accepted rows: 5
- Quarantined rows: 0

### Decision

**ACCEPT**

The retry batch passed the required checks. All five expected sensors provided valid and fresh readings. The invalid-reading rate was 0%, and usable and fresh coverage was 100%.

### Repeat-run test

I ran the Python program again without changing the input files.

The retry batch produced the same results:

- First run: 5 unique readings and 5 accepted rows.
- Second run: 5 unique readings and 5 accepted rows.

The accepted CSV still contained exactly 5 data rows. This confirms that the program safely overwrites the output files instead of appending duplicate records.

The initial batch results were also preserved after the retry run.

### Scheduled batch versus streaming

A scheduled batch process is suitable for producing a temperature report every 15 minutes. It collects readings over a period, processes them together, validates the data, removes duplicate deliveries, and produces a report.

For an alert required in less than one minute, a streaming approach would be more appropriate. Streaming processes incoming sensor readings continuously and can detect abnormal temperatures much faster.

One limitation of streaming is that it requires continuous processing and reliable connectivity. It also needs appropriate handling of duplicate, delayed, and out-of-order readings.

### Final recommendation

Use the scheduled batch pipeline for routine 15-minute temperature reports. Use a streaming system for urgent temperature alerts that require a response in less than one minute.

The retry batch is safe to accept based on the validation results.