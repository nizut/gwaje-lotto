#!/bin/sh
set -e

# Django 마이그레이션 및 정적파일 수집
echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# 이후 전달된 CMD 실행 (예: gunicorn)
exec "$@"
