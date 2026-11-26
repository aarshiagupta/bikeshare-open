# Seeded faults (Exercise 2)

Every block below is pasted output, not a description of it.

**Method.** Each fault is seeded with the repo's own  skill in a
headless Claude Code session (, model ) started in
the repo root, so  and its PostToolUse hook are live.
The fault is then fixed by a **second, fresh session** that is told only
"python -m pytest tests/ -q
...................                                                      [100%]
=============================== warnings summary ===============================
tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/utils/extmath.py:203: RuntimeWarning: divide by zero encountered in matmul
    ret = a @ b

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/utils/extmath.py:203: RuntimeWarning: overflow encountered in matmul
    ret = a @ b

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/utils/extmath.py:203: RuntimeWarning: invalid value encountered in matmul
    ret = a @ b

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/linear_model/_base.py:279: RuntimeWarning: divide by zero encountered in matmul
    return X @ coef_ + self.intercept_

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/linear_model/_base.py:279: RuntimeWarning: overflow encountered in matmul
    return X @ coef_ + self.intercept_

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/linear_model/_base.py:279: RuntimeWarning: invalid value encountered in matmul
    return X @ coef_ + self.intercept_

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
19 passed, 12 warnings in 2.49s is failing in this repo. Find the cause and fix it. Do not edit
anything under tests/." It is not told what was broken. "Turns to fix" is that
session's  as reported by Claude Code. The hook stderr is copied
from the session transcript ( attachment), i.e. exactly
what the agent was shown. All four faults were run against the final test
suite (19 tests), so the output below is what the suite prints today.

## 0. The feature test, failing before the feature existed

Commit  added  before
 existed. Output of ...................                                                      [100%]
=============================== warnings summary ===============================
tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/utils/extmath.py:203: RuntimeWarning: divide by zero encountered in matmul
    ret = a @ b

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/utils/extmath.py:203: RuntimeWarning: overflow encountered in matmul
    ret = a @ b

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/utils/extmath.py:203: RuntimeWarning: invalid value encountered in matmul
    ret = a @ b

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/linear_model/_base.py:279: RuntimeWarning: divide by zero encountered in matmul
    return X @ coef_ + self.intercept_

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/linear_model/_base.py:279: RuntimeWarning: overflow encountered in matmul
    return X @ coef_ + self.intercept_

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/linear_model/_base.py:279: RuntimeWarning: invalid value encountered in matmul
    return X @ coef_ + self.intercept_

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
19 passed, 12 warnings in 0.69s at that commit:



It fails for the right reason: the column does not exist yet. Commit
 adds the feature and the suite goes green.

## 1. A forbidden column added to 

**Exact change** (seeded by ):



**Hook stderr** (fired on the Edit, before anyone ran a test):



**Red test output** (...................                                                      [100%]
=============================== warnings summary ===============================
tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/utils/extmath.py:203: RuntimeWarning: divide by zero encountered in matmul
    ret = a @ b

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/utils/extmath.py:203: RuntimeWarning: overflow encountered in matmul
    ret = a @ b

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/utils/extmath.py:203: RuntimeWarning: invalid value encountered in matmul
    ret = a @ b

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/linear_model/_base.py:279: RuntimeWarning: divide by zero encountered in matmul
    return X @ coef_ + self.intercept_

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/linear_model/_base.py:279: RuntimeWarning: overflow encountered in matmul
    return X @ coef_ + self.intercept_

tests/test_contract.py::test_beats_the_mean_baseline
tests/test_leakage.py::test_validation_score_is_not_too_good
  /Users/aarshiagupta/miniforge3/lib/python3.12/site-packages/sklearn/linear_model/_base.py:279: RuntimeWarning: invalid value encountered in matmul
    return X @ coef_ + self.intercept_

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
19 passed, 12 warnings in 0.71s):



**Turns to fix: 4.** The fix session found the , removed it,
and confirmed 19 passed;  was empty afterwards. Two independent
tests caught it: the starter's FORBIDDEN gate and the new
unclassified-column contract test (it sees a raw column in the model that is
not in ). Not caught by the "too good" test:  alone
does not push validation ridge R^2 over 0.95.
