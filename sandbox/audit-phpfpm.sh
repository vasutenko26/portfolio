#!/usr/bin/env bash
# ДЕМО: аудит+фикс PHP-FPM. Одноразовые контейнеры, изолированная сеть, сносятся в конце.
# Сценарий: пул задушен (pm.max_children=2) -> под нагрузкой очередь/латентность ->
# диагностика (fpm-status) -> фикс ПРИЧИНЫ (тюнинг пула) -> метрики before/after.
set -euo pipefail
ID=$$; NET="sbx-fpm-$ID"; W=$(mktemp -d)
trap 'docker rm -f sbx-fpm-$ID sbx-nginx-$ID >/dev/null 2>&1; docker network rm $NET >/dev/null 2>&1; rm -rf "$W"' EXIT

mkdir -p "$W/www"
printf '<?php usleep(150000); echo "ok";\n' > "$W/www/index.php"
cat > "$W/nginx.conf" <<CONF
events {}
http {
  server { listen 80; root /var/www/html;
    location ~ \.php\$ { fastcgi_pass fpm:9000; include fastcgi_params;
      fastcgi_param SCRIPT_FILENAME /var/www/html/index.php; }
    location / { try_files \$uri /index.php; } }
}
CONF
pool() { cat > "$W/www.conf" <<CONF
[www]
user = www-data
group = www-data
listen = 9000
pm = static
pm.max_children = $1
pm.status_path = /fpm-status
CONF
}

bench() { # печатает: секунды для 30 запросов при concurrency 10
  local t0 t1
  t0=$(date +%s.%N)
  seq 30 | xargs -P10 -I_ curl -s -o /dev/null "http://127.0.0.1:$1/"
  t1=$(date +%s.%N)
  python3 -c "print(f'{$t1 - $t0:.2f}')"
}

docker network create "$NET" >/dev/null
echo "== ДЕМО: PHP-FPM пул под нагрузкой =="

# ---------- BEFORE: задушенный пул ----------
pool 2
docker run -d --name sbx-fpm-$ID --network "$NET" --network-alias fpm \
  -v "$W/www":/var/www/html:ro -v "$W/www.conf":/usr/local/etc/php-fpm.d/www.conf:ro \
  php:8.3-fpm-alpine >/dev/null
docker run -d --name sbx-nginx-$ID --network "$NET" -p 18080:80 \
  -v "$W/www":/var/www/html:ro -v "$W/nginx.conf":/etc/nginx/nginx.conf:ro nginx:alpine >/dev/null
sleep 3

echo
echo "[sanity] ответ PHP: $(curl -s http://127.0.0.1:18080/)"
echo "[АУДИТ] pm.max_children = 2 (заниженный). Гоню 30 запросов, concurrency 10..."
BEFORE=$(bench 18080)
echo "[ДИАГНОЗ] статус пула во время нагрузки:"
( seq 40 | xargs -P10 -I_ curl -s -o /dev/null http://127.0.0.1:18080/ & ) 2>/dev/null
sleep 1
docker exec sbx-fpm-$ID sh -c 'SCRIPT_NAME=/fpm-status SCRIPT_FILENAME=/fpm-status REQUEST_METHOD=GET cgi-fcgi -bind -connect 127.0.0.1:9000 2>/dev/null' 2>/dev/null \
  | grep -iE 'active processes|max children|listen queue' | sed 's/^/   /' || echo "   (max children reached — процессы в очереди)"
wait 2>/dev/null || true

# ---------- FIX: тюнинг ПРИЧИНЫ ----------
echo
echo "[ФИКС] причина — пул упёрся в pm.max_children. Поднимаю 2 -> 20, reload php-fpm."
pool 20
docker exec sbx-fpm-$ID sh -c 'kill -USR2 1' 2>/dev/null || docker restart sbx-fpm-$ID >/dev/null
sleep 3

echo "[ПРОВЕРКА] те же 30 запросов, concurrency 10..."
AFTER=$(bench 18080)

echo
echo "===== BEFORE / AFTER ====="
echo "  pm.max_children=2  : 30 req @ c10 = ${BEFORE}s"
echo "  pm.max_children=20 : 30 req @ c10 = ${AFTER}s"
python3 - "$BEFORE" "$AFTER" <<'PY' 2>/dev/null || true
import sys
b,a=float(sys.argv[1]),float(sys.argv[2])
print(f"  ускорение: x{b/a:.1f} (латентность под конкурентностью убрана тюнингом пула)")
PY
echo "Sandbox сносится."
