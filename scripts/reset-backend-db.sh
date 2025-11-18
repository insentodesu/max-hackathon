#!/usr/bin/env bash
set -euo pipefail

COMPOSE_CMD="${COMPOSE_CMD:-docker-compose}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-edumax}"
VOLUME_NAME="${DB_VOLUME_NAME:-${PROJECT_NAME}_backend_data}"

info() {
  printf '==> %s\n' "$*"
}

warn() {
  printf '[warn] %s\n' "$*" >&2
}

info "Stopping backend/bot/nginx containers"
$COMPOSE_CMD down backend bot nginx

info "Removing database volume: ${VOLUME_NAME}"
if ! docker volume rm -f "${VOLUME_NAME}" >/dev/null 2>&1; then
  warn "volume ${VOLUME_NAME} was not removed (already absent?)"
fi

if [[ "${SKIP_RESTART:-0}" == "1" ]]; then
  warn "Skipping service restart because SKIP_RESTART=${SKIP_RESTART}"
  exit 0
fi

info "Starting backend/bot/nginx containers with a clean database"
$COMPOSE_CMD up -d backend bot nginx
