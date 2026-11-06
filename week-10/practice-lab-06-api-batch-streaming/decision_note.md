# Harbourline Bike Share — Example Batch Decision

**Batch:** 2026-10-15 at 10:00 a.m.
**Recommendation:** **HOLD** the snapshot from release as a complete station-rebalancing dashboard.

## Evidence

- The client followed two pages and reached a terminal `next_cursor: null`.
- The source returned six rows. One exact page-boundary duplicate was ignored, leaving five unique observations for five expected stations.
- Source station coverage was 5/5 = **100%**.
- Three observations were both valid and no more than 15 minutes old. Usable and fresh coverage was 3/5 = **60%**, below the 95% rule.
- One value was impossible under the stated rule: ST-02 reported 13 available bikes for 10 docks. The value-validation error rate was 1/5 = **20%**, above the 2% maximum.
- ST-04's reading was 20 minutes old, exceeding the 15-minute freshness limit.
- The exact duplicate did not create an extra observation when the same batch was simulated a second time.

## Recommended next actions

1. Keep the original pages and the run outputs for traceability.
2. Ask the source owner to investigate the ST-02 count; do not silently change it to 10.
3. Request or wait for a newer ST-04 observation.
4. Rerun the full paginated batch and check the release gates again.
5. Until the gates pass, label the full dashboard as **HOLD / incomplete for a complete rebalancing plan**. A partial display is appropriate only if the dashboard owner explicitly approves it and unavailable values are clearly identified.

## Limits

This decision applies to one fictional, saved batch and the thresholds in this practice lab. It does not establish why the source values are wrong, prove that the API is generally unreliable, or authorize a different service-level threshold.
