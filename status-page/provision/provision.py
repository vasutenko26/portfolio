#!/usr/bin/env python3
"""
Идемпотентный провижн Uptime Kuma через его socket.io API.

Делает (повторный запуск безопасен):
  1. первичную настройку админа (если инстанс пустой), затем логин;
  2. нотификацию Telegram (по умолчанию, применяется ко всем мониторам);
  3. HTTP-мониторы из monitors.yml (с проверкой срока TLS-сертификата);
  4. публичную статус-страницу со списком сервисов и историей инцидентов.

Конфиг сервисов — monitors.yml. Секреты — только из env.
"""
import os
import sys
import logging

import yaml
from uptime_kuma_api import UptimeKumaApi, MonitorType, NotificationType

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger("provision")

KUMA_URL = os.environ["KUMA_URL"]
ADMIN_USER = os.environ["KUMA_ADMIN_USER"]
ADMIN_PASS = os.environ["KUMA_ADMIN_PASSWORD"]
# Техничка идёт в бот «Фриланс сервер» (тот же, что бэкапы/серверные отчёты).
TG_TOKEN = os.environ["SERVER_BOT_TOKEN"]
TG_CHAT = os.environ["SERVER_CHAT_ID"]
STATUS_DOMAIN = os.environ.get("STATUS_DOMAIN", "status.davidvasutenko.fun")

NOTIF_NAME = "Фриланс сервер"
# Имена нотификаций из прошлых версий — мигрируем (удаляем) при провижне.
STALE_NOTIF_NAMES = ("Telegram (infra)",)


def truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def load_config() -> dict:
    with open(os.path.join(os.path.dirname(__file__), "monitors.yml")) as f:
        return yaml.safe_load(f)


def ensure_login(api: UptimeKumaApi) -> None:
    if api.need_setup():
        log.info("Свежий инстанс — создаю админа %r", ADMIN_USER)
        api.setup(ADMIN_USER, ADMIN_PASS)
    api.login(ADMIN_USER, ADMIN_PASS)
    log.info("Залогинен как %r", ADMIN_USER)


def ensure_notification(api: UptimeKumaApi) -> int:
    existing = {n["name"]: n["id"] for n in api.get_notifications()}

    # Миграция: убрать устаревшие нотификации (например, личный бот из v1).
    for stale in STALE_NOTIF_NAMES:
        if stale != NOTIF_NAME and stale in existing:
            api.delete_notification(existing[stale])
            log.info("Удалена устаревшая нотификация %r", stale)

    kwargs = dict(
        type=NotificationType.TELEGRAM,
        isDefault=True,
        applyExisting=True,
        telegramBotToken=TG_TOKEN,
        telegramChatID=TG_CHAT,
    )
    if NOTIF_NAME in existing:
        nid = existing[NOTIF_NAME]
        api.edit_notification(nid, name=NOTIF_NAME, **kwargs)
        log.info("Обновлена нотификация %r (id=%s)", NOTIF_NAME, nid)
        return nid

    api.add_notification(name=NOTIF_NAME, **kwargs)
    nid = next(n["id"] for n in api.get_notifications() if n["name"] == NOTIF_NAME)
    log.info("Создана нотификация %r (id=%s)", NOTIF_NAME, nid)
    return nid


def ensure_monitor(api: UptimeKumaApi, spec: dict, notif_id: int,
                   existing: dict) -> int | None:
    req = spec.get("requires_env")
    if req and not truthy(req):
        log.info("Пропуск монитора %r (нет env %s)", spec["name"], req)
        return None

    params = dict(
        type=MonitorType.HTTP,
        name=spec["name"],
        url=spec["url"],
        interval=spec.get("interval", 60),
        retryInterval=spec.get("retryInterval", 60),
        maxretries=spec.get("maxretries", 3),
        accepted_statuscodes=spec.get("accepted_statuscodes", ["200-299"]),
        expiryNotification=True,   # алерт о скором истечении TLS-сертификата
        ignoreTls=False,           # проверять валидность/срок сертификата
        notificationIDList={str(notif_id): True},
    )

    if spec["name"] in existing:
        mid = existing[spec["name"]]
        api.edit_monitor(mid, **params)
        log.info("Обновлён монитор %r (id=%s)", spec["name"], mid)
        return mid

    res = api.add_monitor(**params)
    mid = res["monitorID"]
    log.info("Создан монитор %r (id=%s) → %s", spec["name"], mid, spec["url"])
    return mid


def ensure_status_page(api: UptimeKumaApi, cfg: dict, monitor_ids: list[int]) -> None:
    sp = cfg["status_page"]
    slug = sp["slug"]
    existing = {p["slug"] for p in api.get_status_pages()}
    if slug not in existing:
        api.add_status_page(slug, sp["title"])
        log.info("Создана статус-страница /%s", slug)

    api.save_status_page(
        slug,
        title=sp["title"],
        description=sp.get("description", ""),
        published=True,
        showTags=False,
        showPoweredBy=False,
        domainNameList=[STATUS_DOMAIN],
        publicGroupList=[{
            "name": sp.get("group", "Services"),
            "weight": 1,
            "monitorList": [{"id": mid} for mid in monitor_ids],
        }],
    )
    log.info("Статус-страница опубликована: https://%s/status/%s (%d сервисов)",
             STATUS_DOMAIN, slug, len(monitor_ids))


def main() -> int:
    cfg = load_config()
    log.info("Подключаюсь к %s", KUMA_URL)
    api = UptimeKumaApi(KUMA_URL, timeout=60)
    try:
        ensure_login(api)
        notif_id = ensure_notification(api)

        existing = {m["name"]: m["id"] for m in api.get_monitors()}
        published_ids: list[int] = []
        for spec in cfg["monitors"]:
            mid = ensure_monitor(api, spec, notif_id, existing)
            if mid is not None and spec.get("published", True):
                published_ids.append(mid)

        ensure_status_page(api, cfg, published_ids)
        log.info("Готово.")
        return 0
    finally:
        api.disconnect()


if __name__ == "__main__":
    sys.exit(main())
