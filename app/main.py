"""
AirSense - FastAPI service.

ONE Cloud Run service serves both the JSON API (under /api) and the static
frontend (at /). Splitting them would double the deployment surface for no gain.

Nothing is trained here. The model and the cleaned data are artefacts produced
offline by train.py and committed to the repo; this process only loads and
predicts, so the container starts in well under Cloud Run's budget.
"""
import json
import os

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import risk, zones
from app.features import FEATURES, TARGET, build_features
from app.forecast import ASSUMPTION, ASSUMPTION_DETAIL, recursive_forecast

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(ROOT, 'data', 'air_quality.csv')
MODEL_PKL = os.path.join(ROOT, 'models', 'forecaster.pkl')
METRICS_JSON = os.path.join(ROOT, 'models', 'metrics.json')
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

READING_COLS = ['co', 'benzene', 'nox', 'no2', 'temp', 'humidity']

# The dataset is a historical hourly record (UCI, 2004), not a live feed. The
# API says so explicitly so the UI cannot imply otherwise.
DATA_MODE = 'historical dataset replay - not a live sensor feed'
MAX_HORIZON = 6

# Replay bookmarks.
#
# Because this is a historical series, "now" is a position we choose. These
# timestamps were found by scanning every vantage point in the data for hours
# where the model genuinely forecasts a High/Severe peak within 6 hours (586 of
# 1952 positions do). Curating the vantage point is honest; the forecast shown
# at each one is computed live from data up to that hour and nothing further.
# The default position remains the last row of the dataset.
DEMO_BOOKMARKS = [
    {'as_of': '2004-06-23T06:00:00', 'label': 'Peak inbound - alert in 2h'},
    {'as_of': '2004-06-21T04:00:00', 'label': 'Overnight trough before morning rush'},
    {'as_of': '2004-06-17T01:00:00', 'label': 'Quiet night, peak 6h out'},
    {'as_of': '2004-06-18T06:00:00', 'label': 'Morning build-up'},
]


def _load():
    for path in (DATA_CSV, MODEL_PKL, METRICS_JSON):
        if not os.path.exists(path):
            raise RuntimeError(
                f"missing artefact: {path}. Run `python train.py` first - the "
                f"server never trains at runtime.")

    d = pd.read_csv(DATA_CSV, parse_dates=['datetime'])
    d = d.sort_values('datetime').reset_index(drop=True)

    bundle = joblib.load(MODEL_PKL)
    model, features = bundle['model'], bundle['features']

    # Guard against a stale pickle whose feature order no longer matches the
    # shared feature module - that mismatch would silently produce garbage.
    from app.features import FEATURES
    if list(features) != list(FEATURES):
        raise RuntimeError(
            "feature order in forecaster.pkl does not match app/features.py. "
            "Re-run train.py.")

    with open(METRICS_JSON) as fh:
        metrics = json.load(fh)

    return d, model, features, metrics


DATA, MODEL, MODEL_FEATURES, METRICS = _load()

app = FastAPI(
    title='AirSense',
    description='Hyper-local air-quality forecasting. Predicts the NOx peak '
                'before it arrives and attaches a recommended action.',
    version='1.0.0',
)


def _reading(row):
    out = {'timestamp': pd.Timestamp(row['datetime']).isoformat(),
           'hour': int(row['hour'])}
    for c in READING_COLS:
        out[c] = round(float(row[c]), 1)
    return out


AS_OF_PARAM = Query(
    None,
    description='Replay position as an ISO timestamp. Returns the state as it '
                'would have been at that hour, using only data up to it. '
                'Defaults to the last row of the dataset.')


def _vantage(as_of):
    """
    Return the slice of history visible from a given replay position.

    Everything downstream sees only this slice, so a forecast issued from an
    earlier vantage point cannot accidentally consult later readings.
    """
    if as_of is None:
        return DATA
    try:
        ts = pd.Timestamp(as_of)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400,
                            detail=f"as_of is not a valid timestamp: {as_of!r}")

    visible = DATA[DATA['datetime'] <= ts]
    if len(visible) < 25:
        raise HTTPException(
            status_code=400,
            detail=f"as_of={ts.isoformat()} leaves {len(visible)} rows of "
                   f"history; at least 25 are needed for the 24-hour lags. "
                   f"Dataset covers {DATA['datetime'].min()} to "
                   f"{DATA['datetime'].max()}.")
    return visible.reset_index(drop=True)


