#!/bin/sh
set -eu

cd /app/fresh_exchange

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "Preparing the Gather marketplace database..."
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
fi

if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
    echo "Checking Gather demonstration data..."
    python manage.py seed_market
fi

exec "$@"
