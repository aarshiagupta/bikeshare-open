"""The tests that make the agent honest.

test_no_forbidden_features is the single most valuable test in this repo:
casual + registered == cnt exactly, so any model handed those columns
scores R^2 = 1.0 and looks brilliant while having learned nothing.
"""
import pandas as pd
import pytest

from itertools import combinations

from sklearn.metrics import r2_score

from src.config import FORBIDDEN, TARGET
from src.features import build_features, encode_weather, feature_columns
from src.ingest import load_raw
from src.train import MODELS, temporal_split


@pytest.fixture(scope="module")
def feats():
    return build_features(load_raw())


def test_leakage_identity_holds(feats):
    """Documents *why* casual and registered are forbidden."""
    assert (feats.casual + feats.registered == feats[TARGET]).all()


def test_no_forbidden_features(feats):
    """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
    construction, so this cannot discover a *new* leaky column. What it
    catches is someone editing feature_columns() or FORBIDDEN -- which is
    exactly the fault the Step 7 hook demonstrates."""
    cols = set(feature_columns(feats))
    assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"


def test_lags_are_true_calendar_lags(feats):
    """cnt_lag_1 for date d must equal cnt on d-1, in calendar days."""
    by_date = feats.set_index("dteday")[TARGET]
    checked = 0
    for date, lag in feats.set_index("dteday").cnt_lag_1.items():
        prev = date - pd.Timedelta(days=1)
        if prev in by_date.index:
            assert lag == pytest.approx(by_date[prev]), f"bad lag at {date.date()}"
            checked += 1
    assert checked > 600, "too few rows actually verified"


def test_lag_is_not_the_target(feats):
    assert not (feats.cnt_lag_1 == feats[TARGET]).all()


def test_rolling_mean_excludes_today(feats):
    """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
    by_date = feats.set_index("dteday")[TARGET]
    date = feats.dteday.iloc[200]
    window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
    if all(d in by_date.index for d in window):
        expected = sum(by_date[d] for d in window) / 7
        assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)


def test_roll_3_is_mean_of_three_prior_days(feats):
    """cnt_roll_3 on 2011-06-15 must be the mean of cnt on 06-12, 06-13, 06-14,
    read by hand from data/raw/bike_daily.csv: (4460 + 5020 + 4891) / 3.
    Same-day cnt is 5180, so a window that includes today gives a different
    number and fails here."""
    row = feats.set_index("dteday").loc[pd.Timestamp("2011-06-15")]
    assert row.cnt_roll_3 == pytest.approx((4460 + 5020 + 4891) / 3)
    assert row.cnt_roll_3 != pytest.approx(row[TARGET])


def test_unknown_weather_label_raises():
    """encode_weather must fail loudly on a label it does not know. A silent
    .map() turns it into NaN and dropna() deletes the day without a word.
    No row in the real data exercises this, so only a direct call can."""
    with pytest.raises(ValueError, match="unmapped weather"):
        encode_weather(pd.Series(["GOOD", "SNOW"]))


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
            assert abs(feats[c].corr(feats[f])) < 0.99, f"{c} is a near-copy of forbidden {f}"
    for a, b in combinations(cols, 2):
        assert not (feats[a] + feats[b] == y).all(), f"{a} + {b} equals {TARGET}"


def test_validation_score_is_not_too_good(feats):
    """Honest ridge scores ~0.65 on validation. A same-day leak sends it to ~1.
    Anything above 0.95 is treated as leakage until proven otherwise."""
    cols = feature_columns(feats)
    train, valid, _ = temporal_split(feats)
    ridge = MODELS["ridge"].fit(train[cols], train[TARGET])
    assert r2_score(valid[TARGET], ridge.predict(valid[cols])) < 0.95


def test_no_missing_values(feats):
    assert feats[feature_columns(feats)].isna().sum().sum() == 0


def test_dates_are_sorted_and_unique(feats):
    assert feats.dteday.is_monotonic_increasing
    assert feats.dteday.is_unique
