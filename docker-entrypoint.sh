#!/bin/bash
set -euo pipefail

# shellcheck disable=SC1091
if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

export FLASK_APP=${FLASK_APP:-run.py}

echo "Running database migrations..."
flask db upgrade

echo "Starting application (FLASK_ENV=${FLASK_ENV:-production})..."
if [ "${FLASK_ENV:-production}" = "development" ]; then
  exec python run.py
else
  export FLASK_ENV=production
  exec python run.py
fi
