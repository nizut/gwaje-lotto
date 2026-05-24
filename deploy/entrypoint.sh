#!/bin/sh
set -e

# Django 마이그레이션 및 정적파일 수집
echo "Running migrations..."
wait_for_db() {
  echo "Waiting for database to be available..."
  python - <<'PY'
import os, time, sys
from urllib.parse import urlparse
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
	# fallback to individual vars
	host = os.environ.get('DB_HOST', os.environ.get('POSTGRES_HOST', 'db'))
	port = int(os.environ.get('DB_PORT', os.environ.get('POSTGRES_PORT', 5432)))
	user = os.environ.get('DB_USER', os.environ.get('POSTGRES_USER', 'lotto'))
	password = os.environ.get('DB_PASSWORD', os.environ.get('POSTGRES_PASSWORD', 'lotto'))
	dbname = os.environ.get('DB_NAME', os.environ.get('POSTGRES_DB', 'lotto_db'))
	DSN = { 'host': host, 'port': port, 'user': user, 'password': password, 'dbname': dbname }
else:
	parsed = urlparse(DATABASE_URL)
	DSN = {
		'host': parsed.hostname or 'db',
		'port': parsed.port or 5432,
		'user': parsed.username or os.environ.get('POSTGRES_USER','lotto'),
		'password': parsed.password or os.environ.get('POSTGRES_PASSWORD','lotto'),
		'dbname': parsed.path.lstrip('/') or os.environ.get('POSTGRES_DB','lotto_db')
	}

max_tries = 30
for i in range(max_tries):
	try:
		conn = psycopg2.connect(**DSN)
		conn.close()
		print('Database available')
		sys.exit(0)
	except Exception as e:
		print(f'Waiting for db ({i+1}/{max_tries})... {e}')
		time.sleep(1)
print('Database did not become ready in time', file=sys.stderr)
sys.exit(1)
PY

}

wait_for_db

python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# 이후 전달된 CMD 실행 (예: gunicorn)
exec "$@"
