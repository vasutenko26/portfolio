#!/usr/bin/env bash
# Печатает отчёт по серверу в stdout (без отправки в Telegram).
# Вызывается server-bot'ом на хосте через nsenter (root) для кнопки «Отчёт по серверу».
# Логика метрик идентична /usr/local/bin/server-report.sh (которым шлёт суточный таймер).
set -uo pipefail

HOST=$(hostname)
NOW=$(date '+%Y-%m-%d %H:%M %Z')

# --- Нагрузка ---
UP=$(uptime -p 2>/dev/null | sed 's/^up //'); [ -z "$UP" ] && UP="?"
LOAD=$(cut -d' ' -f1-3 /proc/loadavg)
CORES=$(nproc)
MEM=$(free -m | awk '/^Mem:/{printf "%d/%d МБ (%.0f%%)", $3, $2, $3/$2*100}')
MEM_PCT=$(free -m | awk '/^Mem:/{printf "%.0f", $3/$2*100}')
DISK=$(df -h / | awk 'NR==2{print $3"/"$2" ("$5")"}')
DISK_PCT=$(df / | awk 'NR==2{gsub("%","",$5); print $5}')

# --- Безопасность ---
SSH_S=$(systemctl is-active ssh 2>/dev/null)
F2B_S=$(systemctl is-active fail2ban 2>/dev/null)
if grep -q '^ENABLED=yes' /etc/ufw/ufw.conf 2>/dev/null; then UFW_S=active; else UFW_S=inactive; fi
FAILED=$(journalctl -u ssh --since "24 hours ago" 2>/dev/null | grep -cE 'Failed password|Invalid user|authentication failure')
ACCEPTED=$(journalctl -u ssh --since "24 hours ago" 2>/dev/null | grep -c 'Accepted')
BANNED=$(fail2ban-client status sshd 2>/dev/null | grep -i 'currently banned' | grep -oE '[0-9]+$'); [ -z "$BANNED" ] && BANNED="0"

# --- Обновления ---
SEC=$(apt-get -s upgrade 2>/dev/null | grep -ci '\-security'); [ -z "$SEC" ] && SEC=0
if [ -f /var/run/reboot-required ]; then RB="ДА"; else RB="нет"; fi

# --- Вердикт ---
WARN=""
[ "${DISK_PCT:-0}" -ge 90 ] && WARN="${WARN}• диск >90%
"
[ "${MEM_PCT:-0}" -ge 90 ] && WARN="${WARN}• память >90%
"
[ "$RB" = "ДА" ] && WARN="${WARN}• нужна перезагрузка
"
[ "$SSH_S" != "active" ] && WARN="${WARN}• ssh не active
"
[ "$F2B_S" != "active" ] && WARN="${WARN}• fail2ban не active
"
[ "$UFW_S" != "active" ] && WARN="${WARN}• файрвол выключен
"
if [ -z "$WARN" ]; then STATUS="✅ Всё ок"; else STATUS="⚠️ Внимание:
${WARN}"; fi

cat <<EOF
🖥 Отчёт по серверу: ${HOST}
🕒 ${NOW}

${STATUS}

📊 Нагрузка
• Аптайм: ${UP}
• Load avg (1/5/15м): ${LOAD}  (ядер: ${CORES})
• Память: ${MEM}
• Диск /: ${DISK}

🔐 Безопасность
• SSH: ${SSH_S} | fail2ban: ${F2B_S} | ufw: ${UFW_S}
• Неуд. попыток входа (24ч): ${FAILED}
• Успешных входов (24ч): ${ACCEPTED}
• Забанено сейчас (sshd): ${BANNED}

📦 Обновления
• Обновлений безопасности: ${SEC}
• Нужна перезагрузка: ${RB}
EOF
