#!/usr/bin/env bash
# Тест-restore: поднимает ОДНОРАЗОВЫЕ контейнеры, восстанавливает в них последний бэкап
# и проверяет данные. Прод не трогает. Контейнеры сносятся в конце. Запуск от root.
set -euo pipefail

DEST=/opt/backups
B=$(ls -1dt "$DEST"/*/ 2>/dev/null | head -1)
[ -n "$B" ] || { echo "Нет бэкапов в $DEST"; exit 1; }
echo "== ТЕСТ-RESTORE из: $B =="

MARIA="restore-maria-$$"; PG="restore-pg-$$"
cleanup(){ docker rm -f "$MARIA" "$PG" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# ---------- MariaDB ----------
echo "-- MariaDB: поднимаю одноразовый контейнер"
docker run -d --name "$MARIA" -e MARIADB_ROOT_PASSWORD=restore-only mariadb:11 >/dev/null
until docker exec -e MYSQL_PWD=restore-only "$MARIA" mariadb -uroot -e 'SELECT 1' >/dev/null 2>&1; do sleep 2; done
echo "-- MariaDB: восстанавливаю дамп"
zcat "$B/mariadb.sql.gz" | docker exec -i -e MYSQL_PWD=restore-only "$MARIA" mariadb -uroot
POSTS=$(docker exec -e MYSQL_PWD=restore-only "$MARIA" mariadb -uroot -N -e "SELECT COUNT(*) FROM wordpress.wp_posts")
CASES=$(docker exec -e MYSQL_PWD=restore-only "$MARIA" mariadb -uroot -N -e "SELECT COUNT(*) FROM wordpress.wp_posts WHERE post_type='case' AND post_status='publish'")
SITEURL=$(docker exec -e MYSQL_PWD=restore-only "$MARIA" mariadb -uroot -N -e "SELECT option_value FROM wordpress.wp_options WHERE option_name='siteurl'")

# ---------- Postgres (n8n) ----------
echo "-- Postgres: поднимаю одноразовый контейнер"
docker run -d --name "$PG" -e POSTGRES_PASSWORD=restore-only -e POSTGRES_USER=n8n -e POSTGRES_DB=n8n postgres:16-alpine >/dev/null
until docker exec "$PG" pg_isready -U n8n >/dev/null 2>&1; do sleep 2; done
echo "-- Postgres: восстанавливаю дамп"
zcat "$B/n8n-postgres.sql.gz" | docker exec -i "$PG" psql -q -U n8n -d n8n >/dev/null 2>&1
WF=$(docker exec "$PG" psql -U n8n -d n8n -tAc "SELECT COUNT(*) FROM workflow_entity" 2>/dev/null | tr -d '[:space:]')

echo
echo "===== RESULT ====="
echo "MariaDB  : wp_posts=$POSTS, опубликованных кейсов=$CASES, siteurl=$SITEURL"
echo "Postgres : workflow_entity=$WF"
if [ "${POSTS:-0}" -gt 0 ] && [ "${WF:-0}" -gt 0 ] && [ "$SITEURL" = "https://davidvasutenko.fun" ]; then
  echo "VERDICT  : ✅ RESTORE VERIFIED — данные восстановлены и согласованы"
else
  echo "VERDICT  : ❌ проверка не прошла"; exit 1
fi
echo "Sandbox-контейнеры сносятся."
