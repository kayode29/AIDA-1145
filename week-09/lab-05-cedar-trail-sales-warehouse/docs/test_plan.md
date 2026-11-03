# Test plan and run evidence

Complete this before your final recommendation. For each test, write the input or condition, the rule being checked, the command or code that runs it, the observed result, and whether it passed. Do not mark a test as passed until you have run it.

| Check | What could go wrong? | What should your code do? | Evidence / observed result | Pass? |
|---|---|---|---|---|
| Required CSV columns | | | | |
| Blank or duplicate `line_id` | | | | |
| Status scope | | | | |
| Repeated `order_id` with different lines | | | | |
| Invalid quantity, price, or discount | | | | |
| Candidate product code with no match | | | | |
| Duplicate product business key | | | | |
| Fact grain and unique line count | | | | |
| Dimension key coverage / foreign keys | | | | |
| Gross, discount, and net cents | | | | |
| Source-to-fact row and amount controls | | | | |
| Distinct order count and average order value | | | | |
| Repeated run / idempotency | | | | |

## Run record

| Catalogue version | Command | Python version | Output folder | Run status | Notes |
|---|---|---|---|---|---|
| Candidate | | | | | |
| Approved v2 | | | | | |
| Approved v2 repeat run | | | | | |
