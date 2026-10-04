# Site Policy Decision

## Decision

I recommend the `flag` policy for this donation pickup dataset.

## Reason

The `flag` policy keeps records with a missing pickup site in the clean output while clearly marking the site as missing. This preserves more usable donation records for operational analysis while still identifying the data-quality issue.

With the `flag` policy, 4 rows are clean and 3 rows are rejected.

With the `reject` policy, 3 rows are clean and 4 rows are rejected because records with a missing pickup site are removed.

## Limitation

The `flag` policy should only be used when a missing pickup site does not prevent the organization from using the record. Missing site information should be corrected when possible because it may affect pickup planning and reporting.