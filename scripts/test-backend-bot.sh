#!/usr/bin/env bash
set -euo pipefail

COMPOSE_CMD="${COMPOSE_CMD:-docker compose}"
BACKEND_HEALTH_URL="${BACKEND_HEALTH_URL:-http://localhost:8000/health}"
BOT_HEALTH_URL="${BOT_HEALTH_URL:-http://localhost:8080/healthz}"
FRONTEND_HEALTH_URL="${FRONTEND_HEALTH_URL:-http://localhost:4173}"
SERVICES_ENV="${SERVICES:-backend bot frontend}"
read -r -a SERVICES <<<"$SERVICES_ENV"

info() {
  printf '==> %s\n' "$*"
}

warn() {
  printf '[warn] %s\n' "$*" >&2
}

wait_for() {
  local url=$1
  local name=$2
  info "Waiting for ${name} at ${url}"
  until curl -fsS "$url" >/dev/null 2>&1; do
    sleep 1
  done
}

if [[ "${WITH_REBUILD:-0}" == "1" ]]; then
  info "Rebuilding images for services (${SERVICES_ENV})"
  $COMPOSE_CMD build "${SERVICES[@]}"
else
  warn "Skipping image rebuild (WITH_REBUILD=0)"
fi

info "Starting services (${SERVICES_ENV})"
$COMPOSE_CMD up -d "${SERVICES[@]}"

need_service() {
  local name=$1
  for svc in "${SERVICES[@]}"; do
    if [[ "$svc" == "$name" ]]; then
      return 0
    fi
  done
  return 1
}

if need_service "backend"; then
  wait_for "$BACKEND_HEALTH_URL" "backend"
fi

if need_service "bot"; then
  wait_for "$BOT_HEALTH_URL" "bot"
fi

if need_service "frontend"; then
  wait_for "$FRONTEND_HEALTH_URL" "frontend"
fi

if need_service "backend" && [[ "${SKIP_SEED:-0}" != "1" ]]; then
  info "Seeding database inside backend container (init_db.sh)"
  $COMPOSE_CMD exec backend bash -lc "bash ./init_db.sh"
elif need_service "backend"; then
  info "Skipping database seed because SKIP_SEED=${SKIP_SEED}"
fi

if need_service "backend"; then
  info "Backend health response:"
  curl -fsS "$BACKEND_HEALTH_URL"
  printf '\n'
fi

if need_service "bot"; then
  info "Bot health response:"
  curl -fsS "$BOT_HEALTH_URL"
  printf '\n'
fi

if need_service "frontend"; then
  info "Frontend root response (first 200 bytes):"
  curl -fsS "$FRONTEND_HEALTH_URL" | head -c 200
  printf '\n'
fi

info "Container status:"
$COMPOSE_CMD ps "${SERVICES[@]}"
