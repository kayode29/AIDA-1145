# Generated output guide

Run `py run_lab.py` from the lab folder to regenerate these files from the supplied JSON and CSV inputs.

- `accepted_observations.csv` — station observations that pass the value and freshness checks.
- `quarantine.csv` — observations held with a reason for review.
- `release_gates.csv` — observed results compared with the written release rules.
- `retry_policy_examples.csv` — retry decisions for sample HTTP statuses; the program does not contact an API or wait.
- `run_summary.json` — machine-readable batch counts and the overall decision.

The sample result is `HOLD`: only three of five stations have valid, fresh values, and the invalid-value rate exceeds the allowed maximum. The source-coverage result can still be 100% because every station ID arrived even though two observations are not usable for this dashboard.