# --------------------------------------------------------------------- routes
@app.get('/api/health')
def health():
    return {
        'status': 'ok',
        'rows_loaded': int(len(DATA)),
        'model_features': len(MODEL_FEATURES),
        'data_mode': DATA_MODE,
    }


@app.get('/api/current')
def current(as_of: str = AS_OF_PARAM):
    """The reading at the replay position, with its risk band and action."""
    visible = _vantage(as_of)
    row = visible.iloc[-1]
    nox = float(row['nox'])
    return {
        **_reading(row),
        **risk.classify(nox),
        'units': {'nox': 'ppb', 'no2': 'ppb', 'co': 'mg/m³',
                  'benzene': 'µg/m³', 'temp': '°C', 'humidity': '%'},
        'data_mode': DATA_MODE,
        'is_latest': bool(len(visible) == len(DATA)),
        'threshold_note': risk.THRESHOLD_NOTE,
    }


@app.get('/api/history')
def history(hours: int = Query(48, ge=1, le=336), as_of: str = AS_OF_PARAM):
    """Hourly readings up to the replay position, oldest first, for the chart."""
    tail = _vantage(as_of).tail(hours)
    return {
        'hours_requested': hours,
        'count': int(len(tail)),
        'unit': 'ppb',
        'readings': [{**_reading(r), 'risk_band': risk.classify(r['nox'])['risk_band']}
                     for _, r in tail.iterrows()],
    }


@app.get('/api/forecast')
def forecast(horizon: int = Query(MAX_HORIZON, ge=1, le=MAX_HORIZON),
             as_of: str = AS_OF_PARAM):
    """Recursive multi-step NOx forecast with a recommended action per hour."""
    visible = _vantage(as_of)
    try:
        steps = recursive_forecast(visible, MODEL, MODEL_FEATURES, horizon=horizon)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    alerts = [s for s in steps if risk.is_alert(s['risk_band'])]
    peak = max(steps, key=lambda s: s['predicted_nox'])

    return {
        'issued_from': pd.Timestamp(visible.iloc[-1]['datetime']).isoformat(),
        'horizon': horizon,
        'unit': 'ppb',
        'assumption': ASSUMPTION,
        'assumption_detail': ASSUMPTION_DETAIL,
        'data_mode': DATA_MODE,
        'threshold_note': risk.THRESHOLD_NOTE,
        'peak': {'hour_offset': peak['hour_offset'],
                 'predicted_nox': peak['predicted_nox'],
                 'risk_band': peak['risk_band']},
        # drives the "peak predicted in N hours - act now" banner
        'alert': ({'hours_ahead': alerts[0]['hour_offset'],
                   'risk_band': alerts[0]['risk_band'],
                   'predicted_nox': alerts[0]['predicted_nox'],
                   'recommended_action': alerts[0]['recommended_action']}
                  if alerts else None),
        'forecast': steps,
    }


@app.get('/api/metrics')
def metrics():
    """Validation results from the offline training run, verbatim."""
    return METRICS


# Computed on first request rather than at import, to keep the container's cold
# start inside Cloud Run's budget. It is a few milliseconds either way, but the
# startup path is the one that can fail a deploy.
_BACKTEST = None


