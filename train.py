"""
AirSense - model training. Runs OFFLINE, never at request time.

    python train.py

Outputs (all committed to the repo):
    data/air_quality.csv      cleaned hourly series, served by the API
    models/forecaster.pkl     fitted estimator + feature order
    models/metrics.json       validation results, cleaning log, live insight

The server only loads and predicts. Training at startup would blow the Cloud Run
container start budget.
"""
import json
import os
import sys
import urllib.request

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.features import FEATURES, TARGET, build_features  # noqa: E402

RAW_URL = ("https://raw.githubusercontent.com/cmertin/Machine_Learning/"
           "master/Air_Quality_Prediction/Data/AirQuality_clean.csv")

# The file has no header row. Column order matters and the first three are
# Month, Day, Year -- NOT Day, Month, Year. Getting this wrong produces
# impossible dates like 2004-13-03, so it is asserted below.
RAW_COLS = ['Month', 'Day', 'Year', 'Hour', 'CO_GT', 'PT08_S1_CO', 'NMHC_GT',
            'C6H6_GT', 'PT08_S2_NMHC', 'NOx_GT', 'PT08_S3_NOx', 'NO2_GT',
            'PT08_S4_NO2', 'PT08_S5_O3', 'T', 'RH', 'AH',
            'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7']

SENTINEL = -200          # the device's sensor-failure marker, not a reading
N_ROWS = 2000            # contiguous slice; enough for a real 80/20 time split
FEAT_COLS = ['co', 'benzene', 'nox', 'no2', 'temp', 'humidity']

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(ROOT, 'data', 'air_quality.csv')
MODEL_PKL = os.path.join(ROOT, 'models', 'forecaster.pkl')
METRICS_JSON = os.path.join(ROOT, 'models', 'metrics.json')
RAW_CACHE = os.path.join(ROOT, 'raw.csv')


# ---------------------------------------------------------------- load + clean
def load_and_clean():
    if not os.path.exists(RAW_CACHE):
        print(f"downloading {RAW_URL}")
        urllib.request.urlretrieve(RAW_URL, RAW_CACHE)

    df = pd.read_csv(RAW_CACHE, header=None, names=RAW_COLS)

    assert df['Month'].between(1, 12).all(), \
        "Month column out of range 1-12 - the date columns are in the wrong order"
    assert df['Day'].between(1, 31).all(), \
        "Day column out of range 1-31 - the date columns are in the wrong order"

    df = df.head(N_ROWS).copy()
    rows_raw = len(df)

    d = pd.DataFrame({
        'datetime': pd.to_datetime(dict(year=df['Year'], month=df['Month'],
                                        day=df['Day'], hour=df['Hour'])),
        'hour': df['Hour'].astype(int),
        'co': df['CO_GT'], 'benzene': df['C6H6_GT'], 'nox': df['NOx_GT'],
        'no2': df['NO2_GT'], 'temp': df['T'], 'humidity': df['RH'],
    })
    # float so the sentinel can be replaced by NaN without an integer upcast
    d[FEAT_COLS] = d[FEAT_COLS].astype('float64')

    # 1. -200 means the sensor failed. Treating it as a real reading would
    #    poison the model. This source was already cleaned upstream, so the
    #    count below is honestly 0 -- the guard stays because a raw UCI file
    #    would contain thousands.
    sentinels_replaced = int((d[FEAT_COLS] == SENTINEL).sum().sum())
    d[FEAT_COLS] = d[FEAT_COLS].replace(SENTINEL, np.nan)

    # 2. cannot train on an unknown answer
    before = len(d)
    d = d.dropna(subset=[TARGET])
    rows_dropped_missing_target = before - len(d)

    # 3. time series: the previous hour is the best guess for a gap, median as
    #    the fallback for any leading NaN that ffill cannot reach
    nulls_filled = int(d[FEAT_COLS].isna().sum().sum())
    d[FEAT_COLS] = d[FEAT_COLS].ffill()
    d[FEAT_COLS] = d[FEAT_COLS].fillna(d[FEAT_COLS].median())

    # 4. exact duplicate timestamps
    before = len(d)
    d = d.drop_duplicates(subset=['datetime'])
    duplicates_removed = before - len(d)

    # 5. chronological order, so positional shifts mean "earlier"
    d = d.sort_values('datetime').reset_index(drop=True)

    d.to_csv(DATA_CSV, index=False)

    gaps = int((d['datetime'].diff().dropna() != pd.Timedelta('1h')).sum())
    cleaning = {
        'rows_raw': rows_raw,
        'rows_clean': len(d),
        'sentinels_replaced': sentinels_replaced,
        'rows_dropped_missing_target': rows_dropped_missing_target,
        'nulls_filled': nulls_filled,
        'duplicates_removed': duplicates_removed,
        'non_hourly_gaps': gaps,
        'source_pre_cleaned': sentinels_replaced == 0,
    }

    print("CLEANING:", json.dumps(cleaning, indent=2))
    print("date range:", d['datetime'].min(), "->", d['datetime'].max())
    if sentinels_replaced == 0:
        print("  note: 0 sentinels found - this source file was cleaned upstream.")
    return d, cleaning


