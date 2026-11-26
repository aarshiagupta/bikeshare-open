# Seeded faults (Exercise 2)

Every block below is pasted output, not a description of it.

**Method.** Each fault is seeded with the repo's own `/seed-fault` skill in a
headless Claude Code session (`claude -p`, model `claude-opus-5-5`) started in
the repo root, so `.claude/settings.json` and its PostToolUse hook are live.
The fault is then fixed by a **second, fresh session** that is told only:
"make test is failing in this repo. Find the cause and fix it. Do not edit
anything under tests/." It is not told what was broken. "Turns to fix" is that
session's `num_turns` as reported by Claude Code. The hook stderr is copied
from the session transcript (the `hook_blocking_error` attachment), i.e.
exactly what the agent was shown. All faults were run against the final
suite (19 tests), so the output below is what the suite prints today.

## 0. The feature test, failing before the feature existed

Commit `73f955a` added `test_roll_3_is_mean_of_three_prior_days` before
`cnt_roll_3` existed. Output of `python -m pytest tests/ -q` at that commit:

```text
.........F.....                                                          [100%]
=================================== FAILURES ===================================
___________________ test_roll_3_is_mean_of_three_prior_days ____________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]

    def test_roll_3_is_mean_of_three_prior_days(feats):
        """cnt_roll_3 on 2011-06-15 must be the mean of cnt on 06-12, 06-13, 06-14,
        read by hand from data/raw/bike_daily.csv: (4460 + 5020 + 4891) / 3.
        Same-day cnt is 5180, so a window that includes today gives a different
        number and fails here."""
        row = feats.set_index("dteday").loc[pd.Timestamp("2011-06-15")]
>       assert row.cnt_roll_3 == pytest.approx((4460 + 5020 + 4891) / 3)
               ^^^^^^^^^^^^^^

tests/test_leakage.py:66: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = instant                   166.0
season                   SPRING
yr                       2011.0
mnth                  ...        4891.0
cnt_lag_7                4401.0
cnt_roll_7          4605.571429
Name: 2011-06-15 00:00:00, dtype: object
name = 'cnt_roll_3'

    @final
    def __getattr__(self, name: str):
        """
        After regular attribute access, try looking up the name
        This allows simpler access to columns for interactive use.
        """
        # Note: obj.x will always call obj.__getattribute__('x') prior to
        # calling obj.__getattr__('x').
        if (
            name not in self._internal_names_set
            and name not in self._metadata
            and name not in self._accessors
            and self._info_axis._can_hold_identifiers_and_holds_name(name)
        ):
            return self[name]
>       return object.__getattribute__(self, name)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'Series' object has no attribute 'cnt_roll_3'. Did you mean '.cnt_roll_7' instead of '.cnt_roll_3'?

/Users/aarshiagupta/Documents/dsc180a/ma6/bikeshare-open/.venv/lib/python3.15/site-packages/pandas/core/generic.py:6194: AttributeError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_roll_3_is_mean_of_three_prior_days - Attri...
1 failed, 14 passed in 0.88s
```

It fails for the right reason: the column does not exist yet. Commit
`09ce43a` adds the feature and the suite goes green.

## 1. A forbidden column added to `feature_columns`

**Exact change** (seeded by `/seed-fault`):

```diff
 def feature_columns(df: pd.DataFrame) -> list[str]:
     """Numeric columns that are safe to feed the model."""
     numeric = df.select_dtypes(include="number").columns
-    return [c for c in numeric if c not in FORBIDDEN]
+    return [c for c in numeric if c not in FORBIDDEN] + ["casual"]
```

**Hook stderr** (fired on the Edit, before anyone ran a test; session
`fbe086d9`):

```text
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /Users/aarshiagupta/Documents/dsc180a/ma6/bikeshare-open/src/features.py:
        no feature may be a copy or rescaling of any FORBIDDEN column (e.g.
        `walkups = casual`). Highest honest |corr| is ~0.95 (lagged counts)."""
        cols = feature_columns(feats)
        y = feats[TARGET]
        for c in cols:
            assert not (feats[c] == y).all(), f"{c} equals {TARGET}"
            assert abs(feats[c].corr(y)) < 0.99, f"{c} is a near-copy of {TARGET}"
            for f in sorted(FORBIDDEN & set(feats.columns)):
>               assert abs(feats[c].corr(feats[f])) < 0.99, f"{c} is a near-copy of forbidden {f}"
E               AssertionError: casual is a near-copy of forbidden casual
E               assert np.float64(1.0) < 0.99
E                +  where np.float64(1.0) = abs(np.float64(1.0))
E                +    where np.float64(1.0) = corr(0       41.0\n1       43.0\n2       25.0\n3       38.0\n4       54.0\n       ...  \n709    247.0\n710    644.0\n711    159.0\n712    364.0\n713    439.0\nName: casual, Length: 714, dtype: float64)
E                +      where corr = 0       41.0\n1       43.0\n2       25.0\n3       38.0\n4       54.0\n       ...  \n709    247.0\n710    644.0\n711    159.0\n712    364.0\n713    439.0\nName: casual, Length: 714, dtype: float64.corr

tests/test_leakage.py:94: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
FAILED tests/test_leakage.py::test_no_feature_reconstructs_the_target - Asser...
2 failed, 9 passed in 1.11s
```

