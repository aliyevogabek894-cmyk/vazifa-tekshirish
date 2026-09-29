#!/usr/bin/env bash
set -o errexit

echo "=== Gunicorn serveri ishga tushmoqda ==="
exec gunicorn school_homework.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --threads 4 --worker-class gthread --log-file -
