#!/usr/bin/env bash
# Одной командой: конфиг + сертификат + подсказки по .env
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f config/ssl-selfsigned.env ]]; then
  cp config/ssl-selfsigned.env.example config/ssl-selfsigned.env
  echo "Создан config/ssl-selfsigned.env — отредактируйте SSL_IP и запустите снова."
  exit 0
fi

bash "$ROOT/scripts/ssl-selfsigned.sh" --force

echo ""
echo "=== Обновите /srv/shoshop/.env (см. config/env.docker.https-selfsigned.example) ==="
echo ""
echo "=== Запуск с HTTPS ==="
echo "docker compose -f docker-compose.yml -f docker-compose.selfsigned.yml up -d --force-recreate nginx web"
echo ""
echo "=== Авто-перевыпуск (cron, раз в неделю) ==="
echo "0 3 * * 0 root cd /srv/shoshop && ./scripts/ssl-selfsigned-renew.sh >> /var/log/shoshop-ssl-renew.log 2>&1"
