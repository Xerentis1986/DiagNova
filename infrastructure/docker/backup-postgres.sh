#!/usr/bin/env bash
# Postgres-Dump aus dem Prod-Compose-Stack (ohne Secrets auszugeben).
# Voraussetzung: Stack läuft unter APP_DIR mit docker-compose.prod.yml + .env
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/diagnova}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/diagnova}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

cd "${APP_DIR}"
if [[ ! -f .env ]]; then
  echo "FEHLER: ${APP_DIR}/.env fehlt"
  exit 1
fi

mkdir -p "${BACKUP_DIR}"
OUT="${BACKUP_DIR}/diagnova-${STAMP}.dump"

# shellcheck disable=SC1091
set -a; source .env; set +a

docker compose -f "${COMPOSE_FILE}" --env-file .env exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-diagnova}" -d "${POSTGRES_DB:-diagnova}" -Fc > "${OUT}"

# Alembic-Revision mitschreiben (Metadaten, kein Secret)
REV="$(docker compose -f "${COMPOSE_FILE}" --env-file .env exec -T api \
  alembic current 2>/dev/null | tr -d '\r' | head -1 || echo unknown)"
echo "${REV}" > "${BACKUP_DIR}/diagnova-${STAMP}.alembic.txt"

chmod 600 "${OUT}"
ls -lh "${OUT}"
echo "Alembic: ${REV}"
echo "Prüfen: pg_restore --list ${OUT} | head"
