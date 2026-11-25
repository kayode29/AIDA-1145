# Part A – Technical Proposal
## AIDA 1145: Graded Lab 7 – Service-Hours Reporting Pipeline Recovery

### 1. Objective

The objective is to build a reliable service-hours reporting pipeline that processes ticket updates, identifies retransmissions, handles revisions, detects invalid records and conflicts, and publishes a report only when all release conditions are satisfied.

The pipeline will use the supplied CSV source files and JSON manifest. Original source files will remain unchanged.

### 2. Proposed pipeline stages

The pipeline will follow these stages:

1. **Input:** Read the source CSV and batch manifest.
2. **Schema validation:** Confirm all required columns exist.
3. **Row validation:** Check ticket ID, branch, hours and revision.
4. **Duplicate detection:** Identify identical records with the same ticket and revision.
5. **Conflict detection:** Identify records with the same ticket and revision but different branch or hours.
6. **Revision resolution:** Select the highest valid revision for tickets without conflicts.
7. **Reconciliation:** Account for every input row exactly once.
8. **Release checks:** Verify handoff completeness, exceptions, ticket count and branch coverage.
9. **Publication:** Publish branch-hour totals only when every release condition passes.

A report becomes published only after all checks pass. A failed run will retain its evidence without replacing the previous passing report.

### 3. Classification rules

The pipeline will apply the rules in the following order:

**Validation:** Every row must contain a non-empty ticket ID, an expected branch, non-negative integer hours and a positive integer revision. Invalid rows will be recorded as exceptions, even if another row for the same ticket is valid.

**Retransmissions:** Rows identical in all four fields (ticket ID, branch, hours and revision) are retransmissions. One copy is retained as a candidate and each additional copy is counted separately.

**Conflicts:** If valid records share the same ticket ID and revision but disagree in branch or hours, that revision is a conflict. The pipeline will not guess which record is correct. Every distinct conflicting row is an exception, while identical extra copies remain retransmissions. All other valid, non-duplicate rows for that ticket will also be exceptions.

**Revision selection:** For a ticket without a conflict, the highest valid revision is selected. Lower valid revisions are classified as superseded. Invalid records remain exceptions and cannot silently replace an older valid record.

### 4. Row reconciliation

Every input row must be accounted for exactly once.

**Input rows = Selected + Superseded + Retransmitted + Exceptions**

The pipeline will check this formula before making a release decision. If the counts do not reconcile, the batch must be held.

### 5. Release conditions

The report can be released only when all of these conditions are satisfied:

- The manifest indicates that the handoff is complete.
- There are zero exceptions.
- There are zero conflicts.
- The selected distinct ticket count equals the expected count.
- Every expected branch is represented.
- The row-accounting formula reconciles.

A matching ticket count alone is not sufficient proof of correctness.

### 6. Evidence and safe recovery

Each run will have its own evidence folder containing a machine-readable summary and row-level classifications. The evidence will identify the source file and batch.

The initial run will be preserved separately from the corrected run. The corrected source will be processed using a new run folder.

A repeated corrected-source run will use another new run folder. Its selected records and branch totals will be compared with the previous passing run to demonstrate repeatability.

The release process will write a new report only after all gates pass. Failed runs will not overwrite or append to the last passing report. The summary will identify whether a previous passing report remains available and its run identity.

### 7. Test plan

| Test | Input or condition | Expected result | Evidence to inspect |
|---|---|---|---|
| Identical retransmission | Two identical rows for the same ticket and revision | One candidate and one retransmission | Row-level classification and summary |
| Valid revision | Same ticket has two valid revisions | Highest revision selected; lower revision superseded | Row-level classification |
| Invalid value | Negative hours or invalid revision | Exception and HOLD | Summary and row-level evidence |
| Same-revision conflict | Same ticket and revision have different hours or branches | Conflict, exceptions and HOLD | Conflict test evidence |
| Missing column | Source CSV lacks a required column | HOLD with schema error | Missing-column test evidence |
| Successful recovery | Corrected source satisfies all release gates | RELEASE and branch-hour report | Summary and published report |

### 8. Safe rerun and publication

The pipeline will use a new evidence directory for every attempt. Existing evidence will not be overwritten. A successful run will create or replace the published report only after validation and release checks pass.

A failed run will preserve the last passing report and record its identity. A repeated successful run must produce the same selected records and totals without appending duplicate rows.

### 9. Limitation

The pipeline validates the supplied records and manifest but cannot independently verify whether the reported hours reflect the actual work performed in the field. That requires confirmation from an authorized operational source.

### 10. Conclusion

This recovery workflow provides traceable classification, complete row reconciliation, safe revision handling and controlled publication. Separating run evidence from the published report protects the company from incomplete or conflicting data and supports repeatable recovery.