The hook shows only the last 20 lines of pytest's output, which is why it
opens mid-traceback.

**Red test output** (`python -m pytest tests/ -q`, full output; the seeding
session itself looked only at the last 25 lines):

```text
F.....F.....F......                                                      [100%]
=================================== FAILURES ===================================
_____________________ test_every_raw_column_is_classified ______________________

raw =      instant     dteday  season  ...  weather days_since_2011 cnt_2d_bfr
0          3 2011-01-03  WINTER  ...     GOOD...       729       3095
727      731 2012-12-31  WINTER  ...    MISTY             730       1341

[728 rows x 18 columns]
feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....142857  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1531.428571  2077.333333

[714 rows x 29 columns]

    def test_every_raw_column_is_classified(raw, feats):
        """A column in the raw CSV that src/config.py does not classify must not
        enter silently. feature_columns() keeps every numeric non-FORBIDDEN
        column, so a new numeric column would become a feature with no review."""
        classified = FORBIDDEN | RAW_FEATURE_COLS | SOURCE_COLS | {DATE_COL}
        unclassified = set(raw.columns) - classified
        assert not unclassified, (
            f"unclassified raw columns {sorted(unclassified)}: add each to "
            "FORBIDDEN, RAW_FEATURE_COLS or SOURCE_COLS in src/config.py")
        raw_in_model = set(feature_columns(feats)) & set(raw.columns)
>       assert raw_in_model <= RAW_FEATURE_COLS, (
            f"raw columns reaching the model without review: {sorted(raw_in_model - RAW_FEATURE_COLS)}")
E       AssertionError: raw columns reaching the model without review: ['casual']
E       assert {'atemp', 'ca..., 'windspeed'} <= {'atemp', 'hu..., 'windspeed'}
E         
E         Extra items in the left set:
E         'casual'

tests/test_contract.py:33: AssertionError
__________________________ test_no_forbidden_features __________________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....142857  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1531.428571  2077.333333

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_3', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:36: AssertionError
___________________ test_no_feature_reconstructs_the_target ____________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....142857  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1531.428571  2077.333333

[714 rows x 29 columns]

    def test_no_feature_reconstructs_the_target(feats):
        """Catches leakage that FORBIDDEN cannot: a target-derived column under an
        innocent name. No feature, and no sum of two features, may equal cnt; and
        no feature may be a copy or rescaling of any FORBIDDEN column (e.g.
        `walkups = casual`). Highest honest |corr| is ~0.95 (lagged counts)."""
        cols = feature_columns(feats)
        y = feats[TARGET]
        for c in cols:
            assert not (feats[c] == y).all(), f"{c} equals {TARGET}"
            assert abs(feats[c].corr(y)) < 0.99, f"{c} is a near-copy of {TARGET}"
            for f in sorted(FORBIDDEN & set(feats.columns)):
>               assert abs(feats[c].corr(feats[f])) < 0.99, f"{c} is a near-copy of forbidden {f}"
E               AssertionError: casual is a near-copy of forbidden casual
E               assert np.float64(1.0) < 0.99
E                +  where np.float64(1.0) = abs(np.float64(1.0))
E                +    where np.float64(1.0) = corr(0       41.0\n1       43.0\n2       25.0\n3       38.0\n4       54.0\n       ...  \n709    247.0\n710    644.0\n711    159.0\n712    364.0\n713    439.0\nName: casual, Length: 714, dtype: float64)
E                +      where corr = 0       41.0\n1       43.0\n2       25.0\n3       38.0\n4       54.0\n       ...  \n709    247.0\n710    644.0\n711    159.0\n712    364.0\n713    439.0\nName: casual, Length: 714, dtype: float64.corr

tests/test_leakage.py:94: AssertionError
=========================== short test summary info ============================
FAILED tests/test_contract.py::test_every_raw_column_is_classified - Assertio...
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
FAILED tests/test_leakage.py::test_no_feature_reconstructs_the_target - Asser...
3 failed, 16 passed in 0.88s
```

