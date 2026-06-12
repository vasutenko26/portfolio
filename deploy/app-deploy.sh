#!/usr/bin/env bash
# Forced-command для Actions→сервер: ТОЛЬКО передеплой app.
# Подтягивает свежий образ из GHCR и пересоздаёт контейнер. Ничего больше.
set -euo pipefail
cd /opt/app
docker compose pull app
docker compose up -d app
docker image prune -f >/dev/null 2>&1 || true
echo "deployed image: $(docker compose images app --format '{{.Repository}}:{{.Tag}}@{{.ID}}' 2>/dev/null || echo app)"
