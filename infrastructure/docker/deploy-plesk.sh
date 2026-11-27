#!/usr/bin/env bash
# DiagNova Deploy auf World4You V-Server (Plesk + Docker).
# Ausführen als root oder Docker-Gruppenmitglied.
# Ändert KEINE anderen Stacks (helix-ki / helix-ollama) und keine anderen Domains.
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/diagnova}"
REPO_URL="${REPO_URL:-https://github.com/Xerentis1986/DiagNova.git}"
BRANCH="${BRANCH:-cursor/diagnova-phase-16-deploy-8876}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/diagnova}"

echo "==> DiagNova deploy → ${APP_DIR} (branch ${BRANCH})"

if docker ps --format '{{.Names}}' 2>/dev/null | grep -E 'helix' >/dev/null 2>&1; then
  echo "Hinweis: helix-Container laufen – werden nicht verändert."
fi

mkdir -p "${APP_DIR}"
if [[ ! -d "${APP_DIR}/.git" ]]; then
  git clone --branch "${BRANCH}" --single-branch "${REPO_URL}" "${APP_DIR}"
else
  git -C "${APP_DIR}" fetch origin "${BRANCH}"
  git -C "${APP_DIR}" checkout "${BRANCH}"
  git -C "${APP_DIR}" pull --ff-only origin "${BRANCH}"
fi

cd "${APP_DIR}"

if [[ ! -f .env ]]; then
  echo "FEHLER: ${APP_DIR}/.env fehlt."
  echo "Kopiere .env.example → .env, setze starke Secrets, chmod 600 .env"
  exit 1
fi

if [[ "$(stat -c '%a' .env 2>/dev/null || echo '?')" != "600" ]]; then
  echo "WARNUNG: .env sollte chmod 600 haben (aktuell: $(stat -c '%a' .env 2>/dev/null || echo unbekannt))"
fi

# Optional: DB-Backup vor Rebuild (wenn Stack schon läuft)
if docker compose -f "${COMPOSE_FILE}" --env-file .env ps --status running 2>/dev/null | grep -q postgres; then
  mkdir -p "${BACKUP_DIR}"
  STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
  echo "==> Backup vor Deploy → ${BACKUP_DIR}/pre-deploy-${STAMP}.dump"
  # shellcheck disable=SC1091
  set -a; source .env; set +a
  docker compose -f "${COMPOSE_FILE}" --env-file .env exec -T postgres \
    pg_dump -U "${POSTGRES_USER:-diagnova}" -d "${POSTGRES_DB:-diagnova}" -Fc \
    > "${BACKUP_DIR}/pre-deploy-${STAMP}.dump" || echo "WARNUNG: pg_dump fehlgeschlagen – Deploy fortgesetzt"
fi

docker compose -f "${COMPOSE_FILE}" --env-file .env up -d --build

echo "==> Status"
docker compose -f "${COMPOSE_FILE}" --env-file .env ps
echo "==> Health (lokal)"
curl -fsS http://127.0.0.1:3080/health || true
echo
echo "Fertig. Proxy: Plesk Docker Rule → diagnova-web-1:80 oder infrastructure/nginx/plesk-proxy.conf"
echo "Rollback: siehe docs/world4you-plesk-install.md"
