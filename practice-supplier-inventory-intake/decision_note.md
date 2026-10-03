# Worked decision note

Nine supplier records arrived. Four clean records were prepared for loading.
Five records were rejected: one had a quantity of zero, one was missing a
supplier ID, one had an invalid unit cost, one duplicated an earlier valid
record, and one had an invalid date. The warehouse should load only the four
clean records and send the rejected-record file to the supplier for correction.

This is a small fictional teaching dataset. In a production pipeline, the team
would also keep a run ID, source-file name, and timestamp for every load.
