#!/usr/bin/env python3
"""Бот «Фриланс сервер»: кнопки для свежих отчётов по требованию.

Кнопки:
  📊 Суточный отчёт — статус сайта (HTTP, ms) + заявок за 24ч (как ежедневный n8n-отчёт).
  🖥 Отчёт по серверу — нагрузка/безопасность/обновления (как суточный systemd-таймер).

Серверный отчёт собирается на хосте через nsenter (контейнер privileged + pid:host),
поэтому fail2ban-client / journalctl / apt-get работают от root, без правок хост-скриптов.
Отвечает только в авторизованном чате (SERVER_CHAT_ID).
"""
import asyncio
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (Application, CommandHandler, MessageHandler, CallbackQueryHandler,
                          ContextTypes, filters)

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s %(message)s", level=logging.INFO)
log = logging.getLogger("serverbot")

TOKEN = os.environ["SERVER_BOT_TOKEN"]
AUTH_CHAT = int(os.environ["SERVER_CHAT_ID"])
SITE_URL = os.environ.get("SITE_HEALTH_URL", "https://davidvasutenko.fun/")
SITE_NAME = os.environ.get("SITE_NAME", "davidvasutenko.fun")
LEADS_CSV = os.environ.get("LEADS_CSV", "/files/leads.csv")
REPORT_SH = os.environ.get("REPORT_SH", "/opt/portfolio/serverbot/server-report-print.sh")
KYIV = ZoneInfo("Europe/Kyiv")

BTN_SITE = "📊 Суточный отчёт"
BTN_SERVER = "🖥 Отчёт по серверу"

KB = ReplyKeyboardMarkup([[KeyboardButton(BTN_SITE)], [KeyboardButton(BTN_SERVER)]],
                         resize_keyboard=True, is_persistent=True)


def _refresh_kb(kind: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh:{kind}")]])


def _authorized(update: Update) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.id == AUTH_CHAT


# ---------- сбор отчётов ----------
async def build_site_report() -> str:
    status, code, ms = "DOWN", 0, 0
    loop = asyncio.get_event_loop()
    t0 = loop.time()
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
            r = await c.get(SITE_URL)
        ms = int((loop.time() - t0) * 1000)
        code = r.status_code
        status = "UP" if 200 <= code < 400 else "DEGRADED"
    except Exception as e:
        ms = int((loop.time() - t0) * 1000)
        status, code = "DOWN", 0
        log.warning("site check failed: %s", e)

    leads24 = 0
    try:
        with open(LEADS_CSV, encoding="utf-8") as f:
            lines = f.read().strip().split("\n")[1:]  # без заголовка
        day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        for ln in lines:
            m = re.match(r'^"([^"]+)"', ln)
            if not m:
                continue
            try:
                ts = datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
            except ValueError:
                continue
            if ts >= day_ago:
                leads24 += 1
    except FileNotFoundError:
        log.warning("leads csv not found: %s", LEADS_CSV)
    except Exception as e:
        log.warning("leads parse failed: %s", e)

    icon = "✅" if status == "UP" else ("⚠️" if status == "DEGRADED" else "🔴")
    when = datetime.now(KYIV).strftime("%d.%m.%Y, %H:%M:%S")
    return (f"📊 Суточный отчёт — {SITE_NAME}\n\n"
            f"{icon} Сайт: {status} (HTTP {code}, {ms} ms)\n"
            f"📨 Заявок за 24ч: {leads24}\n"
            f"🕑 {when}")


async def build_server_report() -> str:
    cmd = ["nsenter", "-t", "1", "-m", "-u", "-i", "-n", "-p", "--", "bash", REPORT_SH]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=45)
        text = out.decode("utf-8", "replace").strip()
        if proc.returncode != 0 or not text:
            return f"⚠️ Не удалось собрать отчёт по серверу (rc={proc.returncode}).\n{text[:500]}"
        return text
    except asyncio.TimeoutError:
        return "⚠️ Сбор отчёта по серверу превысил тайм-аут (45с)."
    except Exception as e:
        log.exception("server report failed")
        return f"⚠️ Ошибка сбора отчёта по серверу: {e}"


# ---------- хендлеры ----------
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        return
    await update.message.reply_text(
        "🤖 Фриланс-сервер — отчёты по требованию.\n"
        "Жми кнопку внизу, чтобы получить свежий отчёт в любой момент.",
        reply_markup=KB)


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _authorized(update):
        return
    txt = (update.message.text or "").strip()
    if txt == BTN_SITE:
        await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        await update.message.reply_text(await build_site_report(), reply_markup=_refresh_kb("site"))
    elif txt == BTN_SERVER:
        await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        await update.message.reply_text(await build_server_report(), reply_markup=_refresh_kb("server"))
    else:
        await update.message.reply_text("Выбери отчёт кнопкой ниже 👇", reply_markup=KB)


async def on_refresh(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not _authorized(update):
        await q.answer()
        return
    kind = q.data.split(":", 1)[1]
    await q.answer("Обновляю…")
    await ctx.bot.send_chat_action(q.message.chat.id, ChatAction.TYPING)
    text = await (build_site_report() if kind == "site" else build_server_report())
    try:
        await q.edit_message_text(text, reply_markup=_refresh_kb(kind))
    except Exception:
        # текст не изменился / нельзя редактировать — шлём новым сообщением
        await ctx.bot.send_message(q.message.chat.id, text, reply_markup=_refresh_kb(kind))


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("report", cmd_start))
    app.add_handler(CallbackQueryHandler(on_refresh, pattern=r"^refresh:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    log.info("server-bot started (auth chat %s)", AUTH_CHAT)
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
