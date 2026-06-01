#!/usr/bin/env bash
# Авто-перевыпуск, если до конца срока < RENEW_BEFORE_DAYS (cron/systemd).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${SSL_ENV_FILE:-config/ssl-selfsigned.env}"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

RENEW_BEFORE_DAYS="${RENEW_BEFORE_DAYS:-30}"
CERT="$ROOT/config/nginx/certs/fullchain.pem"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.selfsigned.yml"
LOG_TAG="[shoshop-ssl-renew]"

_log() { echo "$(date -Is) $LOG_TAG $*"; }

if [[ ! -f "$CERT" ]]; then
  _log "Сертификата нет — создаём"
  bash "$ROOT/scripts/ssl-selfsigned.sh" --force
  exit 0
fi

end=$(openssl x509 -enddate -noout -in "$CERT" | cut -d= -f2)
end_s=$(date -d "$end" +%s)
now_s=$(date +%s)
left=$(( (end_s - now_s) / 86400 ))

if [[ "$left" -lt "$RENEW_BEFORE_DAYS" ]]; then
  _log "Осталось ${left} дн. (< ${RENEW_BEFORE_DAYS}) — перевыпуск"
  bash "$ROOT/scripts/ssl-selfsigned.sh" --force
  if $COMPOSE ps nginx 2>/dev/null | grep -qE 'Up|running'; then
    _log "Перезапуск nginx"
    $COMPOSE restart nginx
  fi
  _log "Готово"
else
  _log "OK, до истечения ${left} дн."
fi
