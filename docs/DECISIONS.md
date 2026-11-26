# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.
- 2026-11-25: Add `cnt_roll_3` (mean cnt over the 3 days before d; uses only d-1..d-3, known before d). Validation R^2 ridge 0.6475 -> 0.6439 (-0.0036), hgb 0.2185 -> 0.1983 (-0.0202). Below the 0.01 floor, so the skill's rule says drop it; kept only so the report's before/after rows exist, and reported as a negative result.
- 2026-11-25: Keep `cnt_roll_3` despite the negative delta, so the before/after comparison in REPORT.md stays reproducible from the committed pipeline; the negative result is reported, not hidden.
- 2026-11-25: Classify every raw column by hand in `src/config.py` (`RAW_FEATURE_COLS`, `SOURCE_COLS`) and test that none is unclassified. Typed out, not derived from `feature_columns()`, because a derived list would absorb a new column and the test could never fail. Checked by appending a column to a copy of the CSV: test goes red.
- 2026-11-25: Add a direct test that `encode_weather` raises on an unknown label. Without it, deleting the `raise` (seeded fault 3) left all tests green: no real row has an unknown label.
- 2026-11-25: Add two leakage checks FORBIDDEN cannot provide: no feature or pair of features equals `cnt`, and validation ridge R^2 must stay below 0.95 (honest is ~0.65). Checked by adding `casual + registered` as `riders_total` to a copy: both go red.
