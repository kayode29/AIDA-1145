# AIDA 1145 - Week 12 Graded Lab 8
# Part B: Final Decision and Business Interpretation

## 1. Business question

Can regional service revenue be trusted?

The answer is yes, but only after validating the service entries, confirming effective-dated site assignments, and reconciling the released facts to the canonical source records.

The candidate reference did not pass the release controls. The approved reference passed all implemented checks.

## 2. Candidate reference result

Decision: HOLD.

The candidate reference produced:

- 7 input rows.
- 6 canonical service entries.
- 1 identical retransmission.
- 0 source errors.
- 1 entry with zero history matches.
- 1 entry with multiple history matches.
- 17,300 cents of canonical source revenue.

Two reference problems were identified:

1. E03, for site S2 on November 15, matched both East and West because the effective-date intervals overlapped.
2. E04, for site S3 on November 14, had no matching history because the candidate South interval began on November 16.

The candidate report was not released. This was the correct decision because the regional assignments were not reliable.

## 3. Risk of an ordinary inner join

An ordinary inner join would not safely diagnose these problems.

- E04 would disappear because it has no matching history row. Its 1,500 cents of revenue would be omitted.
- E03 would appear twice because it matches two history rows. Its 6,000 cents would be counted twice.

The resulting joined data would contain 6 rows and 21,800 cents of revenue, instead of the correct 6 canonical entries and 17,300 cents.

The row count alone would not reveal the problem: one entry was lost and another was duplicated.

Therefore, the pipeline checks match counts before aggregation and does not use an ordinary inner join as its release validation.

## 4. Approved reference result

Decision: PASS.

The reference owner confirmed that:

- S2 moved from East to West effective November 10.
- S3 operated in South throughout November.
- The approved history contains the corrected effective dates.

The approved run produced:

- 7 input rows.
- 6 canonical entries.
- 1 identical retransmission.
- 0 source errors.
- 0 missing matches.
- 0 ambiguous matches.
- 6 released facts.
- 17,300 cents of released revenue.

The fact count and revenue both reconciled to the canonical source.

## 5. Regional results

| Region | Entries | Units | Revenue | Distinct work orders |
|---|---:|---:|---:|---:|
| East | 3 | 5 | 6,800 cents | 2 |
| West | 1 | 3 | 6,000 cents | 1 |
| South | 2 | 3 | 4,500 cents | 2 |
| Total | 6 | 11 | 17,300 cents | 4 globally |

The global distinct work-order count is 4.

Regional distinct work-order counts add up to 5 because work order W04 has service entries in both East and South. It is counted once in each region but only once in the global total.

## 6. Testing evidence

The following tests were completed:

| Test | Expected result | Actual result |
|---|---|---|
| Candidate reference | HOLD | HOLD |
| Approved reference | PASS | PASS |
| Identical retransmission | Keep one canonical record | PASS |
| Conflicting entry ID | HOLD | HOLD |
| November 10 boundary | Assign S2 to West | PASS |
| Repeatability | Identical output files | PASS |

The conflict test added a second E02 with a different unit price. The program classified it as a source error and withheld the released report.

The boundary test added E07 for S2 on November 10. The program correctly assigned E07 to West under the half-open interval rule.

The repeatability test produced identical SHA-256 hashes for the approved and repeated fact tables and regional reports.

## 7. Release controls

The pipeline applies these controls:

1. Validate required source fields, identifiers, dates, units and unit prices.
2. Identify identical retransmissions and conflicting entry IDs.
3. Validate site-history intervals.
4. Match each canonical entry to exactly one effective-dated history row.
5. Reconcile fact count and revenue to the canonical source.
6. Release facts and regional reporting only when all release checks pass.

Held runs retain diagnostic evidence but do not produce a released fact table or regional report.

## 8. Final business recommendation

Use the approved site-history reference for regional service revenue reporting.

Do not use the candidate reference for reporting because its overlapping S2 intervals and missing S3 coverage make regional results unreliable.

Retain the candidate run and its diagnostic files as evidence of the original reference-data problems.

The approved run is suitable for this exercise because all canonical entries have exactly one effective-dated match, the fact count and revenue reconcile, and the repeated run produces identical outputs.

The recommendation depends on the accuracy of the reference owner's approved history. Future changes to site assignments should be validated before regional revenue reports are released.

## 9. Conclusion

The pipeline demonstrates that regional service revenue should not be trusted simply because a join or report can be generated.

It must first pass source validation, retransmission and conflict checks, effective-date matching, and reconciliation.

The candidate reference correctly resulted in HOLD. The approved reference passed, producing 6 service facts and 17,300 cents of reconciled revenue.