def _compute_backtest():
    """
    Re-run the held-out test set through the model, hour by hour.

    This reproduces exactly the split train.py used: the same feature matrix,
    the same chronological 80/20 boundary. It exists so the accuracy claim can
    be SEEN rather than taken on trust -- every point is a real prediction
    compared against what actually happened.
    """
    f = build_features(DATA).dropna().reset_index(drop=True)
    split = int(len(f) * 0.8)
    test = f.iloc[split:]

    pred = MODEL.predict(test[MODEL_FEATURES])
    actual = test[TARGET].to_numpy(dtype=float)
    baseline = test['nox_lag_1'].to_numpy(dtype=float)   # persistence
    err = np.abs(pred - actual)

    rows = [{
        'timestamp': pd.Timestamp(t).isoformat(),
        'actual': round(float(a), 1),
        'predicted': round(float(p), 1),
        'baseline': round(float(b), 1),
        'abs_error': round(float(e), 1),
    } for t, a, p, b, e in zip(test['datetime'], actual, pred, baseline, err)]

    within = lambda tol: round(float((err <= tol).mean() * 100), 1)

    # Early-warning skill: the operational question is not "what is the average
    # error" but "when the air actually went High, did we say so beforehand?"
    # Threshold is the High band boundary, taken from risk.py rather than typed
    # in here, so the two can never disagree.
    high = next(lo for band, _c, _h, lo, _hi in risk.BANDS if band == 'High')
    actual_high = actual >= high
    pred_high = pred >= high
    hits = int((actual_high & pred_high).sum())
    misses = int((actual_high & ~pred_high).sum())
    false_alarms = int((~actual_high & pred_high).sum())
    pct = lambda n, d: (round(n / d * 100, 1) if d else None)

    return {
        'early_warning': {
            'threshold_ppb': high,
            'threshold_band': 'High',
            'actual_high_hours': int(actual_high.sum()),
            'correctly_warned': hits,
            'missed': misses,
            'false_alarms': false_alarms,
            'recall_pct': pct(hits, int(actual_high.sum())),
            'precision_pct': pct(hits, hits + false_alarms),
            'lead_time_hours': 1,
            'note': ('Of the hours that actually exceeded the High threshold, this is '
                     'the share the model flagged one hour in advance. Measured on the '
                     'held-out test set, not on data the model trained on.'),
        },
        'n_test': len(rows),
        'unit': 'ppb',
        'period': {'start': rows[0]['timestamp'], 'end': rows[-1]['timestamp']},
        'mae': round(float(err.mean()), 2),
        'baseline_mae': round(float(np.abs(baseline - actual).mean()), 2),
        'median_abs_error': round(float(np.median(err)), 2),
        'worst_abs_error': round(float(err.max()), 1),
        'within_25_ppb_pct': within(25),
        'within_50_ppb_pct': within(50),
        'note': ('Every point is a one-hour-ahead prediction made using only data '
                 'available before that hour, on data the model never saw in training.'),
        'rows': rows,
    }


@app.get('/api/backtest')
def backtest():
    """Actual vs predicted vs persistence baseline across the held-out test set."""
    global _BACKTEST
    if _BACKTEST is None:
        _BACKTEST = _compute_backtest()
    return _BACKTEST


@app.get('/api/zones')
def zone_view(as_of: str = AS_OF_PARAM):
    """
    Four campus zones derived from the ONE real sensor stream by a fixed
    multiplier. Flagged simulated because that is what it is.
    """
    return zones.zone_status(float(_vantage(as_of).iloc[-1]['nox']))


@app.get('/api/replay')
def replay():
    """
    Where the replay can be positioned, and a few curated bookmarks.

    The bookmarks exist so the forecast-alert banner can be demonstrated: the
    final hour of the dataset happens to be a flat one. See DEMO_BOOKMARKS.
    """
    return {
        'data_mode': DATA_MODE,
        'dataset_start': pd.Timestamp(DATA.iloc[0]['datetime']).isoformat(),
        'dataset_end': pd.Timestamp(DATA.iloc[-1]['datetime']).isoformat(),
        'default_as_of': pd.Timestamp(DATA.iloc[-1]['datetime']).isoformat(),
        'note': ('Forecasts are computed live from data up to the selected hour '
                 'only. Choosing the vantage point does not change the model.'),
        'bookmarks': DEMO_BOOKMARKS,
    }


@app.get('/api/daily-profile')
def daily_profile():
    """Mean NOx per hour-of-day, computed live from the cleaned data."""
    prof = DATA.groupby('hour')['nox'].mean()
    counts = DATA.groupby('hour')['nox'].size()
    insight = METRICS['peak_insight']
    return {
        'unit': 'ppb',
        'n_days_covered': round(len(DATA) / 24, 1),
        'profile': [{'hour': int(h), 'mean_nox': round(float(v), 1),
                     'n_observations': int(counts.loc[h])}
                    for h, v in prof.items()],
        'evening_window': insight['evening_window'],
        'overnight_window': insight['overnight_window'],
        'evening_mean_nox': insight['evening_mean_nox'],
        'overnight_mean_nox': insight['overnight_mean_nox'],
        'ratio': insight['ratio'],
        'caption': (f"Evening peak averages {insight['ratio']}x overnight levels "
                    f"({insight['evening_mean_nox']} ppb vs "
                    f"{insight['overnight_mean_nox']} ppb)."),
    }


@app.get('/api/risk-bands')
def risk_bands():
    """The band table, so the UI legend is never hardcoded."""
    return risk.band_reference()


@app.exception_handler(404)
def not_found(request, exc):
    if request.url.path.startswith('/api/'):
        return JSONResponse({'detail': 'no such endpoint'}, status_code=404)
    return JSONResponse({'detail': 'not found'}, status_code=404)


# Mounted LAST so the /api routes above take precedence.
app.mount('/', StaticFiles(directory=STATIC_DIR, html=True), name='static')
