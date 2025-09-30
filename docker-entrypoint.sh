#!/bin/bash
set -euo pipefail

# shellcheck disable=SC1091
if [ "${LOAD_ENV_FROM_FILE:-true}" = "true" ] && [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

export FLASK_APP=${FLASK_APP:-run.py}
: "${FLASK_ENV:=production}"
export FLASK_ENV

echo "Running database migrations..."
flask db upgrade

echo "Starting application (FLASK_ENV=${FLASK_ENV})..."
if [ "${FLASK_ENV}" = "development" ]; then
  exec python run.py
else
  exec python run.py
fi
