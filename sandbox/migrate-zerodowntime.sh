#!/usr/bin/env bash
# ДЕМО: zero-downtime миграция blue->green. Одноразовые контейнеры, сносятся в конце.
# Непрерывная нагрузка идёт ВО ВРЕМЯ переключения; трафик уходит на green только
# после его health-check; считаем потери (должно быть 0).
set -euo pipefail
ID=$$; NET="sbx-mig-$ID"; W=$(mktemp -d)
trap 'docker rm -f sbx-blue-$ID sbx-green-$ID sbx-proxy-$ID >/dev/null 2>&1; docker network rm $NET >/dev/null 2>&1; rm -rf "$W"' EXIT

printf 'v1 (blue)\n'  > "$W/blue.html"
printf 'v2 (green)\n' > "$W/green.html"
proxycfg() { cat > "$W/proxy.conf" <<CONF
events {}
http {
  upstream site { server $1:80 max_fails=0; }
  server { listen 80; location / { proxy_pass http://site; proxy_connect_timeout 1s; } }
}
CONF
}

docker network create "$NET" >/dev/null
echo "== ДЕМО: zero-downtime миграция blue -> green =="
docker run -d --name sbx-blue-$ID --network "$NET" --network-alias blue \
  -v "$W/blue.html":/usr/share/nginx/html/index.html:ro nginx:alpine >/dev/null
proxycfg blue
docker run -d --name sbx-proxy-$ID --network "$NET" -p 18090:80 \
  -v "$W/proxy.conf":/etc/nginx/nginx.conf:ro nginx:alpine >/dev/null
sleep 3
echo "[старт] прокси отдаёт: $(curl -s http://127.0.0.1:18090/)"

# непрерывная нагрузка в фоне (~10с)
RES="$W/res.txt"; : > "$RES"
( for _ in $(seq 1 200); do
    code=$(curl -s -o /tmp/body-$ID -m 2 -w '%{http_code}' http://127.0.0.1:18090/ 2>/dev/null || echo 000)
    echo "$code $(tr -d '\n' < /tmp/body-$ID 2>/dev/null)" >> "$RES"
    sleep 0.05
  done ) &
LOADPID=$!

sleep 2
echo "[миграция] поднимаю green (v2), health-check ДО переключения трафика"
docker run -d --name sbx-green-$ID --network "$NET" --network-alias green \
  -v "$W/green.html":/usr/share/nginx/html/index.html:ro nginx:alpine >/dev/null
until docker exec sbx-proxy-$ID wget -qO- http://green/ >/dev/null 2>&1; do sleep 0.3; done
echo "[миграция] green здоров -> переключаю upstream blue->green + graceful reload"
proxycfg green   # переписываем host-файл; bind-mount отражает его в контейнер
docker exec sbx-proxy-$ID nginx -s reload
echo "[после] прокси отдаёт: $(curl -s http://127.0.0.1:18090/)"

wait $LOADPID 2>/dev/null || true
TOTAL=$(wc -l < "$RES"); OK=$(grep -c '^200' "$RES" || true); FAIL=$(grep -vc '^200' "$RES" || true)
V1=$(grep -c 'v1' "$RES" || true); V2=$(grep -c 'v2' "$RES" || true)
echo
echo "===== РЕЗУЛЬТАТ (нагрузка во время миграции) ====="
echo "  всего запросов : $TOTAL"
echo "  успешных (200) : $OK"
echo "  ошибок/потерь  : $FAIL"
echo "  отдал blue(v1) : $V1    green(v2): $V2"
if [ "${FAIL:-1}" -eq 0 ]; then
  echo "  VERDICT: ✅ ZERO DOWNTIME — переключение blue->green без единой потерянной запроса"
else
  echo "  VERDICT: ⚠️ потерь: $FAIL"
fi
echo "Sandbox сносится."
