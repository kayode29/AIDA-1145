# AIDA 1145 – Can the Sales Model Support the Report?

## 1. Fact Grain and Replay

The fact grain is one distinct completed order line. The line_id identifies each individual order line, while order_id identifies the overall order.

The input contained six rows, five canonical lines, and one identical replay. The repeated L02 transaction was removed because it was an identical retransmission. O01 contains two legitimate order lines, L01 and L02, so both were retained.

## 2. Candidate Catalog Overlap and Financial Effect

The candidate catalog was placed on HOLD because P2 had overlapping effective dates between Essentials and Accessories.

L03, dated November 12, matched two catalog records instead of one. Its revenue was 3,000 cents. Counting it twice would incorrectly increase the total from 7,900 cents to 10,900 cents.

The pipeline correctly prevented the ambiguous transaction from entering the fact table.

## 3. Why the Corrected Output Passes

The source owner corrected the catalog so that Essentials ends on November 10 and Accessories begins on November 10.

Because the end date is exclusive, the two periods no longer overlap.

All five canonical sales lines matched exactly one catalog record. The fact table contained five rows, and the category report reconciled to 7,900 cents ($79.00).

There were four distinct orders, giving an average completed order value of $19.75.

The repeat-run test confirmed that the same inputs produced the same results.

## 4. Missing Reference Test

The missing-reference test changed P3's valid_from date to November 13.

L04 occurred on November 12 and therefore had zero catalog matches. The pipeline correctly returned HOLD because every sales line must have exactly one reference match.

## 5. One Limitation

The pipeline cannot independently prove that the original source contains every expected transaction because no external expected-order manifest was supplied. The exercise also excludes taxes, discounts, and returns.

## Final Decision

HOLD the candidate catalog because of overlapping effective dates and the risk of double-counting revenue.

PASS the corrected catalog because all five canonical lines have exactly one valid category match and the category report reconciles to $79.00.

Release the corrected report for this specific case, subject to the stated source-completeness and business-scope limitations.
