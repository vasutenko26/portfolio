#!/usr/bin/env bash
# Автобэкап стека portfolio → Telegram-бот «Фриланс сервер».
# Состав: дампы БД (assistant/n8n/WP) + медиа WP + конфиги + ПОЛНЫЙ бандл.
# Отправка: per-element (мелкие) + полный (дробится на части ≤49 МБ).
# Retention: на диске остаётся только самый свежий набор (backups/latest).
# Работает из контейнера backup (docker.sock) или с хоста (sg docker -c ...).
set -euo pipefail

cd /opt/portfolio
set -a; . ./.env; set +a

P="${COMPOSE_PROJECT:-portfolio}"        # префикс имён контейнеров

SB="${SERVER_BOT_TOKEN}"; CHAT="${SERVER_CHAT_ID}"
API="https://api.telegram.org/bot${SB}"
TS="$(date +%Y%m%d-%H%M)"
HOST="$(hostname)"
ROOT=/opt/portfolio/backups
WORK="${ROOT}/build-${TS}"
LATEST="${ROOT}/latest"
LIMIT=49000000          # порог дробления под лимит Telegram (50 МБ)
mkdir -p "${WORK}"

tg_msg(){ curl -sS -X POST "${API}/sendMessage" -d chat_id="${CHAT}" \
          --data-urlencode "text=$1" >/dev/null 2>&1 || true; }

on_err(){ local rc=$?; tg_msg "🔴 Бэкап ${TS} на ${HOST}: ОШИБКА (код ${rc}). Локальные файлы не тронуты."; \
          rm -rf "${WORK}"; exit "${rc}"; }
trap on_err ERR

# ---- отправка файла (с дроблением) ----
send_doc(){
  local f="$1" cap="$2" sz resp
  sz=$(stat -c%s "$f")
  if [ "$sz" -le "$LIMIT" ]; then
    resp=$(curl -sS -F chat_id="${CHAT}" -F document=@"${f}" -F caption="${cap}" "${API}/sendDocument")
    echo "$resp" | grep -q '"ok":true' || { echo "send failed: $resp" >&2; return 1; }
  else
    local pre="${f}.part." parts i=1 n
    split -b 49m -d -a 3 "$f" "$pre"
    parts=( "${pre}"* ); n=${#parts[@]}
    for p in "${parts[@]}"; do
      resp=$(curl -sS -F chat_id="${CHAT}" -F document=@"${p}" \
             -F caption="${cap} (part ${i}/${n})" "${API}/sendDocument")
      echo "$resp" | grep -q '"ok":true' || { echo "send part failed: $resp" >&2; return 1; }
      i=$((i+1))
    done
    rm -f "${pre}"*
  fi
}

# ---- 1. дампы БД (консистентно) ----
docker exec "${P}-assistant-bot-1" python -c "import sqlite3; s=sqlite3.connect('/data/assistant.db'); d=sqlite3.connect('/tmp/a.db'); s.backup(d); d.close()"
docker cp "${P}-assistant-bot-1:/tmp/a.db" "${WORK}/assistant-db.sqlite"
gzip -f "${WORK}/assistant-db.sqlite"
docker exec "${P}-assistant-bot-1" rm -f /tmp/a.db || true

docker exec "${P}-n8n-postgres-1" pg_dump -U n8n n8n | gzip > "${WORK}/n8n-postgres.sql.gz"

docker exec -e MYSQL_PWD="${MYSQL_ROOT_PASSWORD}" "${P}-mariadb-1" \
  mariadb-dump -uroot --single-transaction --routines "${MYSQL_DATABASE}" | gzip > "${WORK}/wp-mariadb.sql.gz"

# ---- 2. медиа и данные томов ----
docker run --rm -v portfolio_wp_data:/d:ro -v "${WORK}":/out alpine \
  tar czf /out/wp-content.tar.gz -C /d wp-content
docker run --rm -v portfolio_n8n_data:/d:ro -v "${WORK}":/out alpine \
  tar czf /out/n8n-data.tar.gz -C /d . 2>/dev/null || true
docker run --rm -v portfolio_grafana_data:/d:ro -v "${WORK}":/out alpine \
  tar czf /out/grafana-data.tar.gz -C /d . 2>/dev/null || true

# ---- 3. конфиги (включая .env — нужен для восстановления) ----
tar czf "${WORK}/configs.tar.gz" -C /opt/portfolio \
  docker-compose.yml Caddyfile .env \
  caddy/n8n.caddy monitoring workflows backup assistant/Dockerfile \
  assistant/requirements.txt assistant/assistant.py 2>/dev/null || true

# ---- 4. ПОЛНЫЙ бандл (все элементы в одном архиве) ----
( cd "${WORK}" && tar cf "full-${TS}.tar" \
    assistant-db.sqlite.gz n8n-postgres.sql.gz wp-mariadb.sql.gz \
    wp-content.tar.gz n8n-data.tar.gz grafana-data.tar.gz configs.tar.gz )

# ---- 5. отправка ----
send_doc "${WORK}/assistant-db.sqlite.gz" "🤖 assistant.db · ${TS}"
send_doc "${WORK}/n8n-postgres.sql.gz"    "🧩 n8n Postgres · ${TS}"
send_doc "${WORK}/wp-mariadb.sql.gz"      "🌐 WP MariaDB · ${TS}"
send_doc "${WORK}/configs.tar.gz"         "⚙️ Конфиги стека · ${TS}"
send_doc "${WORK}/full-${TS}.tar"         "📦 ПОЛНЫЙ бэкап сервера · ${TS}"

# ---- 6. retention: оставляем на диске только свежий набор ----
rm -rf "${LATEST}"; mkdir -p "${LATEST}"
mv "${WORK}"/* "${LATEST}"/
rm -rf "${WORK}"
# на всякий случай чистим прежние build-* и осиротевшие .part
rm -rf "${ROOT}"/build-* 2>/dev/null || true

FULL_SZ=$(du -h "${LATEST}/full-${TS}.tar" | cut -f1)
TOTAL=$(du -sh "${LATEST}" | cut -f1)
tg_msg "🟢 Бэкап ${TS} (${HOST}): отправлено — assistant.db, n8n, WP, конфиги + полный (${FULL_SZ}). На диске только свежий набор: ${TOTAL}."
