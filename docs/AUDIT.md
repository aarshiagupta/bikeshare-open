# Audit of a teammate's repository (Exercise 3)

**Repository audited:** https://github.com/Igosain08/bikeshare-open
at commit `c4d7f25` ("REPORT.md: rewrite in plainer language").

**How it was run.** Cloned to a separate folder and checked for anything
unsafe to execute (no network calls, no deletes beyond the starter's
`make clean`). Then, from this repo's root, a headless Claude Code session
(`claude-opus-5-5`, session `fed616fe`) invoked this repo's
`leakage-auditor` subagent on everything since the teammate's first commit:
`git diff $(first commit) HEAD -- src tests Makefile`. The subagent ran 14
tool calls in about 100 s, including the teammate's full test suite and a
re-run of their pipeline. Its report follows unedited; only the harness's
hand-back wrapper lines were removed.

## The auditor's output (verbatim)

# Audit: teammate repo bikeshare-open (diff from `220b118` to `c4d7f25`, limited to src, tests and Makefile)

**Verdict: all five checks pass. I found nothing in the diff that changes a reported number or undoes a conclusion.**

I used the teammate repo's own `/Users/aarshiagupta/Documents/dsc180a/ma6/teammate-audit/bikeshare-open/CLAUDE.md`. It matches the reference rules and adds two of its own: rejected features go in `REJECTED_COLS`, and a feature is kept only if ridge validation R² rises by at least 0.01.

## Test results
`python -m pytest tests -q`, run from inside the teammate repo: **24 passed in 1.26s**. I turned off the pytest cache and bytecode writing, and `git status` was still clean afterwards. I didn't modify any repo files. My reproduction script and its parquet output are in `/tmp/audit_bk/`.

## Reproduction
I rebuilt the features in memory, wrote the parquet to `/tmp`, and ran `fit_and_score`, `score_transforms(None)`, `score_transforms("ratio_roll7")` and `diagnostics()`. All four outputs exactly match the committed files:
- `reports/metrics.json`
- `reports/exercise4_valid.json`
- `reports/exercise4_test.json`
- `reports/diagnostics.json`

`verify_raw()` passes, so the raw data still matches `RAW_SHA256`.

## Evidence for each check
1. **Target leakage: pass.**
   - `casual + registered == cnt` holds on all 728 raw rows.
   - The final feature set has 14 columns: temp, atemp, hum, windspeed, dayofweek, is_weekend, is_holiday, is_workday, month_sin, month_cos, weather_severity, cnt_lag_1, cnt_lag_7, cnt_roll_7. None of them is in `FORBIDDEN`.
   - `cnt_lag_2` is excluded through `REJECTED_COLS` (`src/config.py:49`).
   - `test_no_feature_restates_the_target` fits every single feature and every pair against cnt, casual and registered, and finds no exact fit.
   - In `RelativeTarget` (`src/train.py:50-85`), the reference columns are `cnt_roll_7` and `cnt_lag_1`. Both are shifted, so they are known at prediction time.
2. **Temporal ordering: pass.**
   - `temporal_split` splits by date: train is 2011-01-10 to 2011-12-31 (348 rows), valid is 2012-01-01 to 2012-06-30 (182), test is 2012-07-01 to 2012-12-31 (184).
   - The only fitted transformer is the `StandardScaler` inside the ridge pipeline, and it is fit on train only.
   - `cnt_roll_7` shifts by one day before the rolling mean (`src/features.py:77`).
   - `test_beats_the_mean_baseline` now runs on validation instead of test.
   - The transform scored on test, ratio_roll7, was the best on validation (hgb R² 0.7454), so it was chosen on validation.
   - `--final` was run a second time in commit `222a7ca`. That rerun only added the two baseline rows; every model score is identical to the first run, and no choice changed afterwards.
3. **Calendar gaps: pass.**
   - `cnt_lag_2` is built after `reindex_to_calendar` (`src/features.py:54,75`).
   - The pinned test value is correct: cnt on 2011-03-16 is 2192 (CSV line 73, instant 75).
   - `changed()` in `src/diagnostics.py:58-60` shifts by rows, not calendar days, on the post-dropna frame. The only gap in that frame is just before 2011-03-18, which is outside the test set, so no diagnostic number is affected.
4. **Silent row loss: pass.**
   - 728 raw rows become 714 feature rows: 7 lost to the lag warm-up and 7 after the missing 2011-03-10.
   - `test_only_expected_rows_are_dropped` caps the loss at exactly 14.
   - The `.map()` in `encode_weather` raises on any unknown label, and two tests check that.
5. **Unreported baseline: pass.** The mean and persistence baselines are reported next to every model score:
   - `fit_and_score`
   - `score_transforms`, where they were added in `222a7ca`
   - every test slice and validation half in `diagnostics`

   For context, persistence scores 0.4507 on validation and 0.5099 on test, against ridge at 0.6475 and 0.5833.

I also independently confirmed the decision to reject `cnt_lag_2`: ridge validation R² goes from 0.6475 to 0.6453, a change of -0.0022, matching the figure in `src/config.py`.

## My verdict

**The auditor found nothing that changes a number, and I agree.** I checked
its central claim myself instead of taking it on trust: in a fresh clone of
the teammate's repo, `make all` regenerated `reports/metrics.json` with no
diff, and `python -m pytest tests -q` printed `24 passed`. Of the remarks it
made, I agree that the row-based `.shift()` in `changed()`
(`src/diagnostics.py:58-60`) is latent and affects no reported number,
because the frame's only gap is in March 2011, outside the test set. The
one place I would push further is a point the auditor raised and then
waved through: `--final` was run a second time, in commit `222a7ca`. I read
that diff, and it only adds the two baseline rows to
`reports/exercise4_test.json`; every model score is identical, so no
choice was informed by a second look at test. It is not a leak. It does,
though, make the DECISIONS.md line "Test set touched once" slightly
inaccurate as written. I would reword it as "scored once for the choice;
regenerated in `222a7ca` only to add baseline rows", so a grader reading
the commit history does not take the second run for iteration on test.
