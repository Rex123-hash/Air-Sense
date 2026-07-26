# Base image note:
#   The PRD specified python:3.11-slim. That is not usable here -- pandas 3.0.2
#   (the version that trained the model) publishes no cp311 wheel; the newest
#   pandas for Python 3.11 is 2.3.2. Rather than downgrade pandas away from the
#   training environment, the container matches the environment the model was
#   actually trained in: Python 3.14. Verified that all six pinned
#   dependencies publish manylinux_2_28 cp314 wheels, which this Debian base
#   (glibc >= 2.28) satisfies, so the build needs no compiler.
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first so this layer caches across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Fail the build rather than the deploy if the offline artefacts are missing.
RUN test -f models/forecaster.pkl && test -f models/metrics.json && test -f data/air_quality.csv

# Cloud Run injects PORT and requires binding 0.0.0.0 -- binding 127.0.0.1 is
# the single most common Cloud Run deploy failure. Shell form so ${PORT} expands.
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
