# AIDA 1145 - Graded Lab 8
# Part A: Technical Solution Proposal

## Can Regional Service Revenue Be Trusted?

### 1. Proposed analytical pipeline

The solution will use Python 3 to validate, process, reconcile, and report field-service revenue using CSV inputs.

Processing flow:

Source Inputs -> Validation -> Canonicalization -> Effective-Date Matching -> Reconciliation -> Release Gate -> Regional Report.

| Stage | Input | Processing | Output |
|---|---|---|---|
| Source inputs | Service entries and site history CSV files | Load source records | Loaded records |
| Validation | Loaded records | Check columns, IDs, dates, units and prices | Valid records and error diagnostics |
| Canonicalization | Valid entries | Identify identical retransmissions and conflicting IDs | Canonical entries and replay records |
| Effective-date matching | Canonical entries and history | Match by site and service date | Match counts and diagnostics |
| Reconciliation | Canonical entries and matched records | Compare fact count and revenue | Reconciliation evidence |
| Release gate | Validation and matching results | Determine PASS or HOLD | Release decision |
| Reporting | Reconciled facts from passing run | Aggregate regional results | Fact table and regional report |

A held run will retain diagnostics and a summary but will not produce a released fact table or regional report.

### 2. Grain, keys and business rules

The fact table grain is one distinct service entry.

The primary key is entry_id. Work_order is not the primary key because one work order can contain multiple entries at different sites or regions.

Required fields include entry_id, work_order, service_date, site_id, units and unit_cents.

Revenue formula:

entry_cents = units * unit_cents

Revenue will be stored as integer cents to avoid floating-point errors.

#### Retransmission and conflict detection

Records will be grouped by entry_id.

- Identical records with the same ID: retain the first as canonical and classify later copies as retransmissions.
- Same ID with different values: classify the conflicting row as a source error and hold the batch.

Row accounting:

Input rows = Canonical entries + Identical retransmissions + Source-error rows.

### 3. Effective-date matching

Every canonical entry must match exactly one site-history row.

Matching requires:

- Matching site_id.
- service_date >= valid_from.
- service_date < valid_to.

The interval is half-open: [valid_from, valid_to).

The start date is inclusive and the end date is exclusive.

The program will identify match counts before aggregation:

- Zero matches: missing reference history.
- One match: valid reference assignment.
- More than one match: ambiguous or overlapping reference history.

Missing and ambiguous matches will remain visible in diagnostics. An ordinary inner join will not be used as the release validation method because it can discard missing entries and duplicate ambiguous entries.

### 4. Test plan

| Test | Input or change | Expected behaviour | Evidence |
|---|---|---|---|
| Identical replay | Repeat E02 with identical values | One canonical entry and one retransmission | Summary and replay diagnostics |
| Conflicting ID | Change a field in a second E02 | Classify conflict and HOLD | Error CSV and summary |
| Overlapping history | Candidate S2 intervals on November 15 | E03 has multiple matches; HOLD | Match diagnostics |
| Missing history | Candidate S3 begins November 16 | E04 has zero matches; HOLD | Match diagnostics |
| Date boundary | S2 entry dated November 10 | Maps to West, not East | Boundary test evidence |
| Corrected run | Use approved history | Six facts, 17,300 cents and PASS | Summary, facts and report |
| Repeatability | Run approved history again | Same facts and amounts | Comparison evidence |

### 5. Release gate and recovery plan

The batch will be held if any of the following occurs:

1. Invalid source records or conflicting entry IDs.
2. Missing site-history matches.
3. Multiple site-history matches.
4. Invalid reference intervals.
5. Row-accounting failure.
6. Fact count or revenue reconciliation failure.

The candidate run will be preserved in its own output directory. The approved reference will be processed separately in another output directory.

Each run will record its source and reference identities. Separate output folders will prevent old reports from being confused with new runs.

The approved run will be repeated in a third directory to demonstrate reproducibility without duplicating facts or revenue.

### 6. Limitations

The analysis depends on the accuracy and completeness of the reference history supplied by the reference owner.

The program can identify missing and overlapping intervals, but cannot independently establish which region assignment is factually correct.

### 7. Expected outcome

The candidate reference is expected to fail because of overlapping S2 intervals and missing S3 coverage.

The approved reference should pass because the reference owner corrected the S2 transition and S3 effective dates.

The final model will provide traceable diagnostics, reconciled revenue, regional work-order counts and a global distinct-work-order count.
