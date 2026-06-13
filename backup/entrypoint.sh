#!/usr/bin/env bash
# Планировщик бэкапов: crond по локальному времени (TZ), 06/14/22.
set -euo pipefail

CRONTAB="${BACKUP_CRON:-0 6,14,22 * * *}"
echo "${CRONTAB} /opt/portfolio/backup/backup.sh >> /opt/portfolio/backups/cron.log 2>&1" > /etc/crontabs/root
mkdir -p /opt/portfolio/backups

echo "[backup] scheduler up; TZ=${TZ:-UTC}; cron='${CRONTAB}'"
# -f foreground, -l 8 уровень логов
exec crond -f -l 8
