#!/usr/bin/env bash
# Генерация/перевыпуск самоподписанного сертификата для nginx (тест).
# Использование: ./scripts/ssl-selfsigned.sh [--force]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${SSL_ENV_FILE:-config/ssl-selfsigned.env}"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

FORCE=false
if [[ "${1:-}" == "--force" ]]; then
  FORCE=true
fi

SSL_IP="${SSL_IP:-}"
SSL_DNS="${SSL_DNS:-localhost}"
SSL_CN="${SSL_CN:-${SSL_IP:-$SSL_DNS}}"
SSL_DAYS="${SSL_DAYS:-90}"

CERT_DIR="$ROOT/config/nginx/certs"
FULLCHAIN="$CERT_DIR/fullchain.pem"
PRIVKEY="$CERT_DIR/privkey.pem"

mkdir -p "$CERT_DIR"

_build_san() {
  local san="" part
  local IFS=,
  for part in $SSL_DNS; do
    part="${part// /}"
    [[ -z "$part" ]] && continue
    [[ -n "$san" ]] && san+=","
    san+="DNS:${part}"
  done
  if [[ -n "$SSL_IP" ]]; then
    [[ -n "$san" ]] && san+=","
    san+="IP:${SSL_IP}"
  fi
  if [[ -z "$san" ]]; then
    echo "Укажите SSL_IP и/или SSL_DNS в $ENV_FILE" >&2
    exit 1
  fi
  echo "$san"
}

if [[ -f "$FULLCHAIN" && "$FORCE" != true ]]; then
  echo "Сертификат уже есть: $FULLCHAIN"
  echo "Перевыпуск: $0 --force"
  openssl x509 -in "$FULLCHAIN" -noout -subject -dates
  exit 0
fi

SAN="$(_build_san)"
echo "Выпуск самоподписанного сертификата (${SSL_DAYS} дн., CN=${SSL_CN}, SAN=${SAN})"

openssl req -x509 -nodes -newkey rsa:2048 \
  -days "$SSL_DAYS" \
  -keyout "$PRIVKEY" \
  -out "$FULLCHAIN" \
  -subj "/CN=${SSL_CN}" \
  -addext "subjectAltName=${SAN}"

chmod 600 "$PRIVKEY"
chmod 644 "$FULLCHAIN"

echo ""
echo "Готово:"
openssl x509 -in "$FULLCHAIN" -noout -subject -dates -ext subjectAltName
echo ""
echo "Дальше:"
echo "  docker compose -f docker-compose.yml -f docker-compose.selfsigned.yml up -d --force-recreate nginx web"
echo "  Откройте https://${SSL_IP:-$SSL_DNS}/ (примите предупреждение браузера)"
