#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn chatty.main:socketio_app --host 0.0.0.0 --port "${APP_PORT:-8000}"
