"""
Recursive multi-step forecasting, t+1 through t+6.

The model predicts exactly one hour ahead. To reach six hours we predict t+1,
append that prediction to the history as the newest lag, predict t+2 from it,
and so on.

Two assumptions are baked into this and BOTH are reported in the API response
rather than hidden:

1. Exogenous features (temperature, humidity, CO, benzene, NO2) are held at
   their last observed values. We do not have a weather forecast, and inventing
   one would be fabricating input data.
2. From t+2 onward the lag features are fed by our own predictions, not by
   measurements. Errors therefore compound with the horizon, which is why the
   later cards in the UI deserve less trust than the earlier ones.
"""
import numpy as np
import pandas as pd

from app.features import EXOG, hour_cyclical
from app.risk import classify

ASSUMPTION = 'exogenous features held constant'
ASSUMPTION_DETAIL = (
    'Temperature, humidity and co-pollutants are held at their last observed '
    'values; from t+2 the NOx lags are fed by the model\'s own predictions, so '
    'uncertainty grows with the horizon.'
)

# nox_lag_24 and nox_roll_24 need two dozen hours of history to be defined.
MIN_HISTORY = 24


def recursive_forecast(d, model, features, horizon=6):
    """
    d       cleaned dataframe, ascending by datetime
    model   fitted estimator
    features    column order the model was trained on
    horizon number of hours ahead (1-6)
    """
    if len(d) < MIN_HISTORY:
        raise ValueError(f"need at least {MIN_HISTORY} rows of history, got {len(d)}")

    nox_hist = [float(v) for v in d['nox'].to_numpy()]
    last = d.iloc[-1]
    last_dt = pd.Timestamp(last['datetime'])

    # Held constant - see assumption 1 above.
    exog = {c: float(last[c]) for c in EXOG}

    results = []
    for step in range(1, horizon + 1):
        ts = last_dt + pd.Timedelta(hours=step)
        sin_h, cos_h = hour_cyclical(ts.hour)

        row = {
            'nox_lag_1': nox_hist[-1],
            'nox_lag_2': nox_hist[-2],
            'nox_lag_3': nox_hist[-3],
            'nox_lag_24': nox_hist[-24],
            'nox_roll_3': float(np.mean(nox_hist[-3:])),
            'nox_roll_24': float(np.mean(nox_hist[-24:])),
            'hour_sin': float(sin_h),
            'hour_cos': float(cos_h),
        }
        for c in EXOG:
            row[f'{c}_lag_1'] = exog[c]

        X = pd.DataFrame([row], columns=features)
        pred = float(model.predict(X)[0])
        pred = max(pred, 0.0)          # a negative concentration is meaningless

        results.append({
            'hour_offset': step,
            'timestamp': ts.isoformat(),
            'predicted_nox': round(pred, 1),
            'unit': 'ppb',
            # t+1 uses only measured inputs; later steps do not
            'inputs_measured': step == 1,
            **classify(pred),
        })

        nox_hist.append(pred)

    return results
