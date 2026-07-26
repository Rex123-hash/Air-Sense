"""
Feature engineering for AirSense.

This module is imported by BOTH train.py and the serving code. It is deliberately
the single source of truth: duplicating this logic between training and serving is
the classic way a forecasting project silently breaks (training/serving skew).

NO LEAKAGE RULE
---------------
Every feature must be knowable BEFORE the hour being predicted.

Co-pollutants and weather are therefore lagged by one hour. Using same-hour co,
benzene or no2 would be *nowcasting*, not forecasting: CO and NOx correlate at
0.94 in this dataset (measured, not assumed), so feeding them in at time t
inflates the score from a genuine ~26% improvement over baseline to a misleading
one. The honest answer to "what did the model know at prediction time?" must be
"only the past".
"""
import numpy as np

# Column order is part of the model contract. It is persisted alongside the
# fitted estimator in forecaster.pkl and re-checked at load time.
FEATURES = [
    'nox_lag_1', 'nox_lag_2', 'nox_lag_3', 'nox_lag_24',
    'nox_roll_3', 'nox_roll_24',
    'hour_sin', 'hour_cos',
    'co_lag_1', 'benzene_lag_1', 'no2_lag_1', 'temp_lag_1', 'humidity_lag_1',
]

TARGET = 'nox'

# Exogenous series that get lagged by one hour.
EXOG = ('co', 'benzene', 'no2', 'temp', 'humidity')

NOX_LAGS = (1, 2, 3, 24)


def hour_cyclical(hour):
    """Hour-of-day as a cyclical pair, so hour 23 sits next to hour 0."""
    return (np.sin(2 * np.pi * hour / 24), np.cos(2 * np.pi * hour / 24))


def build_features(d):
    """
    Add the FEATURES columns to a cleaned dataframe.

    Expects columns: datetime, hour, co, benzene, nox, no2, temp, humidity,
    sorted ascending by datetime. Rows made NaN by lagging are the caller's
    problem to drop (train drops them; serving slices a known-good tail).

    NOTE: shifts are positional, not time-aware. The cleaned slice contains 63
    gaps that are not exactly one hour, so nox_lag_1 occasionally spans a gap
    rather than a true single hour. That affects ~3% of rows and is documented
    as a limitation in the README rather than silently ignored.
    """
    f = d.copy()

    for lag in NOX_LAGS:
        f[f'nox_lag_{lag}'] = f[TARGET].shift(lag)

    # shift(1) first so the window never includes the hour being predicted.
    f['nox_roll_3'] = f[TARGET].shift(1).rolling(3).mean()
    f['nox_roll_24'] = f[TARGET].shift(1).rolling(24).mean()

    f['hour_sin'], f['hour_cos'] = hour_cyclical(f['hour'])

    for c in EXOG:
        f[f'{c}_lag_1'] = f[c].shift(1)

    return f