**Turns to fix: 7** (blind fix session `4be382e4`): it found the
`+ ["casual"]`, removed it, and confirmed 19 passed with `git diff` empty.
Three independent tests catch this fault: the starter's FORBIDDEN gate; the
unclassified-column contract test (a raw column reached the model without
being in `RAW_FEATURE_COLS`); and the copy-of-a-forbidden-column check.

*Why fault 1 was recorded twice.* It was first recorded in `f3cd58d`/`7989151`,
when 2 tests failed and the blind fix took 4 turns. The final review then
found that a renamed single leak (`walkups = casual`) passed every test, and
`2a0e86f` extended `test_no_feature_reconstructs_the_target` to close it.
That made this fault trip a third test, so the section was re-recorded
against the final suite: the output above is what the tests print today.

## 2. The `.shift(1)` deleted from `cnt_roll_7`

**Exact change** (seeded by `/seed-fault`):

```diff
     out["cnt_lag_1"] = out[TARGET].shift(1)
     out["cnt_lag_7"] = out[TARGET].shift(LAG_WARMUP)
-    out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()
+    out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()
```

**Hook stderr:**

```text
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /Users/aarshiagupta/Documents/dsc180a/ma6/bikeshare-open/src/features.py:
[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:62: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 10 passed in 1.25s
```

**Red test output** (`python -m pytest tests/ -q`):

```text
.........F.........                                                      [100%]
=================================== FAILURES ===================================
_______________________ test_rolling_mean_excludes_today _______________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....428571  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1789.857143  2077.333333

[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:62: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 18 passed in 0.82s
```

**Turns to fix: 4.** The fix session restored `.shift(1)` and nothing else;
19 passed, `git status` clean.

**What this exposed.** Only one test catches this, and it checks one date
(row 200). The broader leakage checks stay green because today's count is
only 1/7 of the window: correlation with `cnt` stays under 0.99 and ridge
stays under 0.95. The starter's test also guards its assertion with
`if all(...)`, so if row 200 ever sat next to a missing day it would pass
without checking anything. It holds today (the checked date has a full
window), but it is the weakest link in the suite.

## 3. The weather encoder's `raise` removed

**Exact change** (seeded by `/seed-fault`):

```diff
     known = series.dropna()
     unknown = set(known.unique()) - set(WEATHER_ORDER)
-    if unknown:
-        raise ValueError(f"unmapped weather labels: {sorted(unknown)}")
     return series.map(WEATHER_ORDER).astype(float)
```

**Hook stderr:**

```text
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /Users/aarshiagupta/Documents/dsc180a/ma6/bikeshare-open/src/features.py:
......F....                                                              [100%]
=================================== FAILURES ===================================
______________________ test_unknown_weather_label_raises _______________________

    def test_unknown_weather_label_raises():
        """encode_weather must fail loudly on a label it does not know. A silent
        .map() turns it into NaN and dropna() deletes the day without a word.
        No row in the real data exercises this, so only a direct call can."""
>       with pytest.raises(ValueError, match="unmapped weather"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:79: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_unknown_weather_label_raises - Failed: DID...
1 failed, 10 passed in 1.25s
```

**Red test output** (`python -m pytest tests/ -q`):

```text
...........F.......                                                      [100%]
=================================== FAILURES ===================================
______________________ test_unknown_weather_label_raises _______________________

    def test_unknown_weather_label_raises():
        """encode_weather must fail loudly on a label it does not know. A silent
        .map() turns it into NaN and dropna() deletes the day without a word.
        No row in the real data exercises this, so only a direct call can."""
>       with pytest.raises(ValueError, match="unmapped weather"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:79: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_unknown_weather_label_raises - Failed: DID...
1 failed, 18 passed in 0.84s
```

**Turns to fix: 5.** The fix session restored both lines exactly; 19 passed,
`git status` clean.

**What this exposed.** On the unmodified starter this fault was invisible:
every one of the 14 starter tests stays green, because no row in the real
data has an unknown label, so the `raise` is never reached. The test that
catches it, `test_unknown_weather_label_raises`, was added in commit `8137cfd`
before any fault was seeded, precisely because of this. It is in
`tests/test_leakage.py` and not `test_contract.py` because the hook only runs
`test_leakage.py`; anywhere else, the hook would have stayed silent.

## 4. The fault the hook cannot see: a `cp` into `data/raw/`

**The fault.** Replace `data/raw/bike_daily.csv` with a "corrected" file
that is quietly wrong: windspeed set to 0 on all 30 days of June 2012 (a
sensor dropout). The `casual + registered == cnt` identity still holds, so
nothing in the data announces it. The PostToolUse hook matches only
`Edit|Write`, and the repo's deny rules are `Edit`/`Write` path rules, so a
Bash `cp` is outside both.

