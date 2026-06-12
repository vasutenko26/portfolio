#!/usr/bin/env bash
# Настраивает Grafana-алертинг → Telegram (читает секреты из .env, в git не хардкодит).
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a

GRAF="https://grafana.davidvasutenko.fun"
R=(--resolve grafana.davidvasutenko.fun:443:127.0.0.1)
AUTH=(-u "admin:${GRAFANA_ADMIN_PASSWORD}")
H=(-H 'Content-Type: application/json' -H 'X-Disable-Provenance: true')

echo "1) Папка для алертов"
FUID=$(curl -s "${R[@]}" "${AUTH[@]}" "${H[@]}" -X POST "$GRAF/api/folders" \
  -d '{"title":"Portfolio Alerts"}' | python3 -c "import sys,json;print(json.load(sys.stdin).get('uid',''))" 2>/dev/null || true)
[ -z "$FUID" ] && FUID=$(curl -s "${R[@]}" "${AUTH[@]}" "$GRAF/api/folders" | python3 -c "import sys,json;[print(f['uid']) for f in json.load(sys.stdin) if f['title']=='Portfolio Alerts']")
echo "   folderUID=$FUID"

echo "2) Telegram contact point"
curl -s "${R[@]}" "${AUTH[@]}" "${H[@]}" -X POST "$GRAF/api/v1/provisioning/contact-points" \
  -d "{\"name\":\"telegram\",\"type\":\"telegram\",\"settings\":{\"bottoken\":\"${TELEGRAM_BOT_TOKEN}\",\"chatid\":\"${TELEGRAM_CHAT_ID}\"},\"disableResolveMessage\":false}" \
  -o /dev/null -w "   http %{http_code}\n"

echo "3) Notification policy (root → telegram)"
curl -s "${R[@]}" "${AUTH[@]}" "${H[@]}" -X PUT "$GRAF/api/v1/provisioning/policies" \
  -d '{"receiver":"telegram","group_by":["grafana_folder","alertname"],"group_wait":"10s","group_interval":"1m","repeat_interval":"4h"}' \
  -o /dev/null -w "   http %{http_code}\n"

echo "4) Alert rule: App down (up{job=app} < 1)"
RULE=$(cat <<JSON
{
  "title": "App down (job=app)",
  "ruleGroup": "portfolio",
  "folderUID": "$FUID",
  "condition": "C",
  "for": "30s",
  "noDataState": "Alerting",
  "execErrState": "Alerting",
  "orgID": 1,
  "data": [
    {"refId":"A","relativeTimeRange":{"from":600,"to":0},"datasourceUid":"prometheus","model":{"editorMode":"code","expr":"up{job=\"app\"}","instant":true,"intervalMs":1000,"maxDataPoints":43200,"refId":"A"}},
    {"refId":"C","datasourceUid":"__expr__","model":{"conditions":[{"evaluator":{"params":[1],"type":"lt"},"operator":{"type":"and"},"query":{"params":["A"]},"reducer":{"type":"last"},"type":"query"}],"datasource":{"type":"__expr__","uid":"__expr__"},"expression":"A","refId":"C","type":"threshold"}}
  ]
}
JSON
)
curl -s "${R[@]}" "${AUTH[@]}" "${H[@]}" -X POST "$GRAF/api/v1/provisioning/alert-rules" \
  -d "$RULE" -w "\n   http %{http_code}\n" | tail -2

echo "Готово."
