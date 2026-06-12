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

## Языки (i18n)

Три языка через **Polylang**: English (дефолт, без префикса), Українська (`/uk/`), Русский (`/ru/`).

- **UI темы** — gettext, источник английский. Строки в `languages/davidv.pot`,
  переводы `davidv-uk.po/.mo`, `davidv-ru_RU.po/.mo`. Текстдомен грузится под
  язык Polylang на `template_redirect` (см. `functions.php`).
- **Кейсы** — каждый кейс это 3 связанных поста (EN/UK/RU), у каждого свои
  ACF-поля и вложения. Связь карточки услуги с кейсом — по мете `service_key`
  (не по slug), поэтому не зависит от языка.
- **Slug кейсов** уникальны по языку: `devops`, `devops-uk`, `devops-ru`
  (надёжная резолюция при EN без префикса). Переключатель ведёт по корректным
  пермалинкам Polylang.
- **Шрифты:** заголовки — Space Grotesk (латиница) + **Onest** (кириллица,
  per-glyph fallback, грузится только на UK/RU). Body/mono — Inter / JetBrains
  Mono с cyrillic-сабсетами.
- **SEO:** `hreflang` на все версии (Polylang), `<html lang>` динамический.

Скрипты настройки: `scripts/i18n-langs.php` (языки + URL), `scripts/i18n-content.php`
(переводы кейсов), `scripts/i18n-slugfix.php` (slug). Перевод UI обновлять так:
```bash
# 1) пере-извлечь строки
docker compose run --rm wpcli i18n make-pot wp-content/themes/davidv \
  wp-content/themes/davidv/languages/davidv.pot --domain=davidv
# 2) дописать переводы в davidv-uk.po / davidv-ru_RU.po, затем скомпилировать
docker compose run --rm wpcli i18n make-mo wp-content/themes/davidv/languages \
  wp-content/themes/davidv/languages
```
Скриншоты прикрепляются к конкретной языковой версии кейса по её slug
(`capture.sh <url> devops-uk` — в украинский кейс).

## Безопасность

- Вход в админку скрыт (`/***REDACTED***/`), `/wp-login.php` → 404
- XML-RPC выключен, перечисление пользователей заблокировано
- Лимит попыток входа, `DISALLOW_FILE_EDIT`, авто-обновления ядра
- Заголовки HSTS / nosniff / frame-options на уровне Caddy
- Хост: ufw (только 22/80/443), fail2ban, вход по SSH-ключу
