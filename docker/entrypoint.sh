#!/bin/sh
set -e
cd /app
# Синхронизация static → volume для nginx (/var/www/static)
python manage.py collectstatic --noinput 2>/dev/null || true
exec "$@"
