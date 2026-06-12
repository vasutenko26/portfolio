#!/usr/bin/env bash
# Бэкап прод-стека: MariaDB (WordPress) + n8n Postgres + том WP uploads + конфиги.
# Только ЧИТАЕТ прод (dump/exec/ro-mount). Локально, с ротацией. Запуск от root.
set -euo pipefail

REPO=/opt/portfolio
DEST=/opt/backups
KEEP=7
TS=$(date +%Y%m%d-%H%M%S)
OUT="$DEST/$TS"
mkdir -p "$OUT"

cd "$REPO"
set -a; . ./.env; set +a

log() { echo "[$(date +%H:%M:%S)] $*"; }

log "MariaDB (wordpress) -> mariadb.sql.gz"
docker compose exec -T -e MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mariadb \
  mariadb-dump -uroot --single-transaction --routines --databases "$MYSQL_DATABASE" | gzip > "$OUT/mariadb.sql.gz"

log "n8n Postgres -> n8n-postgres.sql.gz"
docker compose exec -T n8n-postgres pg_dump -U n8n -d n8n | gzip > "$OUT/n8n-postgres.sql.gz"

log "WP uploads (том, read-only) -> wp-uploads.tar.gz"
docker run --rm -v portfolio_wp_data:/data:ro alpine \
  tar czf - -C /data wp-content/uploads 2>/dev/null > "$OUT/wp-uploads.tar.gz" || true

log "Конфиги -> configs.tar.gz"
tar czf "$OUT/configs.tar.gz" -C "$REPO" \
  .env docker-compose.yml Caddyfile caddy/n8n.caddy monitoring deploy scripts 2>/dev/null || true

# манифест с размерами и контрольными суммами
( cd "$OUT" && sha256sum ./* > SHA256SUMS && du -h ./* ) > "$OUT/MANIFEST.txt"
chmod -R 600 "$OUT"/* ; chmod 700 "$OUT"

log "Ротация: оставляю последние $KEEP"
ls -1dt "$DEST"/*/ 2>/dev/null | tail -n +$((KEEP+1)) | xargs -r rm -rf

log "Готово: $OUT ($(du -sh "$OUT" | cut -f1))"
