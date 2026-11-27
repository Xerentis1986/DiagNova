#!/usr/bin/env bash
# DiagNova lean deploy on Plesk/World4You V-Server
# Run as root or a user in the docker group. Does NOT touch helix-ki.
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/diagnova}"
REPO_URL="${REPO_URL:-https://github.com/Xerentis1986/DiagNova.git}"
BRANCH="${BRANCH:-cursor/diagnova-deploy-ff93}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

echo "==> DiagNova deploy → ${APP_DIR} (branch ${BRANCH})"

if docker ps --format '{{.Names}}' | grep -E '^helix-(ki|ollama)$' >/dev/null 2>&1; then
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
  echo "FEHLER: ${APP_DIR}/.env fehlt. Lege sie mit starken Secrets an (nicht committen)."
  exit 1
fi

# Safety: never expose compose ports beyond 127.0.0.1 for web
docker compose -f "${COMPOSE_FILE}" --env-file .env up -d --build

echo "==> Status"
docker compose -f "${COMPOSE_FILE}" ps
echo "==> Health (via web proxy path)"
curl -fsS http://127.0.0.1:3080/health || true
echo
echo "Fertig. Plesk Reverse-Proxy → 127.0.0.1:3080 setzen (siehe infrastructure/nginx/plesk-proxy.conf)."
