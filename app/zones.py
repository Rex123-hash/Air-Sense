"""
Campus zone view.

HONESTY NOTE - READ THIS BEFORE CHANGING ANYTHING HERE
------------------------------------------------------
We have ONE sensor stream, not four. These four zones are derived from that
single stream by a fixed, documented multiplier reflecting how exposed each
location is to traffic. They are NOT four independent sensors.

Every response from this module carries "simulated": true, and the UI is
required to render the words "simulated zone offset - single sensor stream"
visibly. Presenting four derived numbers as four real sensors would be the
fastest way to lose credibility with an evaluator. Framed honestly, this is a
perfectly good demonstration of the multi-zone design that a real deployment
would use.
"""
from app.risk import classify

ZONES = [
    {'name': 'Main Gate',     'multiplier': 1.25,
     'rationale': 'Directly traffic-exposed - vehicle queue at entry'},
    {'name': 'Parking Block', 'multiplier': 1.15,
     'rationale': 'Cold starts and idling vehicles'},
    {'name': 'Central Lawn',  'multiplier': 0.90,
     'rationale': 'Open ground, set back from the road'},
    {'name': 'Library Block', 'multiplier': 0.80,
     'rationale': 'Sheltered, furthest from the carriageway'},
]

DISCLAIMER = 'simulated zone offset - single sensor stream'


def zone_status(base_nox):
    """Derive per-zone readings from the one real measured value."""
    out = []
    for z in ZONES:
        nox = round(float(base_nox) * z['multiplier'], 1)
        out.append({
            'name': z['name'],
            'nox': nox,
            'unit': 'ppb',
            'multiplier': z['multiplier'],
            'rationale': z['rationale'],
            'simulated': True,
            **classify(nox),
        })
    return {
        'measured_nox': round(float(base_nox), 1),
        'unit': 'ppb',
        'simulated': True,
        'disclaimer': DISCLAIMER,
        'zones': out,
    }