**What happened when the agent was asked to do it.** Three attempts, all in
headless sessions with `Bash(cp:*)` explicitly allowlisted:

*Attempt 1.* The agent refused on its own, before any permission check:

```text
I didn't replace the file, and I didn't run `make test` yet.

**Why I stopped:** `.claude/settings.json` blocks the Write and Edit tools from changing anything under `data/raw/` (`Write(./data/raw/**)` and `Edit(./data/raw/**)`). So the Write attempt would certainly be denied, and I skipped it. You did say to fall back to `cp`, but that rule looks like a deliberate guard on the raw data, and `cp` would just go around it. I'd rather have your OK before overriding it than assume it.

**What I could check:**
- Both files have 728 data rows plus a header, with the same columns in the same order.
- The first rows match in value. The only visible difference is that v2 drops the quotes around text fields.
- I couldn't compare every row: the command for that needed approval and didn't run. So I can't yet tell you what v2 actually corrects.

If you confirm, I'll run `cp` and then `make test`. Expect failures either way: the last three commits deliberately seeded faults into the pipeline, and they're still in place.
```

*Attempts 2 and 3.* After explicit approval, Claude Code's permission layer
denied the `cp`, first with the source outside the repo, then inside it:

```text
Permission to use Bash with command cp /private/tmp/.../incoming/bike_daily_v2.csv data/raw/bike_daily.csv has been denied.
Permission to use Bash with command cp incoming/bike_daily_v2.csv data/raw/bike_daily.csv has been denied.
```

So in Claude Code 2.1.332 the `Edit(./data/raw/**)` deny rule is also
applied to the destination of a simple `cp`. The lesson's premise that an
Edit deny does not stop a Bash `cp` is out of date for this version for
that one command. It is still not a sandbox: it parses the command, and
anything it cannot parse (a Python one-liner, a Make target, a script)
is not covered.

**What happened from a plain shell.** The same `cp`, run in an ordinary
terminal (no Claude Code, so no hook and no permission rules), with the
pre-fix code:

```text
$ cp bike_daily_v2.csv data/raw/bike_daily.csv
(exit 0)
$ git status --short
 M data/raw/bike_daily.csv
$ make test
python -m pytest tests/ -q
...................                                                      [100%]
19 passed in 0.76s
$ make all
OK ingest: 728 rows, 2011-01-03 -> 2012-12-31
OK features: 714 rows, 15 features -> features.parquet
  "ridge": {
  "hgb": {
```

The copy succeeded, no hook fired, **all 19 tests stayed green**, and
`make all` printed `OK` at every stage. Only the numbers moved, and they
moved *up*, which is the dangerous direction:

```text
ridge valid r2 0.6439 -> 0.6576 | test r2 0.58 -> 0.58
hgb valid r2 0.1983 -> 0.2401 | test r2 -0.5338 -> -0.5338
baseline_persistence valid r2 0.4507 -> 0.4507 | test r2 0.5099 -> 0.5099
```

A reader would take the higher validation R^2 for a modelling gain.

**What would have caught it.**

- *A Stop hook running `make test`*: would not. The tests were green.
- *A PreToolUse hook on Bash* that rejects any command writing under
  `data/raw/`: catches the agent, not a person or a script in a shell.
- *A filesystem permission* (`chmod a-w data/raw/bike_daily.csv`, or
  `chflags uchg` on macOS): catches every writer, but lives outside git, so
  a fresh clone does not have it.
- *A hash check on the raw file*: catches every writer, travels with the
  repo, and fails before any number is produced. **Implemented.**

**The catch (implemented).** `load_raw()` checks the file's SHA-256 against
`RAW_SHA256` in `src/config.py`. Every stage and every test reads the raw
file through `load_raw()`, so a changed file stops all of them:

```diff
diff --git a/src/config.py b/src/config.py
index 9f8cfb4..844dd51 100644
--- a/src/config.py
+++ b/src/config.py
@@ -20,6 +20,12 @@ DATA_URL = (
     "interpretable-ml-book/master/data/bike.csv"
 )
 
+# SHA-256 of the checked-in raw file. load_raw() refuses any other bytes, so a
+# `cp` into data/raw/ from a shell -- which no Claude Code hook or permission
+# rule sees -- fails every stage and every test instead of shifting the
+# numbers silently. Replacing the data is then a deliberate, reviewed edit here.
+RAW_SHA256 = "a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc"
+
 TARGET = "cnt"
 
 # --- Three reasons a column is kept out of the feature set --------------
diff --git a/src/ingest.py b/src/ingest.py
index 6654075..0657e65 100644
--- a/src/ingest.py
+++ b/src/ingest.py
@@ -2,12 +2,13 @@
 
 Run: python -m src.ingest
 """
+import hashlib
 import sys
 import urllib.request
 
 import pandas as pd
 
-from src.config import DATA_URL, RAW
+from src.config import DATA_URL, RAW, RAW_SHA256
 
 EXPECTED_MIN_ROWS = 700
 REQUIRED_COLS = {"dteday", "cnt", "casual", "registered", "temp", "hum", "windspeed"}
@@ -21,6 +22,12 @@ def download(force: bool = False) -> None:
 
 
 def load_raw() -> pd.DataFrame:
+    digest = hashlib.sha256(RAW.read_bytes()).hexdigest()
+    if digest != RAW_SHA256:
+        raise ValueError(
+            f"{RAW.name} has changed (sha256 {digest[:16]}..., expected "
+            f"{RAW_SHA256[:16]}...). Restore it with `git checkout -- data/raw/` "
+            "or, if the change is intended, review it and update RAW_SHA256.")
     df = pd.read_csv(RAW, parse_dates=["dteday"])
     missing = REQUIRED_COLS - set(df.columns)
     if missing:
```

The same tampered file, copied in again, with the catch in place:

```text
$ git status --short
 M data/raw/bike_daily.csv
 M src/config.py
 M src/ingest.py
$ make test
                f"{RAW_SHA256[:16]}...). Restore it with `git checkout -- data/raw/` "
                "or, if the change is intended, review it and update RAW_SHA256.")
E           ValueError: bike_daily.csv has changed (sha256 8a33aa5ae9cd9fea..., expected a6bed1577f6e4de5...). Restore it with `git checkout -- data/raw/` or, if the change is intended, review it and update RAW_SHA256.

src/ingest.py:27: ValueError
=========================== short test summary info ============================
ERROR tests/test_contract.py::test_every_raw_column_is_classified - ValueErro...
ERROR tests/test_contract.py::test_calendar_is_complete_before_lagging - Valu...
ERROR tests/test_contract.py::test_only_expected_rows_are_dropped - ValueErro...
ERROR tests/test_contract.py::test_beats_the_mean_baseline - ValueError: bike...
ERROR tests/test_leakage.py::test_leakage_identity_holds - ValueError: bike_d...
ERROR tests/test_leakage.py::test_no_forbidden_features - ValueError: bike_da...
ERROR tests/test_leakage.py::test_lags_are_true_calendar_lags - ValueError: b...
ERROR tests/test_leakage.py::test_lag_is_not_the_target - ValueError: bike_da...
ERROR tests/test_leakage.py::test_rolling_mean_excludes_today - ValueError: b...
ERROR tests/test_leakage.py::test_roll_3_is_mean_of_three_prior_days - ValueE...
ERROR tests/test_leakage.py::test_no_feature_reconstructs_the_target - ValueE...
ERROR tests/test_leakage.py::test_validation_score_is_not_too_good - ValueErr...
ERROR tests/test_leakage.py::test_no_missing_values - ValueError: bike_daily....
ERROR tests/test_leakage.py::test_dates_are_sorted_and_unique - ValueError: b...
ERROR tests/test_split.py::test_splits_non_empty - ValueError: bike_daily.csv...
ERROR tests/test_split.py::test_splits_are_ordered_in_time - ValueError: bike...
ERROR tests/test_split.py::test_no_overlapping_dates - ValueError: bike_daily...
2 passed, 17 errors in 0.77s
make: *** [test] Error 1
$ make all
    ...<2 lines>...
        "or, if the change is intended, review it and update RAW_SHA256.")
ValueError: bike_daily.csv has changed (sha256 8a33aa5ae9cd9fea..., expected a6bed1577f6e4de5...). Restore it with `git checkout -- data/raw/` or, if the change is intended, review it and update RAW_SHA256.
make: *** [data] Error 1
```

Restored with `git checkout -- data/raw/`: the hash is back to
`a6bed1577f6e4de5`, 19 tests pass, and `make all` reproduces
`reports/metrics.json` byte for byte.

*Interaction with the unclassified-column test.* With this guard in place, a
column appended to the raw CSV is stopped by the hash before
`test_every_raw_column_is_classified` reaches its own assertion: that test
errors with the hash message instead of failing with its own. It stays as
the second line of defence for the case the hash cannot see, a new file
whose hash was deliberately updated, and it was shown to fail on an appended
column in `8137cfd`, before the guard existed.
