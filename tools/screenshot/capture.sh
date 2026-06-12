#!/usr/bin/env bash
# Полный цикл: скриншот URL -> загрузка в медиатеку WP -> прикрепление к кейсу.
#
#   bash capture.sh <url> <case-slug> [selector] [title]
#
# Доп. аргументы Playwright (логин в панель и пр.) можно дописать через EXTRA="..."
#   EXTRA='--login-url https://n8n/signin --login-user me --login-pass x' bash capture.sh ...
set -euo pipefail
cd "$(dirname "$0")/../.."   # -> /opt/portfolio

URL="${1:?url}"; SLUG="${2:?case-slug}"; SELECTOR="${3:-}"; TITLE="${4:-Демо: $SLUG}"
EXTRA="${EXTRA:-}"

TS="$(date +%Y%m%d-%H%M%S)"
FILE="shot-${SLUG}-${TS}.png"
OUTREL="tools/screenshot/out/${FILE}"

echo "1/3 Снимаю $URL ..."
SEL_ARG=""; [ -n "$SELECTOR" ] && SEL_ARG="--selector $SELECTOR"
node tools/screenshot/shot.js --url "$URL" --out "$OUTREL" $SEL_ARG $EXTRA

echo "2/3 Ищу кейс '$SLUG' ..."
CASE_ID="$(sudo docker compose run --rm --no-deps -T --entrypoint sh wpcli -c \
  "wp --allow-root post list --post_type=case --name=$SLUG --field=ID" 2>/dev/null | tr -d '\r' | grep -E '^[0-9]+$' | head -1)"
[ -n "$CASE_ID" ] || { echo "Кейс со slug '$SLUG' не найден"; exit 1; }

echo "3/3 Загружаю в медиатеку и прикрепляю к кейсу #$CASE_ID ..."
sudo docker compose run --rm --no-deps -T \
  -v "$(pwd)/tools/screenshot/out:/shots" \
  wpcli media import "/shots/${FILE}" --post_id="$CASE_ID" --title="$TITLE" --alt="$TITLE" 2>&1 \
  | grep -iE 'Imported|Error' || true

echo "Готово: $FILE -> кейс '$SLUG' (post_id=$CASE_ID)"
