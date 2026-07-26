"""
Risk banding and recommended actions.

IMPORTANT: these thresholds are PROJECT-DEFINED operational bands for
demonstration purposes. They are NOT official CPCB or WHO air-quality
standards and must never be labelled as government AQI categories. The
value of the band is that it maps a number to a decision someone can act on.
"""

# (band, colour name, hex for the UI, inclusive lower bound, exclusive upper bound)
BANDS = [
    ('Low',      'green',  '#22c55e',    0,  100),
    ('Moderate', 'amber',  '#f59e0b',  100,  200),
    ('High',     'orange', '#f97316',  200,  300),
    ('Severe',   'red',    '#ef4444',  300,  float('inf')),
]

ACTIONS = {
    'Low':      'Normal operations. Good window for outdoor activity.',
    'Moderate': 'Prefer indoor activity for sensitive individuals. Monitor.',
    'High':     'Increase ventilation/filtration indoors. Move outdoor sessions indoors.',
    'Severe':   'Avoid outdoor activity. Maximise filtration. Consider staggering exit timings.',
}

THRESHOLD_NOTE = ('Project-defined operational bands for demonstration - '
                  'not official CPCB/WHO standards.')

# Bands at or above which we consider the hour worth warning about in advance.
ALERT_BANDS = ('High', 'Severe')


def classify(nox):
    """Map a NOx value in ppb to its band, colour and recommended action."""
    value = max(float(nox), 0.0)
    for band, colour, hex_code, lo, hi in BANDS:
        if lo <= value < hi:
            return {
                'risk_band': band,
                'risk_color': colour,
                'risk_hex': hex_code,
                'recommended_action': ACTIONS[band],
            }
    # unreachable: the last band is open-ended
    raise ValueError(f"could not classify nox={nox}")


def is_alert(band):
    return band in ALERT_BANDS


def band_reference():
    """The band table, for the UI to render its own legend without hardcoding."""
    return {
        'note': THRESHOLD_NOTE,
        'unit': 'ppb',
        'bands': [
            {'band': b, 'color': c, 'hex': h,
             'min': lo, 'max': (None if hi == float('inf') else hi),
             'recommended_action': ACTIONS[b]}
            for b, c, h, lo, hi in BANDS
        ],
    }