# ----------------------------------------------------------------------- train
def main():
    d, cleaning = load_and_clean()

    f = build_features(d).dropna().reset_index(drop=True)
    X, y = f[FEATURES], f[TARGET]

    # CHRONOLOGICAL split. A shuffled train_test_split would leak the future
    # into training and produce a fraudulently good score.
    split = int(len(f) * 0.8)
    X_tr, X_te = X.iloc[:split], X.iloc[split:]
    y_tr, y_te = y.iloc[:split], y.iloc[split:]
    assert f['datetime'].iloc[split - 1] < f['datetime'].iloc[split], \
        "test set must start strictly after the training set ends"

    model = GradientBoostingRegressor(n_estimators=300, max_depth=4,
                                      learning_rate=0.05, random_state=42)
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)

    # Baseline: persistence -- predict next hour == current hour. The honest
    # naive benchmark. Beating it is the whole claim.
    base = X_te['nox_lag_1'].to_numpy()

    m_mae = float(mean_absolute_error(y_te, pred))
    m_rmse = float(np.sqrt(mean_squared_error(y_te, pred)))
    m_r2 = float(r2_score(y_te, pred))
    b_mae = float(mean_absolute_error(y_te, base))
    b_rmse = float(np.sqrt(mean_squared_error(y_te, base)))
    improvement = (b_mae - m_mae) / b_mae * 100

    # The headline insight, computed live. Never hardcode this number.
    prof = d.groupby('hour')[TARGET].mean()
    evening = float(prof.loc[18:21].mean())     # 6-9 PM traffic window
    overnight = float(prof.loc[3:6].mean())     # 3-6 AM trough

    metrics = {
        'model': {'mae': round(m_mae, 2), 'rmse': round(m_rmse, 2),
                  'r2': round(m_r2, 3)},
        'baseline_persistence': {'mae': round(b_mae, 2), 'rmse': round(b_rmse, 2)},
        'improvement_pct_mae': round(improvement, 1),
        'beats_baseline': bool(m_mae < b_mae),
        'n_train': int(len(X_tr)),
        'n_test': int(len(X_te)),
        'test_period': {'start': str(f['datetime'].iloc[split]),
                        'end': str(f['datetime'].iloc[-1])},
        'train_period': {'start': str(f['datetime'].iloc[0]),
                         'end': str(f['datetime'].iloc[split - 1])},
        'target': 'nox',
        'target_unit': 'ppb',
        'daily_profile': {str(h): round(float(v), 1) for h, v in prof.items()},
        'peak_insight': {
            'evening_window': '18:00-21:00',
            'overnight_window': '03:00-06:00',
            'evening_mean_nox': round(evening, 1),
            'overnight_mean_nox': round(overnight, 1),
            'ratio': round(evening / overnight, 1),
        },
        'feature_importance': sorted(
            [{'feature': c, 'importance': round(float(i), 4)}
             for c, i in zip(FEATURES, model.feature_importances_)],
            key=lambda x: -x['importance']),
        'cleaning': cleaning,
        'trained_with': {'scikit_learn': sklearn.__version__,
                         'numpy': np.__version__,
                         'pandas': pd.__version__,
                         'python': sys.version.split()[0]},
    }

    joblib.dump({'model': model, 'features': FEATURES,
                 'sklearn_version': sklearn.__version__}, MODEL_PKL)
    with open(METRICS_JSON, 'w') as fh:
        json.dump(metrics, fh, indent=2)

    print("\n=== VALIDATION (held-out chronological test set) ===")
    print(f"  model     MAE {m_mae:7.2f}   RMSE {m_rmse:7.2f}   R2 {m_r2:.3f}")
    print(f"  baseline  MAE {b_mae:7.2f}   RMSE {b_rmse:7.2f}   (persistence)")
    print(f"  improvement over baseline: {improvement:.1f}%")
    print(f"  train {len(X_tr)} rows / test {len(X_te)} rows")
    print(f"  train {metrics['train_period']['start']} -> {metrics['train_period']['end']}")
    print(f"  test  {metrics['test_period']['start']} -> {metrics['test_period']['end']}")
    print(f"\n  peak insight: evening {evening:.0f} ppb vs overnight "
          f"{overnight:.0f} ppb = {evening / overnight:.1f}x")
    print("  top features:",
          ", ".join(x['feature'] for x in metrics['feature_importance'][:4]))

    if m_mae >= b_mae:
        print("\n  WARNING: the model does NOT beat persistence. Report this "
              "honestly; do not present it as a win.")
    if m_r2 > 0.9:
        print("\n  WARNING: R2 above 0.90 on this data suggests leakage has "
              "been reintroduced. Re-check app/features.py.")


if __name__ == '__main__':
    main()
