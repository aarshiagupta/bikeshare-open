# Forecasting daily bikeshare demand: report

## Results

Daily Capital Bikeshare rides (`cnt`), split by date: train is 2011 (348
days after the 7-day lag warm-up), validation is H1 2012 (182 days), and
test is H2 2012 (184 days). **Before** is the unmodified starter (commit
`5a3fefe`; `git checkout 5a3fefe && make all` reproduces it). **After**
adds my feature, `cnt_roll_3` (the mean of the 3 days before *d*), and is
`reports/metrics.json` exactly as committed: `make all` on the final code.

| Model | Features | Valid R^2 | Valid MAE | Test R^2 | Test MAE |
|---|---|---|---|---|---|
| `baseline_mean` | before (14) | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| `baseline_mean` | after (15, + `cnt_roll_3`) | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| `baseline_persistence` | before (14) | 0.4507 | 900.6 | 0.5099 | 840.1 |
| `baseline_persistence` | after (15, + `cnt_roll_3`) | 0.4507 | 900.6 | 0.5099 | 840.1 |
| `ridge` | before (14) | 0.6475 | 832.9 | 0.5833 | 947.1 |
| `ridge` | after (15, + `cnt_roll_3`) | 0.6439 | 836.5 | 0.58 | 946.2 |
| `hgb` | before (14) | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| `hgb` | after (15, + `cnt_roll_3`) | 0.1983 | 1311.6 | -0.5338 | 1998.7 |

How to read it:

- **Mean baseline.** Negative R^2 on both splits, because 2012 is far
  busier than the 2011 mean.
- **Persistence ("yesterday again").** The baseline that matters here.
- **Ridge.** Beats persistence on R^2 in both splits, but loses to it on
  test MAE (946.2 vs 840.1).
- **Gradient boosting (hgb).** Negative on test (-0.5338), yet still far
  better than the mean baseline (-2.1441; MAE 1998.7 vs 2847.7). Negative
  R^2 and losing to the baseline are different things.
- **The feature.** Validation R^2 fell for both models: ridge -0.0036, hgb
  -0.0202. `cnt_lag_1` and `cnt_roll_7` already carry the short-term level,
  so a 3-day mean adds nothing.

**Response to the automated audit** (`reports/audit.jsonl`: leakage
`none`, temporal, baseline and reproducibility all `true`, 2 findings).

1. *`make train` prints test scores on every run.* That is the starter's
   design, and the assignment requires test scores in `metrics.json`, so I
   left it. It did mean the post-feature test numbers were on screen when
   `cnt_roll_3` was trained. The keep/drop call used only the validation
   deltas, both negative, and no modelling change was made after that. The
   Exercise 4 runs hide test unless `--final` is passed, and `--final` was
   run once.
2. *REPORT.md did not exist.* Correct when the audit ran: by the required
   commit order the audit comes before the report. This file resolves it.

## Headline finding

A model handed `casual` and `registered` scores test R^2 = 1.000
(`python -m src.leakage_demo`) because `casual + registered == cnt` on
every row: it has learned addition, not demand. With those and the time
indexes excluded, the honest ridge model scores test R^2 0.58 (MAE 946.2),
only 0.07 above "yesterday again" (R^2 0.5099, MAE 840.1), and it loses to
yesterday on MAE. Gradient boosting scores -0.5338 on test. That is not a
bug: ridership grew so much that 56.5% of test days exceed the highest 2011
count (6,043), and a tree cannot predict a value above anything it saw in
training. My feature, `cnt_roll_3`, lowered validation R^2 for both models
(ridge 0.6475 -> 0.6439, hgb 0.2185 -> 0.1983). I kept it only so this
before/after comparison is reproducible from the committed pipeline; on the
`/new-feature` rule (gain < 0.01) it would be dropped.

## Exercise 4: target transformation

**Why hgb fails.** It fails on *level*: 2012 counts lie outside the 2011
range. So I tried targets that express today relative to the recent past,
which a tree can handle, and multiplied or added the reference back after
prediction. They are behind `python -m src.train --target-transform <name>`.
That flag never writes `metrics.json`, and it hides the test set unless
`--final` is passed.

Validation only:

| Target | ridge val R^2 | hgb val R^2 | hgb val MAE |
|---|---|---|---|
| `cnt` (committed pipeline) | 0.6439 | 0.1983 | 1311.6 |
| `log1p(cnt)` | 0.0931 | 0.1675 | 1342.0 |
| `cnt / cnt_lag_1` | -1.2933 | 0.6167 | 816.4 |
| `cnt / cnt_roll_7` | 0.3924 | **0.7483** | **681.5** |
| `cnt - cnt_roll_7` | 0.6545 | 0.7209 | 722.4 |

I chose `cnt / cnt_roll_7` on validation and then **touched the test set
once** (`--final`): hgb test R^2 **0.6225**, MAE **829.4**. That is better
than untransformed ridge (0.58 / 946.2) and persistence (0.5099 / 840.1).

**Is it defensible, or a way to win?** Defensible as a modelling choice,
with a narrower claim than the table invites.

For:

- The denominator is past-only: `cnt_roll_7` shifts before it rolls,
  which is tested.
