#!/usr/bin/env bash
# Создаёт 5 кейсов-плейсхолдеров (идемпотентно). Запуск: bash scripts/seed-content.sh
set -euo pipefail
cd "$(dirname "$0")/.."

sudo docker compose run --rm --no-deps -T --entrypoint sh wpcli -c '
set -e
WP="wp --allow-root"

if [ -n "$($WP post list --post_type=case --format=ids)" ]; then
  echo "Кейсы уже есть — пропускаю seed."
  exit 0
fi

setf() { $WP post meta update "$1" "$2" "$3" >/dev/null; $WP post meta update "$1" "_$2" "$4" >/dev/null; }

TASK="<p>Здесь будет описание исходной задачи: контекст клиента, ограничения и цель. Плейсхолдер — заполняется по мере готовности демо.</p>"
APPR="<p>Что было сделано: архитектура решения, инструменты и ключевые шаги внедрения. Плейсхолдер.</p>"
RES="<p>Достигнутый результат и измеримый эффект. Плейсхолдер до публикации демо.</p>"

mkcase() {
  TITLE="$1"; SLUG="$2"; ORD="$3"; ROLE="$4"; SUM="$5"; STACK="$6"; METRIC="$7"
  ID=$($WP post create --post_type=case --post_status=publish --post_title="$TITLE" --post_name="$SLUG" --menu_order=$ORD --porcelain)
  setf $ID role_label "$ROLE" f_role
  setf $ID summary "$SUM" f_sum
  setf $ID stack "$STACK" f_stack
  setf $ID result_metric "$METRIC" f_metric
  setf $ID task "$TASK" f_task
  setf $ID approach "$APPR" f_appr
  setf $ID result "$RES" f_res
  echo "  + [$ID] $TITLE"
}

echo "Создаю кейсы..."
mkcase "Корпоративная телефония на Asterisk/FreePBX" "telephony" 1 "Телефония" \
  "АТС, маршрутизация звонков, голосовое меню и запись разговоров под ключ." \
  "Asterisk, FreePBX, SIP, PJSIP" "<1с set-up звонка"
mkcase "Администрирование Linux-серверов 24/7" "linux" 2 "Linux" \
  "Поддержка, обновления, бэкапы и мониторинг боевых серверов без простоев." \
  "Debian, Ubuntu, systemd, Bash" "99.98% uptime"
mkcase "DevOps-конвейер: Docker и CI/CD" "devops" 3 "DevOps" \
  "Контейнеризация, автодеплой и наблюдаемость: от пуша до прод за минуты." \
  "Docker, GitLab CI, Grafana, Prometheus" "деплой за 2 мин"
mkcase "Автоматизация процессов на n8n" "automation" 4 "Автоматизация" \
  "Связал сервисы в один поток: вебхуки, интеграции и уведомления без рутины." \
  "n8n, REST, Webhooks, API" "−15ч рутины/нед"
mkcase "Этот сайт: Caddy + Docker + WordPress" "web" 5 "Web" \
  "Кастомная тема, авто-SSL, кеш и Lighthouse 90+ — собран в Docker и в git." \
  "Caddy, Docker, WordPress, Vite" "Lighthouse 90+"

echo "Готово."
$WP post list --post_type=case --fields=ID,post_title,post_name,menu_order
'
