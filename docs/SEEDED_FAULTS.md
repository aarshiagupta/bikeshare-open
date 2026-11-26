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

**Hook stderr** (fired on the Edit, before anyone ran a test):

```text
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /Users/aarshiagupta/Documents/dsc180a/ma6/bikeshare-open/src/features.py:
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
```

**Red test output** (`python -m pytest tests/ -q`):

```text
F.....F............                                                      [100%]
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
=========================== short test summary info ============================
FAILED tests/test_contract.py::test_every_raw_column_is_classified - Assertio...
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
2 failed, 17 passed in 0.83s
```

**Turns to fix: 4.** The fix session found the `+ ["casual"]`, removed it,
and confirmed 19 passed; `git diff` was empty afterwards. Two independent
tests caught it: the starter's FORBIDDEN gate, and the new unclassified-column
contract test (a raw column reached the model without being in
`RAW_FEATURE_COLS`). The "too good to be true" test did not fire: `casual`
alone does not push validation ridge R^2 over 0.95.