- The transformation answers a diagnosed failure (extrapolation), not a
  search for a better number.
- Two different detrendings (ratio and difference) both lift hgb from 0.20
  to above 0.72, while `log`, which compresses the scale but does not
  detrend, does nothing. The gain comes from removing the level, not from
  luck.
- It held on test.

Against:

- It is the best of four tries on 182 validation days.
- The same transform *hurts* ridge (validation 0.3924, test 0.0267), so
  "transform everything" would flip the comparison for the wrong reason. A
  fair comparison gives each model its own best target. On validation that
  is still hgb (0.7483) over ridge (0.6545).
- On test its MAE edge over persistence is 10.7 rides a day (1.3%), which
  is inside the noise.

The defensible claim is: **trees compete once the target is detrended.**
The claim "gradient boosting beats persistence" is not defensible. The
committed `metrics.json` stays untransformed.

## Exercise 5: ridge vs persistence

Ridge is not worth deploying over "yesterday again" as a drop-in
replacement. Its 0.07 R^2 edge on test (0.58 vs 0.5099) is bought almost
entirely on 32 days when demand swung by more than 1,500 rides from the day
before: there ridge's MAE is 1,502 against persistence's 2,413, because
persistence is always one day late. On the other 152 test days persistence
is far better (MAE 509 vs 829). Ridge is closer to the truth on only 38.6%
of test days, its median error is 891 rides against 506, and it
under-predicts by 551 rides a day on average: it learned 2011 levels, and
ridership grew. R^2 squares errors, so a few large misses dominate it; MAE
weights every day equally and says persistence. If the operator's costs
scale with rides on an ordinary day (staffing, rebalancing), persistence is
the better and simpler forecast. Ridge earns its place only if the costly
event is a large miss: it has 3 test days with errors above 2,500 against
persistence's 12. Even then, the right deployment is persistence with a
ridge-based alarm for weather-driven swings, not ridge alone.

## Attribution

**Model: Claude Opus 5.5** (`claude-opus-5-5`, Anthropic, hosted;
Anthropic does not publish its parameter count), 1M-token context, via
Claude Code 2.1.332 on a Claude subscription. **I switched models before
Exercise 1.** `qwen3.5:27b` via Ollama would not load: it needed 18.4 GiB
and only 15.5 GiB was available on a 24 GB M4 Pro. `qwen3.5:9b` (64k
context) passed `make check-model` but was used only for setup checks. All
graded work used Opus 5.5: interactively in a VS Code session, and in
headless `claude -p` sessions in the repo root, so the repo's hook and
skills were live, for the seeded faults, the blind fixes and the audits.
Optional Exercise 6 (a second model) was not attempted.

**Generated by the agent:**

- `tests/test_leakage.py`:
  - `test_roll_3_is_mean_of_three_prior_days`
  - `test_unknown_weather_label_raises`
  - `test_no_feature_reconstructs_the_target`
  - `test_validation_score_is_not_too_good`
- `tests/test_contract.py`: `test_every_raw_column_is_classified`.
- `src/features.py`: the `cnt_roll_3` line.
- `src/config.py`: `RAW_FEATURE_COLS`, `SOURCE_COLS`, `DATE_COL`,
  `RAW_SHA256`.
- `src/ingest.py`: the hash check in `load_raw()`.
- `src/train.py`: `TARGET_TRANSFORMS`, `TransformedTarget`,
  `--target-transform` and `--final`.
- `.claude/skills/seed-fault/SKILL.md`.
- Seeding all four faults, and all three fixes (blind sessions).
- `docs/SEEDED_FAULTS.md`, `docs/AUDIT.md` (auditor output and a draft
  verdict), the CLAUDE.md edits, the DECISIONS.md wording, and the draft of
  this report.
- `reports/audit.jsonl` (`agent/audit.py`) and `reports/metrics.json`
  (`make all`).

**Decisions that were mine.** Several were first proposed by the agent; I
accepted each after reading the numbers. Each one traces to a line in
`docs/DECISIONS.md`:

1. **What to predict.** Daily `cnt`, scored on H2 2012 (starter line,
   kept).
2. **What counts as leakage.** `casual`/`registered`, the time indexes and
   `cnt_2d_bfr` (starter lines). Also any feature or pair of features that
   reconstructs `cnt`, and validation ridge R^2 above 0.95 treated as a
   leak until proven otherwise (the line on the two leakage checks).
3. **How to split.** By date, 2011 / H1 2012 / H2 2012 (starter line).
4. **Which baselines.** Mean and persistence, reported with every score
   (starter line).
5. **Whether to keep my feature.** Kept despite a negative delta, for the
   comparison only (the `cnt_roll_3` lines).
6. **Whether the answer is believable.** R^2 1.000 rejected as leakage;
   hgb's negative test R^2 believed, because of the 56.5% out-of-range
   evidence (the believability line).
7. **Raw data is guarded by hash, not trust** (the SHA-256 line).
8. **Exercise 4.** Defensible but not adopted (the Exercise 4 line).
9. **Exercise 5.** Persistence over ridge (the Exercise 5 line).
10. **Model.** Opus 5.5 after the local models failed (the model line).

The agent is accountable for the code; I am accountable for every number
above.
