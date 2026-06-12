# davidvasutenko.fun — портфолио инженера инфраструктуры

Кастомный сайт-портфолио на WordPress в Docker, за обратным прокси Caddy с
автоматическим HTTPS. Тема — своя (классическая, без билдеров), анимации на
GSAP + Lenis, сборка ассетов через Vite.

## Стек

| Слой        | Технология |
|-------------|------------|
| Прокси/TLS  | Caddy 2 (Let's Encrypt, авто-renew) |
| CMS         | WordPress (php8.3) + WP-CLI |
| БД          | MariaDB 11 |
| Тема        | `src/theme/davidv` — Vite, GSAP, ScrollTrigger, Lenis, self-hosted шрифты |
| Данные      | `src/mu-plugins/portfolio-core.php` — CPT «Кейс», поля (ACF), хардненинг |
| Скриншоты   | `tools/screenshot` — Playwright → медиатека WP |

## Структура

```
docker-compose.yml      # caddy + wordpress + mariadb + wpcli
Caddyfile               # обратный прокси, TLS, заголовки безопасности
.env                    # секреты (НЕ в git)
src/theme/davidv/       # кастомная тема
src/mu-plugins/         # must-use плагин (CPT, поля, безопасность)
tools/screenshot/       # Playwright-пайплайн скриншотов
scripts/seed-content.sh # сидинг кейсов-плейсхолдеров
```

## Развернуть с нуля

```bash
cp .env.example .env          # заполнить секреты
docker compose up -d          # поднять стек (Caddy сам выпишет SSL)
# установка WP и базовая настройка — через wpcli (см. историю команд)
cd src/theme/davidv && npm ci && npm run build   # собрать ассеты темы
bash scripts/seed-content.sh  # создать кейсы-плейсхолдеры
```

## Сборка темы

```bash
cd src/theme/davidv
npm run build      # прод-сборка в assets/build (хешированные файлы + manifest)
npm run dev        # пересборка по изменениям
```
`functions.php` читает `assets/build/.vite/manifest.json` и подключает
хешированный бандл. Без сборки сайт работает на фолбэк-стилях.

## Авто-скриншоты демок

```bash
# простой случай: снять URL и прикрепить к кейсу по slug
bash tools/screenshot/capture.sh https://example.com devops

# по селектору + заголовок
bash tools/screenshot/capture.sh https://panel.example.com devops "#dashboard" "Grafana — нагрузка"

# панель с логином (n8n / Grafana / FreePBX)
EXTRA='--login-url https://n8n/signin --login-user me --login-pass *** \
  --user-sel "input[name=email]" --pass-sel "input[name=password]"' \
  bash tools/screenshot/capture.sh https://n8n/home automation "" "n8n — воркфлоу"
```
Скриншот сохраняется в `tools/screenshot/out/`, грузится в медиатеку и
прикрепляется к нужному кейсу; в галерее кейса появляется автоматически.

## Безопасность

- Вход в админку скрыт (`/***REDACTED***/`), `/wp-login.php` → 404
- XML-RPC выключен, перечисление пользователей заблокировано
- Лимит попыток входа, `DISALLOW_FILE_EDIT`, авто-обновления ядра
- Заголовки HSTS / nosniff / frame-options на уровне Caddy
- Хост: ufw (только 22/80/443), fail2ban, вход по SSH-ключу
