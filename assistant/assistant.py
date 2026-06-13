#!/usr/bin/env python3
"""
Парный бот-ассистент задач (Telegram) — ты и друг.

Возможности:
• Ставить задачи себе и друг другу, с дедлайнами.
• Gemini разбивает новую задачу на подзадачи и даёт советы.
• Корректировать свои задачи: название, дедлайн, подзадачи, переразбить.
• Напоминания: утренний дайджест 09:30 (Киев), «отложенные», дедлайны.
• 👊 Подзатыльник другу.

Секреты — только из env. Хранилище — SQLite в томе /data.
Доступ только у двух известных пользователей (OWNER_ID, FRIEND_ID).
"""
import os
import re
import json
import html
import base64
import io
import csv
import random
import logging
import sqlite3
import calendar
import unicodedata
import datetime as dt
from zoneinfo import ZoneInfo

import httpx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from telegram import (
    Update, BotCommand,
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton,
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)

# ---------------------------------------------------------------- конфиг
TOKEN     = os.environ["TELEGRAM_BOT_TOKEN"]
OWNER_ID  = int(os.environ["TELEGRAM_CHAT_ID"])
FRIEND_ID = int(os.environ.get("FRIEND_CHAT_ID", "1178778072"))
GEM_KEY   = os.environ.get("GEMINI_API_KEY", "")
GEM_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
TZ        = ZoneInfo(os.environ.get("ASSISTANT_TZ", "Europe/Kyiv"))
DB_PATH   = os.environ.get("ASSISTANT_DB", "/data/assistant.db")
DIGEST_H, DIGEST_M = 9, 30

ALLOWED = {OWNER_ID, FRIEND_ID}
NAME_DEFAULT = {OWNER_ID: "владелец", FRIEND_ID: "друг"}

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s — %(message)s", level=logging.INFO)
log = logging.getLogger("assistant")

# ---------------------------------------------------------------- меню
BTN_NEW   = "📝 Новая задача"
BTN_LIST  = "📋 Мои задачи"
BTN_DASH  = "🗂 Дашборд"
BTN_DELEG = "📤 Поручено мной"
BTN_PROG  = "📊 Прогресс"
BTN_PLAN  = "🌅 План дня"
BTN_SLAP  = "👊 Подзатыльник"
BTN_HELP  = "ℹ️ Помощь"
MAIN_KB = ReplyKeyboardMarkup(
    [[KeyboardButton(BTN_NEW), KeyboardButton(BTN_LIST)],
     [KeyboardButton(BTN_DASH), KeyboardButton(BTN_DELEG)],
     [KeyboardButton(BTN_PROG), KeyboardButton(BTN_PLAN)],
     [KeyboardButton(BTN_SLAP), KeyboardButton(BTN_HELP)]],
    resize_keyboard=True,
)

USERS_ORDER = [OWNER_ID, FRIEND_ID]
PERIODS = {"day": (1, "день"), "week": (7, "неделю"), "2w": (14, "2 недели")}
# приоритет: 1 высокий .. 3 низкий (сортировка по возрастанию)
PRIO = {1: ("🔴", "высокий"), 2: ("🟡", "средний"), 3: ("⚪", "низкий")}
PRIO_CODE = {"high": 1, "medium": 2, "med": 2, "low": 3}
RECUR = {"daily": "ежедневно", "weekly": "еженедельно", "monthly": "ежемесячно"}
# статусы задач: pending (ждёт принятия) · open · done · declined

# ---------------------------------------------------------------- БД
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _ensure_col(c, table, col, decl):
    cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
    if col not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
        log.info("migrate: added %s.%s", table, col)


def init_db():
    with db() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id    INTEGER NOT NULL,           -- assignee: чья это задача (в чьём списке)
            creator_id INTEGER,                    -- кто поставил
            title      TEXT NOT NULL,
            status     TEXT NOT NULL DEFAULT 'open',
            estimate   TEXT,
            advice     TEXT,
            created_at TEXT NOT NULL,
            done_at    TEXT,
            remind_at  TEXT,                        -- личное «отложить»
            deadline   TEXT,                        -- срок
            deadline_notified INTEGER NOT NULL DEFAULT 0,
            comment    TEXT,                          -- обязательный итог при выполнении
            priority   INTEGER NOT NULL DEFAULT 2,    -- 1 высокий .. 3 низкий
            decline_reason TEXT,                       -- причина отказа от поручения
            recur      TEXT,                           -- daily | weekly | monthly | NULL
            tags       TEXT,                           -- через запятую, нижний регистр
            pre_day_notified  INTEGER NOT NULL DEFAULT 0,
            pre_hour_notified INTEGER NOT NULL DEFAULT 0,
            last_escalate TEXT,                         -- iso последней эскалации просрочки
            card_msg_id INTEGER
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS comments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            file_id TEXT,
            file_type TEXT
        )""")
        _ensure_col(c, "comments", "file_id", "TEXT")
        _ensure_col(c, "comments", "file_type", "TEXT")
        c.execute("""
        CREATE TABLE IF NOT EXISTS subtasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            idx INTEGER NOT NULL, text TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0
        )""")
        c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT)")
        _ensure_col(c, "users", "points", "INTEGER NOT NULL DEFAULT 0")
        _ensure_col(c, "users", "streak", "INTEGER NOT NULL DEFAULT 0")
        _ensure_col(c, "users", "last_done_date", "TEXT")
        # миграция старой схемы
        _ensure_col(c, "tasks", "creator_id", "INTEGER")
        _ensure_col(c, "tasks", "deadline", "TEXT")
        _ensure_col(c, "tasks", "deadline_notified", "INTEGER NOT NULL DEFAULT 0")
        _ensure_col(c, "tasks", "comment", "TEXT")
        _ensure_col(c, "tasks", "priority", "INTEGER NOT NULL DEFAULT 2")
        _ensure_col(c, "tasks", "decline_reason", "TEXT")
        _ensure_col(c, "tasks", "recur", "TEXT")
        _ensure_col(c, "tasks", "tags", "TEXT")
        _ensure_col(c, "tasks", "pre_day_notified", "INTEGER NOT NULL DEFAULT 0")
        _ensure_col(c, "tasks", "pre_hour_notified", "INTEGER NOT NULL DEFAULT 0")
        _ensure_col(c, "tasks", "last_escalate", "TEXT")
        c.execute("UPDATE tasks SET creator_id=chat_id WHERE creator_id IS NULL")


# ---------- время
def now_utc():            return dt.datetime.now(dt.timezone.utc)
def iso(d):               return d.astimezone(dt.timezone.utc).isoformat()
def parse_iso(s):         return dt.datetime.fromisoformat(s)
def fmt_local(s):
    try:    return parse_iso(s).astimezone(TZ).strftime("%d.%m %H:%M")
    except Exception:  return s


# ---------- пользователи / имена
def upsert_user(uid, name):
    if uid not in ALLOWED:
        return
    with db() as c:
        c.execute("INSERT INTO users(id,name) VALUES(?,?) "
                  "ON CONFLICT(id) DO UPDATE SET name=excluded.name", (uid, name or ""))


def clean_name(s):
    """Срезаем zalgo: комбинирующие (Mn/Me) и форматирующие/zero-width (Cf) символы."""
    if not s:
        return s
    out = "".join(ch for ch in unicodedata.normalize("NFC", s)
                  if unicodedata.category(ch) not in ("Mn", "Me", "Cf")).strip()
    return (out or s)[:32]


def uname(uid):
    with db() as c:
        r = c.execute("SELECT name FROM users WHERE id=?", (uid,)).fetchone()
    if r and r["name"]:
        return clean_name(r["name"])
    return NAME_DEFAULT.get(uid, "пользователь")


def other_user(uid):
    return FRIEND_ID if uid == OWNER_ID else OWNER_ID


PRAISE = ["Красава! 💪", "Так держать! 🚀", "Огонь! 🔥", "Чисто сработано ✨",
          "Минус задача, плюс карма 😎", "Машина! 🤖", "Вот это темп! ⚡", "Респект 🙌"]


def award_completion(uid, task):
    """Начисляет очки и обновляет стрик при выполнении. Возвращает (earned, total, streak)."""
    base = {1: 3, 2: 2, 3: 1}.get(task["priority"] or 2, 2)
    on_time = not (task["deadline"] and parse_iso(task["deadline"]) < now_utc())
    earned = base + (1 if on_time else 0)
    today = dt.datetime.now(TZ).date()
    with db() as c:
        r = c.execute("SELECT points,streak,last_done_date FROM users WHERE id=?", (uid,)).fetchone()
        points = (r["points"] if r else 0) + earned
        streak = r["streak"] if r else 0
        last = r["last_done_date"] if r else None
        if last != today.isoformat():
            yest = (today - dt.timedelta(days=1)).isoformat()
            streak = streak + 1 if last == yest else 1
        c.execute("INSERT INTO users(id,name,points,streak,last_done_date) VALUES(?,?,?,?,?) "
                  "ON CONFLICT(id) DO UPDATE SET points=?, streak=?, last_done_date=?",
                  (uid, uname(uid), points, streak, today.isoformat(), points, streak, today.isoformat()))
    return earned, points, streak


def get_gamify(uid):
    with db() as c:
        r = c.execute("SELECT points,streak FROM users WHERE id=?", (uid,)).fetchone()
    return (r["points"] if r else 0, r["streak"] if r else 0)


# ---------- задачи
def create_task(assignee, creator, title, breakdown, deadline_iso, priority=2, status="open",
                recur=None, tags=None):
    with db() as c:
        cur = c.execute(
            "INSERT INTO tasks(chat_id,creator_id,title,estimate,advice,created_at,deadline,"
            "priority,status,recur,tags) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (assignee, creator, title, breakdown.get("estimate"),
             json.dumps(breakdown.get("advice", []), ensure_ascii=False),
             iso(now_utc()), deadline_iso, priority, status, recur, tags))
        tid = cur.lastrowid
        for i, s in enumerate(breakdown.get("subtasks", [])):
            c.execute("INSERT INTO subtasks(task_id,idx,text) VALUES(?,?,?)", (tid, i, str(s)[:300]))
        return tid


def get_task(tid):
    with db() as c:
        t = c.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
        if not t:
            return None
        subs = c.execute("SELECT * FROM subtasks WHERE task_id=? ORDER BY idx", (tid,)).fetchall()
    return t, subs


def _list(where, params):
    with db() as c:
        rows = c.execute(
            f"SELECT * FROM tasks WHERE {where} ORDER BY priority, "
            "CASE WHEN deadline IS NULL THEN 1 ELSE 0 END, deadline, created_at", params).fetchall()
        out = []
        for t in rows:
            d = c.execute("SELECT COUNT(*) n, COALESCE(SUM(done),0) d FROM subtasks WHERE task_id=?",
                          (t["id"],)).fetchone()
            out.append((t, d["n"], d["d"]))
    return out


def list_assigned(uid):   return _list("chat_id=? AND status IN ('open','pending')", (uid,))
def list_delegated(uid):  return _list("creator_id=? AND chat_id<>? AND status IN ('open','pending')", (uid, uid))


def list_done_since(cutoff_iso):
    with db() as c:
        return c.execute("SELECT * FROM tasks WHERE status='done' AND done_at IS NOT NULL "
                         "AND done_at>=? ORDER BY done_at DESC", (cutoff_iso,)).fetchall()


def toggle_subtask(tid, sidx):
    with db() as c: c.execute("UPDATE subtasks SET done=1-done WHERE task_id=? AND idx=?", (tid, sidx))
def add_subtask(tid, text):
    with db() as c:
        nxt = c.execute("SELECT COALESCE(MAX(idx)+1,0) n FROM subtasks WHERE task_id=?", (tid,)).fetchone()["n"]
        c.execute("INSERT INTO subtasks(task_id,idx,text) VALUES(?,?,?)", (tid, nxt, text[:300]))
def edit_subtask(tid, idx, text):
    with db() as c:
        c.execute("UPDATE subtasks SET text=? WHERE task_id=? AND idx=?", (text[:300], tid, idx))
def delete_subtask(tid, idx):
    with db() as c:
        c.execute("DELETE FROM subtasks WHERE task_id=? AND idx=?", (tid, idx))
        # переиндексация, чтобы номера оставались 1..n
        rows = c.execute("SELECT id FROM subtasks WHERE task_id=? ORDER BY idx", (tid,)).fetchall()
        for new_idx, r in enumerate(rows):
            c.execute("UPDATE subtasks SET idx=? WHERE id=?", (new_idx, r["id"]))
def replace_subtasks(tid, bd):
    with db() as c:
        c.execute("DELETE FROM subtasks WHERE task_id=?", (tid,))
        for i, s in enumerate(bd.get("subtasks", [])):
            c.execute("INSERT INTO subtasks(task_id,idx,text) VALUES(?,?,?)", (tid, i, str(s)[:300]))
        c.execute("UPDATE tasks SET estimate=?, advice=? WHERE id=?",
                  (bd.get("estimate"), json.dumps(bd.get("advice", []), ensure_ascii=False), tid))
def set_status(tid, status):
    with db() as c:
        if status == "done":
            c.execute("UPDATE tasks SET status='done', done_at=?, remind_at=NULL WHERE id=?",
                      (iso(now_utc()), tid))
        else:  # вернуть в работу: сбросить итог прошлого цикла
            c.execute("UPDATE tasks SET status=?, done_at=NULL, remind_at=NULL, comment=NULL WHERE id=?",
                      (status, tid))
def set_comment(tid, text):
    with db() as c: c.execute("UPDATE tasks SET comment=? WHERE id=?", (text, tid))
def set_priority(tid, p):
    with db() as c: c.execute("UPDATE tasks SET priority=? WHERE id=?", (p, tid))
def set_recur(tid, val):
    with db() as c: c.execute("UPDATE tasks SET recur=? WHERE id=?", (val, tid))
def set_tags(tid, val):
    with db() as c: c.execute("UPDATE tasks SET tags=? WHERE id=?", (val, tid))
def set_assignee(tid, new_assignee, status):
    with db() as c:
        c.execute("UPDATE tasks SET chat_id=?, status=?, card_msg_id=NULL WHERE id=?",
                  (new_assignee, status, tid))
def set_declined(tid, reason):
    with db() as c:
        c.execute("UPDATE tasks SET status='declined', decline_reason=? WHERE id=?", (reason, tid))


def add_period(base, recur):
    if recur == "daily":
        return base + dt.timedelta(days=1)
    if recur == "weekly":
        return base + dt.timedelta(days=7)
    if recur == "monthly":
        m = base.month % 12 + 1
        y = base.year + (1 if base.month == 12 else 0)
        day = min(base.day, calendar.monthrange(y, m)[1])
        return base.replace(year=y, month=m, day=day)
    return None


def clone_for_recur(t, subs):
    """Создаёт следующее повторение завершённой задачи. Возвращает (tid, deadline|None)."""
    recur = t["recur"]
    if not recur:
        return None, None
    nd_iso = None
    nd = None
    if t["deadline"]:
        base = parse_iso(t["deadline"])
        nd = add_period(base, recur)
        if nd and nd <= now_utc():           # старый дедлайн в прошлом — считаем от сейчас
            nd = add_period(now_utc(), recur)
    else:
        nd = add_period(now_utc(), recur)
    if nd:
        nd_iso = iso(nd)
    bd = {"subtasks": [s["text"] for s in subs],
          "advice": json.loads(t["advice"] or "[]"), "estimate": t["estimate"]}
    tid = create_task(t["chat_id"], t["creator_id"], t["title"], bd, nd_iso,
                      priority=t["priority"], status="open", recur=recur, tags=t["tags"])
    return tid, nd
def delete_task(tid):
    with db() as c:
        c.execute("DELETE FROM subtasks WHERE task_id=?", (tid,))
        c.execute("DELETE FROM comments WHERE task_id=?", (tid,))
        c.execute("DELETE FROM tasks WHERE id=?", (tid,))
def set_remind(tid, when):
    with db() as c: c.execute("UPDATE tasks SET remind_at=? WHERE id=?", (iso(when) if when else None, tid))
def set_deadline(tid, when):
    with db() as c:
        c.execute("UPDATE tasks SET deadline=?, deadline_notified=0, pre_day_notified=0, "
                  "pre_hour_notified=0, last_escalate=NULL WHERE id=?",
                  (iso(when) if when else None, tid))
def set_flag(tid, col, val):
    assert col in ("deadline_notified", "pre_day_notified", "pre_hour_notified")
    with db() as c: c.execute(f"UPDATE tasks SET {col}=? WHERE id=?", (val, tid))
def set_last_escalate(tid, when_iso):
    with db() as c: c.execute("UPDATE tasks SET last_escalate=? WHERE id=?", (when_iso, tid))


def add_comment(tid, author, text, file_id=None, file_type=None):
    with db() as c:
        c.execute("INSERT INTO comments(task_id,author_id,text,created_at,file_id,file_type) "
                  "VALUES(?,?,?,?,?,?)", (tid, author, text[:1000], iso(now_utc()), file_id, file_type))
def get_comments(tid):
    with db() as c:
        return c.execute("SELECT * FROM comments WHERE task_id=? ORDER BY created_at", (tid,)).fetchall()
def get_comment(cid):
    with db() as c:
        return c.execute("SELECT * FROM comments WHERE id=?", (cid,)).fetchone()
def count_comments(tid):
    with db() as c:
        return c.execute("SELECT COUNT(*) n FROM comments WHERE task_id=?", (tid,)).fetchone()["n"]
def set_title(tid, title):
    with db() as c: c.execute("UPDATE tasks SET title=? WHERE id=?", (title[:500], tid))
def set_card_msg(tid, mid):
    with db() as c: c.execute("UPDATE tasks SET card_msg_id=? WHERE id=?", (mid, tid))


def due_personal(uid):
    n = iso(now_utc())
    with db() as c:
        return c.execute("SELECT id FROM tasks WHERE chat_id=? AND status='open' "
                         "AND remind_at IS NOT NULL AND remind_at<=?", (uid, n)).fetchall()
def deadline_jobs(uid):
    with db() as c:
        return c.execute("SELECT * FROM tasks WHERE chat_id=? AND status='open' "
                         "AND deadline IS NOT NULL", (uid,)).fetchall()


def stats(uid):
    wk = iso(now_utc() - dt.timedelta(days=7))
    with db() as c:
        op = c.execute("SELECT COUNT(*) n FROM tasks WHERE chat_id=? AND status IN ('open','pending')",
                       (uid,)).fetchone()["n"]
        dn = c.execute("SELECT COUNT(*) n FROM tasks WHERE chat_id=? AND status='done'", (uid,)).fetchone()["n"]
        wkn = c.execute("SELECT COUNT(*) n FROM tasks WHERE chat_id=? AND status='done' AND done_at>=?",
                        (uid, wk)).fetchone()["n"]
        deleg = c.execute("SELECT COUNT(*) n FROM tasks WHERE creator_id=? AND chat_id<>? "
                          "AND status IN ('open','pending')", (uid, uid)).fetchone()["n"]
        overdue = c.execute("SELECT COUNT(*) n FROM tasks WHERE chat_id=? AND status IN ('open','pending') "
                            "AND deadline IS NOT NULL AND deadline<?", (uid, iso(now_utc()))).fetchone()["n"]
        oldest = c.execute("SELECT title,created_at FROM tasks WHERE chat_id=? AND status IN ('open','pending') "
                           "ORDER BY created_at LIMIT 1", (uid,)).fetchone()
    return {"open": op, "done": dn, "week": wkn, "deleg": deleg, "overdue": overdue, "oldest": oldest}


# ---------------------------------------------------------------- Gemini
async def gemini_breakdown(title):
    if not GEM_KEY:
        return {}
    prompt = (
        "Ты — практичный ассистент по продуктивности. Разбей задачу на 3–6 конкретных "
        "выполнимых подзадач в логичном порядке и дай 2–3 коротких практичных совета. Пиши на "
        "языке задачи, кратко. Верни СТРОГО JSON без markdown: "
        '{"subtasks":["..."],"advice":["..."],"estimate":"грубая оценка времени"}.\n'
        "Задача: <<<" + title + ">>>")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEM_MODEL}:generateContent?key={GEM_KEY}")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"}}
    try:
        async with httpx.AsyncClient(timeout=30) as cl:
            r = await cl.post(url, json=body); r.raise_for_status()
            data = r.json()
        out = json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
        return {"subtasks": [str(x).strip() for x in out.get("subtasks", []) if str(x).strip()][:8],
                "advice": [str(x).strip() for x in out.get("advice", []) if str(x).strip()][:4],
                "estimate": str(out.get("estimate", "")).strip()}
    except Exception as e:                                    # noqa: BLE001
        log.warning("Gemini failed: %s", e)
        return {}


async def gemini_plan(text):
    """Естественный ввод → {title, priority(1-3), deadline_iso|None, subtasks, advice, estimate}."""
    manual_tags = parse_hashtags(text)
    fallback = {"title": text[:120].strip(), "priority": 2, "deadline_iso": None,
                "subtasks": [], "advice": [], "estimate": "", "tags": ",".join(manual_tags)}
    if not GEM_KEY:
        return fallback
    now_l = dt.datetime.now(TZ).strftime("%Y-%m-%d %H:%M (%A)")
    prompt = (
        f"Текущее время (Europe/Kyiv): {now_l}. Пользователь описал задачу свободным текстом. "
        "Извлеки суть и верни СТРОГО JSON без markdown по схеме: "
        '{"title":"краткий заголовок задачи (без даты и слов про важность)",'
        '"priority":"high|medium|low",'
        '"deadline":"YYYY-MM-DD HH:MM в часовом поясе Киева, или null если срок не указан",'
        '"subtasks":["3-6 конкретных подзадач"],"advice":["2-3 коротких совета"],'
        '"estimate":"грубая оценка времени",'
        '"tags":["1-3 коротких тега-категории в нижнем регистре, без #"]}. '
        "Если важность не указана — medium; если срок не указан — null. "
        "Язык вывода = язык задачи.\nТекст: <<<" + text + ">>>")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEM_MODEL}:generateContent?key={GEM_KEY}")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"}}
    try:
        async with httpx.AsyncClient(timeout=30) as cl:
            r = await cl.post(url, json=body); r.raise_for_status()
            out = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
        dl_iso = None
        dl = str(out.get("deadline") or "").strip()
        if dl and dl.lower() != "null":
            try:
                dl_iso = iso(dt.datetime.strptime(dl[:16], "%Y-%m-%d %H:%M").replace(tzinfo=TZ))
            except ValueError:
                dl_iso = None
        return {
            "title": (str(out.get("title") or "").strip() or text[:120].strip())[:300],
            "priority": PRIO_CODE.get(str(out.get("priority", "medium")).lower(), 2),
            "deadline_iso": dl_iso,
            "subtasks": [str(x).strip() for x in out.get("subtasks", []) if str(x).strip()][:8],
            "advice": [str(x).strip() for x in out.get("advice", []) if str(x).strip()][:4],
            "estimate": str(out.get("estimate", "")).strip(),
            "tags": merge_tags([norm_tag(x) for x in out.get("tags", [])] + manual_tags),
        }
    except Exception as e:                                    # noqa: BLE001
        log.warning("Gemini plan failed: %s", e)
        return fallback


async def gemini_text(prompt, temperature=0.5):
    """Свободный текстовый ответ Gemini (план/ревью). Возвращает строку или ''."""
    if not GEM_KEY:
        return ""
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEM_MODEL}:generateContent?key={GEM_KEY}")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature}}
    try:
        async with httpx.AsyncClient(timeout=40) as cl:
            r = await cl.post(url, json=body); r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:                                    # noqa: BLE001
        log.warning("Gemini text failed: %s", e)
        return ""


async def gemini_transcribe(b64, mime):
    """Расшифровка голосового через Gemini. Возвращает текст или ''."""
    if not GEM_KEY:
        return ""
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEM_MODEL}:generateContent?key={GEM_KEY}")
    body = {"contents": [{"parts": [
        {"text": "Расшифруй это голосовое сообщение дословно. Верни только текст, без комментариев."},
        {"inline_data": {"mime_type": mime or "audio/ogg", "data": b64}}]}],
        "generationConfig": {"temperature": 0.1}}
    try:
        async with httpx.AsyncClient(timeout=60) as cl:
            r = await cl.post(url, json=body); r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:                                    # noqa: BLE001
        log.warning("Gemini transcribe failed: %s", e)
        return ""


def norm_tag(s):
    return re.sub(r"[^0-9a-zа-яё_-]", "", str(s).lower().strip())[:24]


def parse_hashtags(text):
    return [norm_tag(m) for m in re.findall(r"#([0-9A-Za-zА-Яа-яЁё_-]+)", text)]


def merge_tags(tags):
    seen, out = set(), []
    for t in tags:
        t = (t or "").strip()
        if t and t not in seen:
            seen.add(t); out.append(t)
    return ",".join(out[:5])


# ---------------------------------------------------------------- рендер карточки
def render_card(tid):
    res = get_task(tid)
    if not res:
        return None, None
    t, subs = res
    done = t["status"] == "done"
    pending = t["status"] == "pending"
    declined = t["status"] == "declined"
    overdue = (t["status"] in ("open", "pending") and t["deadline"] and parse_iso(t["deadline"]) < now_utc())
    pemoji, plabel = PRIO.get(t["priority"] or 2, PRIO[2])

    head = ("✅ <b>Выполнено</b>\n" if done else "❌ <b>Отклонено</b>\n" if declined
            else "🆕 <b>Ждёт принятия</b>\n" if pending
            else "🔴 <b>Просрочено</b>\n" if overdue else "")
    lines = [f"{head}{pemoji} <b>{html.escape(t['title'])}</b>"]

    if t["creator_id"] and t["creator_id"] != t["chat_id"]:
        lines.append(f"👤 {html.escape(uname(t['creator_id']))} → {html.escape(uname(t['chat_id']))}")

    meta = [f"⚑ {plabel}", f"🗓 {fmt_local(t['created_at'])}"]
    if t["deadline"]:
        meta.append(("🔴" if overdue else "📅") + f" дедлайн {fmt_local(t['deadline'])}")
    if t["recur"]:
        meta.append(f"🔁 {RECUR.get(t['recur'], t['recur'])}")
    if t["estimate"]:
        meta.append(f"⏳ {html.escape(t['estimate'])}")
    if t["remind_at"] and not done:
        meta.append(f"⏰ {fmt_local(t['remind_at'])}")
    lines.append("  ·  ".join(meta))

    if t["tags"]:
        lines.append("🏷 " + " ".join(f"#{html.escape(x)}" for x in t["tags"].split(",") if x))

    if done and t["comment"]:
        lines.append(f"\n💬 <b>Итог:</b> {html.escape(t['comment'])}")
    if declined and t["decline_reason"]:
        lines.append(f"\n❌ <b>Причина отказа:</b> {html.escape(t['decline_reason'])}")

    if subs:
        nd = sum(s["done"] for s in subs)
        filled = round(10 * nd / len(subs))
        bar = "▰" * filled + "▱" * (10 - filled)
        lines.append(f"\n<b>Подзадачи</b> {bar} {nd}/{len(subs)}:")
        for s in subs:
            box = "☑️" if s["done"] else "▫️"
            txt = html.escape(s["text"]); txt = f"<s>{txt}</s>" if s["done"] else txt
            lines.append(f"{box} {s['idx']+1}. {txt}")
    else:
        lines.append("\n<i>Подзадач нет.</i>")

    advice = json.loads(t["advice"] or "[]")
    if advice and not done:
        lines.append("\n💡 <b>Советы</b>:")
        lines += [f"• {html.escape(a)}" for a in advice]

    text = "\n".join(lines)

    if done or declined:
        return text, InlineKeyboardMarkup([[
            InlineKeyboardButton("↩️ В работу", callback_data=f"reopen|{tid}"),
            InlineKeyboardButton("🗑 Удалить", callback_data=f"del|{tid}")]])

    if pending:
        return text, InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Принять", callback_data=f"acc|{tid}"),
             InlineKeyboardButton("❓ Уточнить", callback_data=f"clr|{tid}")],
            [InlineKeyboardButton("❌ Отклонить", callback_data=f"dec|{tid}")]])

    rows, row = [], []
    for s in subs:
        mark = "☑️" if s["done"] else "☐"
        row.append(InlineKeyboardButton(f"{mark} {s['idx']+1}", callback_data=f"tg|{tid}|{s['idx']}"))
        if len(row) == 3: rows.append(row); row = []
    if row: rows.append(row)
    rows.append([InlineKeyboardButton("✅ Завершить", callback_data=f"done|{tid}"),
                 InlineKeyboardButton("⏰ Отложить", callback_data=f"snz|{tid}")])
    if t["creator_id"] and t["creator_id"] != t["chat_id"]:   # совместная задача
        cc = count_comments(tid)
        rows.append([InlineKeyboardButton(f"💬 Обсуждение{f' ({cc})' if cc else ''}", callback_data=f"thr|{tid}"),
                     InlineKeyboardButton("📌 Пинг", callback_data=f"ping|{tid}")])
    rows.append([InlineKeyboardButton("✏️ Название", callback_data=f"edt|{tid}"),
                 InlineKeyboardButton("📅 Дедлайн", callback_data=f"dl|{tid}"),
                 InlineKeyboardButton(f"{pemoji} Важность", callback_data=f"prio|{tid}")])
    rows.append([InlineKeyboardButton("🧩 Подзадачи", callback_data=f"subs|{tid}"),
                 InlineKeyboardButton("🔁 Повтор", callback_data=f"rec|{tid}"),
                 InlineKeyboardButton("🏷 Теги", callback_data=f"tag|{tid}")])
    rows.append([InlineKeyboardButton("👤 Кому", callback_data=f"asg|{tid}"),
                 InlineKeyboardButton("🔄 Переразбить", callback_data=f"re|{tid}"),
                 InlineKeyboardButton("🗑", callback_data=f"del|{tid}")])
    return text, InlineKeyboardMarkup(rows)


def subs_view(tid):
    """Меню управления подзадачами: правка/удаление каждой + добавить."""
    res = get_task(tid)
    if not res:
        return None, None
    t, subs = res
    lines = [f"🧩 <b>Подзадачи</b> — {html.escape(t['title'][:50])}", ""]
    if subs:
        for s in subs:
            box = "☑️" if s["done"] else "▫️"
            lines.append(f"{box} {s['idx']+1}. {html.escape(s['text'])}")
    else:
        lines.append("<i>пока нет</i>")
    rows = []
    for s in subs:
        rows.append([
            InlineKeyboardButton(f"✏️ {s['idx']+1}", callback_data=f"se|{tid}|{s['idx']}"),
            InlineKeyboardButton(f"🗑 {s['idx']+1}", callback_data=f"sd|{tid}|{s['idx']}")])
    rows.append([InlineKeyboardButton("➕ Добавить", callback_data=f"add|{tid}"),
                 InlineKeyboardButton("⬅️ Назад", callback_data=f"open|{tid}")])
    return "\n".join(lines), InlineKeyboardMarkup(rows)


def recur_menu(tid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ежедневно", callback_data=f"rs|{tid}|daily"),
         InlineKeyboardButton("Еженедельно", callback_data=f"rs|{tid}|weekly")],
        [InlineKeyboardButton("Ежемесячно", callback_data=f"rs|{tid}|monthly"),
         InlineKeyboardButton("✖️ Без повтора", callback_data=f"rs|{tid}|none")],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"open|{tid}")]])


def assign_menu(tid, uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Себе", callback_data=f"as|{tid}|self"),
         InlineKeyboardButton(f"🤝 {uname(other_user(uid))}", callback_data=f"as|{tid}|other")],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"open|{tid}")]])


def thread_view(tid):
    res = get_task(tid)
    if not res:
        return None, None
    t = res[0]
    cms = get_comments(tid)
    lines = [f"💬 <b>Обсуждение</b> — {html.escape(t['title'][:50])}", ""]
    if not cms:
        lines.append("<i>пока нет сообщений</i>")
    file_btns = []
    for cm in cms[-15:]:
        lines.append(f"<b>{html.escape(uname(cm['author_id']))}</b> · {fmt_local(cm['created_at'])}")
        if cm["file_id"]:
            icon = "🖼" if cm["file_type"] == "photo" else "📎"
            lines.append(f"{icon} вложение" + (f": {html.escape(cm['text'])}" if cm["text"] else ""))
            file_btns.append(InlineKeyboardButton(f"{icon} {fmt_local(cm['created_at'])[6:]}",
                                                  callback_data=f"att|{cm['id']}"))
        else:
            lines.append(html.escape(cm["text"]))
        lines.append("")
    rows = [[InlineKeyboardButton("✍️ Написать", callback_data=f"tc|{tid}"),
             InlineKeyboardButton("📎 Вложить", callback_data=f"atc|{tid}")]]
    if file_btns:
        rows.append(file_btns[:4])
    rows.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"open|{tid}")])
    return "\n".join(lines), InlineKeyboardMarkup(rows)


def reminder_kb(tid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏰ +1ч", callback_data=f"sn|{tid}|1h"),
         InlineKeyboardButton("+3ч", callback_data=f"sn|{tid}|3h"),
         InlineKeyboardButton("завтра", callback_data=f"sn|{tid}|morn")],
        [InlineKeyboardButton("➡️ Открыть задачу", callback_data=f"open|{tid}")]])


async def send_reminder(context, uid, tid, head):
    res = get_task(tid)
    if not res:
        return
    t = res[0]
    pe = PRIO.get(t["priority"] or 2, PRIO[2])[0]
    dl = f"\n📅 дедлайн {fmt_local(t['deadline'])}" if t["deadline"] else ""
    txt = f"{head}\n{pe} <b>{html.escape(t['title'])}</b>{dl}"
    try:
        await context.bot.send_message(uid, txt, reply_markup=reminder_kb(tid),
                                       parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:                                    # noqa: BLE001
        log.info("reminder to %s skipped: %s", uid, e)


async def send_card(context, chat_id, tid, edit=None, prefix=None):
    text, kb = render_card(tid)
    if text is None:
        return
    if prefix:
        text = prefix + "\n\n" + text
    if edit is not None:
        try:
            await edit.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML,
                                 disable_web_page_preview=True)
            set_card_msg(tid, edit.message_id); return
        except Exception as e:                               # noqa: BLE001
            log.info("edit failed: %s", e)
    msg = await context.bot.send_message(chat_id, text, reply_markup=kb,
                                         parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    set_card_msg(tid, msg.message_id)


async def refresh_stored_card(context, tid):
    res = get_task(tid)
    if not res: return
    t, _ = res
    text, kb = render_card(tid)
    if t["card_msg_id"]:
        try:
            await context.bot.edit_message_text(text, chat_id=t["chat_id"], message_id=t["card_msg_id"],
                                                reply_markup=kb, parse_mode=ParseMode.HTML,
                                                disable_web_page_preview=True)
            return
        except Exception: pass                               # noqa: BLE001
    await send_card(context, t["chat_id"], tid)


# ---------------------------------------------------------------- доступ
def allowed(update):
    u = update.effective_user
    return bool(u and u.id in ALLOWED)


def can_act(uid, t):
    return uid == t["chat_id"] or uid == t["creator_id"]


def remember(update):
    u = update.effective_user
    if u and u.id in ALLOWED:
        upsert_user(u.id, u.first_name or u.username or "")


# ---------------------------------------------------------------- команды
async def cmd_start(update, context):
    if not allowed(update): return
    remember(update); context.user_data.clear()
    await update.message.reply_text(
        "Привет! Это общий ассистент задач — для тебя и напарника.\n\n"
        f"{BTN_NEW} — поставить задачу себе или напарнику, с дедлайном; "
        "Gemini разобьёт её на подзадачи.\n"
        f"{BTN_LIST} — что нужно сделать мне.\n"
        f"{BTN_DELEG} — что я поручил напарнику.\n"
        f"{BTN_PROG} — прогресс.\n\n"
        "Утром в 09:30 пришлю дайджест, по дедлайнам и «отложенным» — напомню.",
        reply_markup=MAIN_KB)


async def cmd_help(update, context):
    if not allowed(update): return
    remember(update)
    await update.message.reply_text(
        "<b>Как пользоваться</b>\n\n"
        f"• {BTN_NEW} (/new): опиши задачу <b>обычным текстом</b> — можно сразу со сроком и "
        "важностью («созвон с клиентом завтра в 15, важное»). Gemini сам вытащит дедлайн, "
        "приоритет и подзадачи. Затем выбери <b>кому</b>.\n"
        "• Поручил напарнику → он жмёт <b>✅ Принять / ❓ Уточнить / ❌ Отклонить</b>; тебе придёт ответ.\n"
        f"• {BTN_LIST} (/tasks) — мои задачи · {BTN_DASH} (/dashboard) — обзор обоих · "
        f"{BTN_DELEG} (/delegated) — что я поручил.\n"
        "• В карточке: ☐N отметить, ✅ Завершить (с комментарием), ⏰ Отложить, ✏️ Название, "
        "📅 Дедлайн, ⚑ Важность, ➕ Подзадача, 🔁 Переразбить, 🗑.\n"
        f"• {BTN_PROG} (/progress) · {BTN_SLAP} · /cancel — отменить ввод.\n\n"
        "Приоритет (🔴🟡⚪) задаёт порядок в списках и дайджесте. "
        "Дедлайн просрочен — напомню обоим.",
        parse_mode=ParseMode.HTML, reply_markup=MAIN_KB)


async def cmd_cancel(update, context):
    if not allowed(update): return
    had = bool(context.user_data.pop("await", None)) or bool(context.user_data.pop("new", None))
    await update.message.reply_text("Отменил." if had else "Нечего отменять.", reply_markup=MAIN_KB)


async def start_new(update, context):
    if not allowed(update): return
    remember(update)
    context.user_data["await"] = ("title", None)
    await update.message.reply_text(
        "Опиши задачу обычным текстом — можно сразу со сроком и важностью.\n"
        "<i>Напр.: «созвон с клиентом завтра в 15:00, важное» или «купить корм коту».\n"
        "Я сам пойму дедлайн, приоритет и разобью на подзадачи. /cancel — отмена.</i>",
        parse_mode=ParseMode.HTML)


def _tags_of(items):
    seen = []
    for t, _, _ in items:
        for x in (t["tags"] or "").split(","):
            x = x.strip()
            if x and x not in seen:
                seen.append(x)
    return seen


def _filter_kb(items, tag=None):
    rows = list(_list_kb(items).inline_keyboard)
    if tag:
        rows.append([InlineKeyboardButton("✖️ Сбросить фильтр", callback_data="flt|*")])
    else:
        tags = _tags_of(items)
        if tags:
            rows.append([InlineKeyboardButton(f"#{x}", callback_data=f"flt|{x}") for x in tags[:5]])
    return InlineKeyboardMarkup(rows)


async def show_list(update, context):
    if not allowed(update): return
    remember(update)
    uid = update.effective_user.id
    items = list_assigned(uid)
    if not items:
        return await update.message.reply_text("Задач на тебе нет 🎉", reply_markup=MAIN_KB)
    await update.message.reply_text(f"<b>Мои задачи: {len(items)}</b>",
                                    reply_markup=_filter_kb(items), parse_mode=ParseMode.HTML)


async def show_delegated(update, context):
    if not allowed(update): return
    remember(update)
    uid = update.effective_user.id
    items = list_delegated(uid)
    if not items:
        return await update.message.reply_text("Ты пока ничего не поручал напарнику.",
                                               reply_markup=MAIN_KB)
    await update.message.reply_text(
        f"<b>Поручено напарнику: {len(items)}</b>",
        reply_markup=_list_kb(items, who=True), parse_mode=ParseMode.HTML)


def _list_kb(items, who=False):
    rows = []
    for t, n, d in items:
        prog = f" ({d}/{n})" if n else ""
        pe = PRIO.get(t["priority"] or 2, PRIO[2])[0]
        flag = "🆕" if t["status"] == "pending" else \
               ("🔴" if (t["deadline"] and parse_iso(t["deadline"]) < now_utc()) else pe)
        label = (t["title"][:32] + "…") if len(t["title"]) > 33 else t["title"]
        suffix = f" · {fmt_local(t['deadline'])}" if t["deadline"] else ""
        if who:
            suffix += f" · {uname(t['chat_id'])}"
        rows.append([InlineKeyboardButton(f"{flag} {label}{prog}{suffix}",
                                          callback_data=f"open|{t['id']}")])
    return InlineKeyboardMarkup(rows)


def _period_row():
    return [InlineKeyboardButton("День", callback_data="dash|day"),
            InlineKeyboardButton("Неделя", callback_data="dash|week"),
            InlineKeyboardButton("2 недели", callback_data="dash|2w")]


def render_dash_home():
    lines = ["🗂 <b>Дашборд</b> — невыполненные задачи", ""]
    for uid in USERS_ORDER:
        items = list_assigned(uid)
        over = sum(1 for t, _, _ in items if t["deadline"] and parse_iso(t["deadline"]) < now_utc())
        head = f"👤 <b>{html.escape(uname(uid))}</b> — открыто: {len(items)}"
        if over:
            head += f"  (🔴 {over})"
        lines.append(head)
        if not items:
            lines.append("   <i>чисто</i>")
        for t, n, d in items[:12]:
            prog = f" ({d}/{n})" if n else ""
            pe = PRIO.get(t["priority"] or 2, PRIO[2])[0]
            dl = ""
            if t["deadline"]:
                od = parse_iso(t["deadline"]) < now_utc()
                dl = f" · {'🔴 просрочено' if od else '📅 ' + fmt_local(t['deadline'])}"
            frm = f" · от {html.escape(uname(t['creator_id']))}" if t["creator_id"] != uid else ""
            pend = " · 🆕 ждёт принятия" if t["status"] == "pending" else ""
            lines.append(f"   {pe} {html.escape(t['title'][:52])}{prog}{dl}{frm}{pend}")
        if len(items) > 12:
            lines.append(f"   …ещё {len(items) - 12}")
        lines.append("")
    lines.append("Выполненные — кнопками ниже 👇")
    kb = InlineKeyboardMarkup([_period_row(), [InlineKeyboardButton("🔄 Обновить", callback_data="dash|home")]])
    return "\n".join(lines), kb


def render_dash_done(code):
    days, label = PERIODS.get(code, PERIODS["week"])
    cutoff = iso(now_utc() - dt.timedelta(days=days))
    rows = list_done_since(cutoff)
    lines = [f"✅ <b>Выполнено за {label}</b>: {len(rows)}", ""]
    if not rows:
        lines.append("<i>Пока ничего.</i>")
    for t in rows[:20]:
        who = html.escape(uname(t["chat_id"]))
        by = f" (от {html.escape(uname(t['creator_id']))})" if t["creator_id"] != t["chat_id"] else ""
        lines.append(f"✅ {html.escape(t['title'][:60])} — {who}{by}, {fmt_local(t['done_at'])}")
        lines.append(f"   💬 {html.escape(t['comment']) if t['comment'] else '—'}")
    if len(rows) > 20:
        lines.append(f"\n…ещё {len(rows) - 20}")
    kb = InlineKeyboardMarkup([_period_row(), [InlineKeyboardButton("⬅️ К дашборду", callback_data="dash|home")]])
    return "\n".join(lines), kb


async def show_dashboard(update, context):
    if not allowed(update): return
    remember(update)
    text, kb = render_dash_home()
    await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True)


async def show_progress(update, context):
    if not allowed(update): return
    remember(update)
    uid = update.effective_user.id
    s = stats(uid)
    pts, streak = get_gamify(uid)
    lines = ["📊 <b>Прогресс</b>", "",
             f"⭐ Очки: <b>{pts}</b>" + (f"  ·  🔥 стрик: <b>{streak}</b> дн." if streak else ""),
             "",
             f"📌 На мне открыто: <b>{s['open']}</b>" +
             (f"  (🔴 просрочено: {s['overdue']})" if s["overdue"] else ""),
             f"✅ Завершено всего: <b>{s['done']}</b>",
             f"🗓 Закрыто за 7 дней: <b>{s['week']}</b>",
             f"📤 Поручено напарнику (открыто): <b>{s['deleg']}</b>"]
    if s["oldest"]:
        age = (now_utc() - parse_iso(s["oldest"]["created_at"])).days
        lines.append(f"\n⏳ Дольше всего висит: «{html.escape(s['oldest']['title'][:50])}» — {age} дн.")
    await update.message.reply_text(
        "\n".join(lines), parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📈 AI-ревью", callback_data="review"),
             InlineKeyboardButton("📊 Графики", callback_data="charts"),
             InlineKeyboardButton("⬇️ CSV", callback_data="export")]]))


# ---------------------------------------------------------------- AI: план дня / ревью недели
async def build_plan(uid):
    items = list_assigned(uid)
    if not items:
        return "На сегодня задач нет — можно выдохнуть 🙂"
    lines = []
    for t, n, d in items[:20]:
        pe = PRIO.get(t["priority"] or 2, PRIO[2])[1]
        dl = ""
        if t["deadline"]:
            od = parse_iso(t["deadline"]) < now_utc()
            dl = (" ПРОСРОЧЕНО" if od else f" дедлайн {fmt_local(t['deadline'])}")
        lines.append(f"- {t['title']} (важность {pe}{dl}, подзадач {d}/{n})")
    prompt = ("Ты — продуктивный ассистент. Вот мои открытые задачи:\n" + "\n".join(lines) +
              "\n\nСоставь короткий план на день: с чего начать и ПОЧЕМУ, 3-5 пунктов по порядку, "
              "учитывая важность и дедлайны (просроченное и срочное — выше). Без воды, по-русски.")
    return (await gemini_text(prompt)) or "AI сейчас недоступен — начни с просроченного и срочного."


async def build_review(uid):
    wk = iso(now_utc() - dt.timedelta(days=7))
    with db() as c:
        done = c.execute("SELECT title FROM tasks WHERE chat_id=? AND status='done' AND done_at>=?",
                         (uid, wk)).fetchall()
        openr = c.execute("SELECT title,deadline,created_at FROM tasks WHERE chat_id=? "
                          "AND status IN ('open','pending')", (uid,)).fetchall()
    done_t = [r["title"] for r in done]
    stale, overdue = [], []
    for r in openr:
        if r["deadline"] and parse_iso(r["deadline"]) < now_utc():
            overdue.append(r["title"])
        elif (now_utc() - parse_iso(r["created_at"])).days >= 5:
            stale.append(r["title"])
    prompt = ("Сделай короткое еженедельное ревью по моим задачам. По-русски, дружелюбно, без воды.\n"
              f"Выполнено за неделю ({len(done_t)}): {', '.join(done_t) or '—'}\n"
              f"Просрочено ({len(overdue)}): {', '.join(overdue) or '—'}\n"
              f"Висит давно ({len(stale)}): {', '.join(stale) or '—'}\n\n"
              "Дай: 1) что удалось, 2) что буксует и почему, 3) 2-3 конкретных совета на следующую неделю.")
    return (await gemini_text(prompt)) or "AI сейчас недоступен — попробуй позже."


async def show_plan(update, context):
    if not allowed(update): return
    remember(update)
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    txt = await build_plan(update.effective_user.id)
    await update.message.reply_text("🌅 <b>План на день</b>\n\n" + html.escape(txt),
                                    parse_mode=ParseMode.HTML, reply_markup=MAIN_KB)


def build_chart_png():
    """Столбчатый график «выполнено по дням за 14 дней» по обоим. Возвращает BytesIO PNG."""
    days = 14
    today = dt.datetime.now(TZ).date()
    labels = [(today - dt.timedelta(days=days - 1 - i)) for i in range(days)]
    counts = {uid: [0] * days for uid in USERS_ORDER}
    cutoff = iso(now_utc() - dt.timedelta(days=days))
    with db() as c:
        rows = c.execute("SELECT chat_id,done_at FROM tasks WHERE status='done' AND done_at>=?",
                         (cutoff,)).fetchall()
    idx = {d: i for i, d in enumerate(labels)}
    for r in rows:
        d = parse_iso(r["done_at"]).astimezone(TZ).date()
        if r["chat_id"] in counts and d in idx:
            counts[r["chat_id"]][idx[d]] += 1

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=130)
    fig.patch.set_facecolor("#0B0E12"); ax.set_facecolor("#0B0E12")
    x = range(days); w = 0.38
    colors = ["#3DD68C", "#5AA9E6"]
    for k, uid in enumerate(USERS_ORDER):
        ax.bar([i + (k - 0.5) * w for i in x], counts[uid], width=w,
               label=uname(uid), color=colors[k % 2])
    ax.set_xticks(list(x))
    ax.set_xticklabels([d.strftime("%d.%m") for d in labels], rotation=45, fontsize=8, color="#AEB7C4")
    ax.set_title("Выполнено по дням (14 дней)", color="#F3F6FA", fontsize=13)
    ax.tick_params(colors="#AEB7C4")
    for s in ax.spines.values():
        s.set_color("#2C3542")
    ax.grid(axis="y", color="#1b2230", linewidth=0.7)
    ax.legend(facecolor="#161A21", edgecolor="#2C3542", labelcolor="#E6EAF0")
    ax.yaxis.get_major_locator().set_params(integer=True)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig); buf.seek(0)
    return buf


def build_csv():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["id", "title", "status", "assignee", "creator", "priority", "deadline",
                "created", "done", "tags", "comment"])
    with db() as c:
        rows = c.execute("SELECT * FROM tasks ORDER BY created_at").fetchall()
    for t in rows:
        w.writerow([t["id"], t["title"], t["status"], uname(t["chat_id"]), uname(t["creator_id"]),
                    PRIO.get(t["priority"] or 2, PRIO[2])[1], t["deadline"] or "",
                    t["created_at"], t["done_at"] or "", t["tags"] or "", t["comment"] or ""])
    return io.BytesIO(out.getvalue().encode("utf-8-sig"))


async def show_charts(update, context):
    if not allowed(update): return
    remember(update)
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.UPLOAD_PHOTO)
    buf = build_chart_png()
    await update.message.reply_photo(buf, caption="📊 Выполнено по дням за 2 недели",
                                     reply_markup=MAIN_KB)


async def show_export(update, context):
    if not allowed(update): return
    remember(update)
    buf = build_csv()
    buf.name = "tasks.csv"
    await update.message.reply_document(buf, filename="tasks.csv",
                                        caption="⬇️ Экспорт всех задач (CSV)")


async def show_review(update, context):
    if not allowed(update): return
    remember(update)
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    txt = await build_review(update.effective_user.id)
    await update.message.reply_text("📈 <b>AI-ревью за неделю</b>\n\n" + html.escape(txt),
                                    parse_mode=ParseMode.HTML, reply_markup=MAIN_KB)


# ---------------------------------------------------------------- текстовый / голос / медиа ввод
async def on_text(update, context):
    if not allowed(update): return
    remember(update)
    await process_input(update, context, (update.message.text or "").strip())


async def on_voice(update, context):
    if not allowed(update): return
    remember(update)
    v = update.message.voice or update.message.audio
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    try:
        f = await context.bot.get_file(v.file_id)
        ba = await f.download_as_bytearray()
        b64 = base64.b64encode(bytes(ba)).decode()
        text = await gemini_transcribe(b64, getattr(v, "mime_type", None))
    except Exception as e:                                    # noqa: BLE001
        log.warning("voice handling failed: %s", e); text = ""
    if not text:
        return await update.message.reply_text("Не смог распознать голос — попробуй ещё раз или текстом.")
    await update.message.reply_text(f"🎤 Распознал: «{html.escape(text)}»", parse_mode=ParseMode.HTML)
    if not context.user_data.get("await"):                    # голос без контекста = новая задача
        context.user_data["await"] = ("title", None)
    await process_input(update, context, text)


async def on_media(update, context):
    """Фото/документ: прикрепляем к задаче, если ждём вложение."""
    if not allowed(update): return
    remember(update)
    uid = update.effective_user.id
    st = context.user_data.get("await")
    if not st or st[0] != "attach":
        # вне режима вложения: сохраняем присланный скрин на диск (для портфолио и т.п.)
        try:
            import os as _os
            _os.makedirs("/data/captures", exist_ok=True)
            if update.message.photo:
                fid, ext = update.message.photo[-1].file_id, "jpg"
            else:
                doc = update.message.document
                fid = doc.file_id
                ext = (doc.file_name.rsplit(".", 1)[-1] if doc.file_name and "." in doc.file_name else "bin")
            n = len([x for x in _os.listdir("/data/captures")]) + 1
            path = f"/data/captures/cap-{n:02d}-{update.message.message_id}.{ext}"
            f = await context.bot.get_file(fid)
            await f.download_to_drive(path)
            return await update.message.reply_text(f"📥 Сохранил скрин #{n} (для портфолио).",
                                                   reply_markup=MAIN_KB)
        except Exception as e:                               # noqa: BLE001
            log.warning("capture failed: %s", e)
            return await update.message.reply_text(
                "Не смог сохранить файл. Для вложения к задаче: открой её → 💬 Обсуждение → 📎 Вложить.",
                reply_markup=MAIN_KB)
    tid = st[1]; context.user_data.pop("await", None)
    if update.message.photo:
        file_id, ftype = update.message.photo[-1].file_id, "photo"
    else:
        file_id, ftype = update.message.document.file_id, "document"
    caption = (update.message.caption or "").strip()
    res = get_task(tid)
    if not res:
        return await update.message.reply_text("Задача не найдена.", reply_markup=MAIN_KB)
    t = res[0]
    add_comment(tid, uid, caption, file_id=file_id, file_type=ftype)
    await update.message.reply_text("📎 Вложение добавлено в обсуждение 👍", reply_markup=MAIN_KB)
    mate = t["creator_id"] if uid == t["chat_id"] else t["chat_id"]
    if mate and mate != uid:
        try:
            cap = f"📎 {uname(uid)} приложил к «{t['title']}»" + (f": {caption}" if caption else "")
            if ftype == "photo":
                await context.bot.send_photo(mate, file_id, caption=cap)
            else:
                await context.bot.send_document(mate, file_id, caption=cap)
        except Exception: pass                               # noqa: BLE001


async def process_input(update, context, text):
    uid = update.effective_user.id

    menu = {BTN_NEW: start_new, BTN_LIST: show_list, BTN_DASH: show_dashboard,
            BTN_DELEG: show_delegated, BTN_PROG: show_progress, BTN_PLAN: show_plan,
            BTN_HELP: cmd_help}
    if text in menu:
        return await menu[text](update, context)
    if text == BTN_SLAP:
        mate = other_user(uid)
        items = list_assigned(mate)
        items.sort(key=lambda x: not (x[0]["deadline"] and parse_iso(x[0]["deadline"]) < now_utc()))
        if not items:
            context.user_data["await"] = ("slap", None)
            return await update.message.reply_text("За что подзатыльник? Напиши причину. /cancel — отмена.")
        rows = []
        for t, _, _ in items[:6]:
            od = "🔴 " if (t["deadline"] and parse_iso(t["deadline"]) < now_utc()) else ""
            rows.append([InlineKeyboardButton(f"{od}за «{t['title'][:30]}»", callback_data=f"slpt|{t['id']}")])
        rows.append([InlineKeyboardButton("✏️ Своя причина", callback_data="slpc")])
        return await update.message.reply_text("За что подзатыльник напарнику?",
                                               reply_markup=InlineKeyboardMarkup(rows))

    st = context.user_data.get("await")
    if not st:
        return await update.message.reply_text("Не понял. Нажми кнопку ниже или /help.",
                                               reply_markup=MAIN_KB)
    kind, payload = st

    if kind == "title":
        context.user_data.pop("await", None)
        context.user_data["new"] = {"title": text[:500]}
        return await update.message.reply_text(
            "Кому задача?", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("👤 Себе", callback_data="na|self"),
                InlineKeyboardButton(f"🤝 {uname(other_user(uid))}", callback_data="na|friend")]]))

    if kind == "decline":
        reason = text.strip()
        if not reason:
            return await update.message.reply_text("Нужна причина отказа. Напиши коротко:")
        res = get_task(payload); context.user_data.pop("await", None)
        if not res:
            return await update.message.reply_text("Задача не найдена.", reply_markup=MAIN_KB)
        t = res[0]
        set_declined(payload, reason)
        await refresh_stored_card(context, payload)
        await update.message.reply_text("Поручение отклонено.", reply_markup=MAIN_KB)
        if t["creator_id"] and t["creator_id"] != uid:
            try:
                await context.bot.send_message(
                    t["creator_id"],
                    f"❌ {html.escape(uname(uid))} отклонил задачу: «{html.escape(t['title'])}»\n"
                    f"Причина: {html.escape(reason)}", parse_mode=ParseMode.HTML)
            except Exception: pass                           # noqa: BLE001
        return

    if kind == "clarify":
        question = text.strip()
        res = get_task(payload); context.user_data.pop("await", None)
        if not res:
            return await update.message.reply_text("Задача не найдена.", reply_markup=MAIN_KB)
        t = res[0]
        ok = False
        if t["creator_id"] and t["creator_id"] != uid:
            try:
                await context.bot.send_message(
                    t["creator_id"],
                    f"❓ {html.escape(uname(uid))} по задаче «{html.escape(t['title'])}» спрашивает:\n"
                    f"{html.escape(question)}", parse_mode=ParseMode.HTML)
                ok = True
            except Exception: pass                           # noqa: BLE001
        await update.message.reply_text("Вопрос отправил постановщику ✅" if ok else
                                        "Не смог отправить вопрос.", reply_markup=MAIN_KB)
        return

    if kind == "donecomment":
        comment = text.strip()
        if not comment:
            return await update.message.reply_text("Комментарий обязателен. Напиши, что сделано:")
        res = get_task(payload)
        context.user_data.pop("await", None)
        if not res:
            return await update.message.reply_text("Задача не найдена.", reply_markup=MAIN_KB)
        t = res[0]
        subs = res[1]
        set_comment(payload, comment)
        set_status(payload, "done")
        earned, total, streak = award_completion(uid, t)
        await refresh_stored_card(context, payload)
        streak_txt = f" · 🔥 стрик {streak} дн." if streak > 1 else ""
        await update.message.reply_text(
            f"✅ Задача закрыта! {random.choice(PRAISE)}\n⭐ +{earned} (всего {total}){streak_txt}",
            reply_markup=MAIN_KB)
        if t["creator_id"] and t["creator_id"] != uid:        # извещаем постановщика + приёмка
            try:
                await context.bot.send_message(
                    t["creator_id"],
                    f"✅ {html.escape(uname(uid))} выполнил задачу: «{html.escape(t['title'])}»\n"
                    f"💬 Комментарий: {html.escape(comment)}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("👍 Принято", callback_data=f"accdone|{payload}"),
                        InlineKeyboardButton("↩️ На доработку", callback_data=f"rework|{payload}")]]))
            except Exception as e:                            # noqa: BLE001
                log.warning("done-notify failed: %s", e)
        if t["recur"]:                                        # создаём следующее повторение
            ntid, ndl = clone_for_recur(t, subs)
            if ntid:
                when = f" на {ndl.astimezone(TZ).strftime('%d.%m %H:%M')}" if ndl else ""
                await update.message.reply_text(f"🔁 Создал следующий повтор{when}.")
                await send_card(context, t["chat_id"], ntid)
        return

    if kind == "edittitle":
        set_title(payload, text)
        context.user_data.pop("await", None)
        await refresh_stored_card(context, payload)
        return await update.message.reply_text("Название обновил 👍", reply_markup=MAIN_KB)

    if kind == "editdeadline":
        when = parse_when(text)
        if not when:
            return await update.message.reply_text("Не понял дату. Напр.: «18:00», «завтра 9:00», «25.12 14:30».")
        set_deadline(payload, when)
        context.user_data.pop("await", None)
        await refresh_stored_card(context, payload)
        return await update.message.reply_text(
            f"📅 Дедлайн: {when.astimezone(TZ).strftime('%d.%m %H:%M')}", reply_markup=MAIN_KB)

    if kind == "subtask":
        add_subtask(payload, text)
        context.user_data.pop("await", None)
        await refresh_stored_card(context, payload)
        return await update.message.reply_text("Добавил подзадачу 👍", reply_markup=MAIN_KB)

    if kind == "editsub":
        tid_, idx_ = payload
        edit_subtask(tid_, idx_, text)
        context.user_data.pop("await", None)
        await refresh_stored_card(context, tid_)
        return await update.message.reply_text("Подзадачу обновил 👍", reply_markup=MAIN_KB)

    if kind == "threadcomment":
        res = get_task(payload); context.user_data.pop("await", None)
        if not res:
            return await update.message.reply_text("Задача не найдена.", reply_markup=MAIN_KB)
        t = res[0]
        add_comment(payload, uid, text)
        mate = t["creator_id"] if uid == t["chat_id"] else t["chat_id"]
        if mate and mate != uid:
            try:
                await context.bot.send_message(
                    mate, f"💬 <b>{html.escape(uname(uid))}</b> по задаче «{html.escape(t['title'])}»:\n"
                    f"{html.escape(text)}", parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                        "➡️ Открыть", callback_data=f"thr|{payload}")]]))
            except Exception: pass                           # noqa: BLE001
        txt, kb = thread_view(payload)
        return await update.message.reply_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)

    if kind == "rework":
        res = get_task(payload); context.user_data.pop("await", None)
        if not res:
            return await update.message.reply_text("Задача не найдена.", reply_markup=MAIN_KB)
        t = res[0]
        set_status(payload, "open")
        await refresh_stored_card(context, payload)
        await update.message.reply_text("Вернул на доработку ↩️", reply_markup=MAIN_KB)
        if t["chat_id"] != uid:
            try:
                await context.bot.send_message(
                    t["chat_id"], f"↩️ {html.escape(uname(uid))} вернул на доработку: «{html.escape(t['title'])}»\n"
                    f"Что доработать: {html.escape(text)}", parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                        "➡️ Открыть", callback_data=f"open|{payload}")]]))
            except Exception: pass                           # noqa: BLE001
        return

    if kind == "edittags":
        context.user_data.pop("await", None)
        val = "" if text.strip() in ("-", "—") else merge_tags(
            [norm_tag(x) for x in re.split(r"[,\s]+", text)])
        set_tags(payload, val or None)
        await refresh_stored_card(context, payload)
        return await update.message.reply_text(
            ("Теги: " + " ".join(f"#{x}" for x in val.split(",")) if val else "Теги убраны."),
            reply_markup=MAIN_KB)

    if kind == "snooze_custom":
        when = parse_when(text)
        if not when:
            return await update.message.reply_text("Не понял дату. Напр.: «18:00», «завтра 9:00».")
        set_remind(payload, when)
        context.user_data.pop("await", None)
        await refresh_stored_card(context, payload)
        return await update.message.reply_text(
            f"⏰ Напомню {when.astimezone(TZ).strftime('%d.%m %H:%M')}", reply_markup=MAIN_KB)

    if kind == "slap":
        context.user_data.pop("await", None)
        try:
            await context.bot.send_message(other_user(uid), f"👊 Вам дали подзатыльник за {text.strip()}")
            await update.message.reply_text("Подзатыльник доставлен 👊", reply_markup=MAIN_KB)
        except Exception as e:                               # noqa: BLE001
            log.warning("slap failed: %s", e)
            await update.message.reply_text(
                "Не смог доставить — напарник ещё не запускал бота (пусть нажмёт /start).",
                reply_markup=MAIN_KB)


# ---------------------------------------------------------------- финал создания
async def finalize_new(update, context):
    uid = update.effective_user.id
    nd = context.user_data.get("new")
    if not nd or "assignee" not in nd:
        return await update.message.reply_text("Сессия истекла, начни заново: 📝 Новая задача.",
                                               reply_markup=MAIN_KB)
    raw = nd["title"]; assignee = nd["assignee"]
    context.user_data.pop("new", None)
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    plan = await gemini_plan(raw)                       # title + priority + deadline + подзадачи
    title = plan["title"] or raw[:300]
    status = "open" if assignee == uid else "pending"
    tid = create_task(assignee, uid, title, plan, plan["deadline_iso"],
                      priority=plan["priority"], status=status)

    if assignee == uid:
        await send_card(context, uid, tid)
    else:
        try:
            await send_card(context, assignee, tid,
                            prefix=f"📥 <b>{html.escape(uname(uid))}</b> предлагает тебе задачу — "
                                   "прими, уточни или отклони:")
            await update.message.reply_text(
                f"📤 Отправил на согласование: {html.escape(uname(assignee))} — «{html.escape(title)}».",
                parse_mode=ParseMode.HTML, reply_markup=MAIN_KB)
        except Exception as e:                               # noqa: BLE001
            log.warning("assign notify failed: %s", e)
            await update.message.reply_text(
                "Задачу создал, но напарник ещё не запускал бота — он получит её, когда нажмёт /start "
                "у @Assistantfreelance_bot.", reply_markup=MAIN_KB)


# ---------------------------------------------------------------- парсер дат
def parse_when(text):
    t = text.lower().strip().replace("сегодня", "").strip()
    base = dt.datetime.now(TZ); add = 0
    if t.startswith("завтра"): add = 1; t = t[len("завтра"):].strip()
    elif t.startswith("послезавтра"): add = 2; t = t[len("послезавтра"):].strip()
    md = re.search(r"(\d{1,2})[.\-/](\d{1,2})(?:[.\-/](\d{2,4}))?", t)
    if md: t = t[:md.start()] + t[md.end():]
    mt = re.search(r"(\d{1,2}):(\d{2})", t)
    if not mt and not md:
        return None
    hh, mm = (int(mt.group(1)), int(mt.group(2))) if mt else (9, 0)
    if md:
        day, mon = int(md.group(1)), int(md.group(2))
        year = int(md.group(3)) if md.group(3) else base.year
        if year < 100: year += 2000
        try: cand = dt.datetime(year, mon, day, hh, mm, tzinfo=TZ)
        except ValueError: return None
    else:
        cand = base.replace(hour=hh, minute=mm, second=0, microsecond=0) + dt.timedelta(days=add)
        if add == 0 and cand <= base: cand += dt.timedelta(days=1)
    return cand.astimezone(dt.timezone.utc)


def preset_at(days, hour):
    c = (dt.datetime.now(TZ) + dt.timedelta(days=days)).replace(hour=hour, minute=0, second=0, microsecond=0)
    return c.astimezone(dt.timezone.utc)


# ---------------------------------------------------------------- меню дедлайна/отложить
def deadline_menu(tid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Сегодня 18:00", callback_data=f"dls|{tid}|today"),
         InlineKeyboardButton("Завтра 18:00", callback_data=f"dls|{tid}|tom")],
        [InlineKeyboardButton("Через 3 дня", callback_data=f"dls|{tid}|3d"),
         InlineKeyboardButton("✏️ Своя дата", callback_data=f"dls|{tid}|custom")],
        [InlineKeyboardButton("✖️ Убрать дедлайн", callback_data=f"dls|{tid}|none"),
         InlineKeyboardButton("⬅️ Назад", callback_data=f"open|{tid}")]])


def priority_menu(tid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔴 Высокий", callback_data=f"prs|{tid}|1"),
         InlineKeyboardButton("🟡 Средний", callback_data=f"prs|{tid}|2"),
         InlineKeyboardButton("⚪ Низкий", callback_data=f"prs|{tid}|3")],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"open|{tid}")]])


def snooze_menu(tid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("через 1 ч", callback_data=f"sn|{tid}|1h"),
         InlineKeyboardButton("через 3 ч", callback_data=f"sn|{tid}|3h")],
        [InlineKeyboardButton("сегодня 18:00", callback_data=f"sn|{tid}|eve"),
         InlineKeyboardButton("завтра 9:00", callback_data=f"sn|{tid}|morn")],
        [InlineKeyboardButton("✏️ Своя дата", callback_data=f"sn|{tid}|custom"),
         InlineKeyboardButton("⬅️ Назад", callback_data=f"open|{tid}")]])


def snooze_time(code):
    base = dt.datetime.now(TZ)
    if code == "1h": return (base + dt.timedelta(hours=1)).astimezone(dt.timezone.utc)
    if code == "3h": return (base + dt.timedelta(hours=3)).astimezone(dt.timezone.utc)
    if code == "eve":
        c = base.replace(hour=18, minute=0, second=0, microsecond=0)
        if c <= base: c += dt.timedelta(days=1)
        return c.astimezone(dt.timezone.utc)
    if code == "morn": return preset_at(1, 9)
    return None


def deadline_code(code):
    if code == "today": return preset_at(0, 18)
    if code == "tom":   return preset_at(1, 18)
    if code == "3d":    return preset_at(3, 18)
    return None


# ---------------------------------------------------------------- callbacks
async def on_callback(update, context):
    q = update.callback_query
    if not allowed(update):
        return await q.answer("Приватный бот.", show_alert=True)
    remember(update)
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    parts = (q.data or "").split("|")
    cmd = parts[0]

    try:
        # --- дашборд (общий обзор; без tid)
        if cmd == "dash":
            await q.answer()
            text, kb = render_dash_home() if parts[1] == "home" else render_dash_done(parts[1])
            try:
                await q.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML,
                                          disable_web_page_preview=True)
            except Exception: pass                           # noqa: BLE001
            return

        # --- AI: ревью недели / план дня (без tid)
        if cmd == "review":
            await q.answer("Готовлю ревью…")
            await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
            txt = await build_review(uid)
            await context.bot.send_message(chat_id, "📈 <b>AI-ревью за неделю</b>\n\n" + html.escape(txt),
                                           parse_mode=ParseMode.HTML)
            return
        if cmd == "plan":
            await q.answer("Готовлю план…")
            await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
            txt = await build_plan(uid)
            await context.bot.send_message(chat_id, "🌅 <b>План на день</b>\n\n" + html.escape(txt),
                                           parse_mode=ParseMode.HTML)
            return
        if cmd == "charts":
            await q.answer("Рисую…")
            await context.bot.send_chat_action(chat_id, ChatAction.UPLOAD_PHOTO)
            await context.bot.send_photo(chat_id, build_chart_png(),
                                         caption="📊 Выполнено по дням за 2 недели")
            return
        if cmd == "export":
            await q.answer("Готовлю CSV…")
            buf = build_csv(); buf.name = "tasks.csv"
            await context.bot.send_document(chat_id, buf, filename="tasks.csv",
                                            caption="⬇️ Экспорт всех задач")
            return
        if cmd == "slpc":                                    # подзатыльник: своя причина
            context.user_data["await"] = ("slap", None)
            await q.answer()
            await q.message.edit_text("За что подзатыльник? Напиши причину:")
            return
        # подзатыльник с поводом из конкретной задачи напарника
        if cmd == "slpt":
            tr = get_task(int(parts[1]))
            if not tr:
                return await q.answer("Задача не найдена.", show_alert=True)
            await q.answer("👊")
            try:
                await context.bot.send_message(
                    tr[0]["chat_id"],
                    f"👊 Вам дали подзатыльник за задачу «{html.escape(tr[0]['title'])}»",
                    parse_mode=ParseMode.HTML)
                await q.message.edit_text("Подзатыльник доставлен 👊")
            except Exception:                                # noqa: BLE001
                await q.message.edit_text("Не доставил — напарник ещё не запускал бота.")
            return

        # --- показать вложение по id комментария (без tid задачи)
        if cmd == "att":
            cm = get_comment(int(parts[1]))
            if not cm or not cm["file_id"]:
                return await q.answer("Вложение не найдено.", show_alert=True)
            tr = get_task(cm["task_id"])
            if not tr or not can_act(uid, tr[0]):
                return await q.answer("Нет доступа.", show_alert=True)
            await q.answer("Отправляю…")
            cap = cm["text"] or None
            try:
                if cm["file_type"] == "photo":
                    await context.bot.send_photo(chat_id, cm["file_id"], caption=cap)
                else:
                    await context.bot.send_document(chat_id, cm["file_id"], caption=cap)
            except Exception: pass                           # noqa: BLE001
            return

        # --- фильтр «Мои задачи» по тегу (без tid)
        if cmd == "flt":
            await q.answer()
            items = list_assigned(uid)
            tag = parts[1]
            if tag == "*":
                txt, kb = f"<b>Мои задачи: {len(items)}</b>", _filter_kb(items)
            else:
                f = [(t, n, d) for (t, n, d) in items if tag in (t["tags"] or "").split(",")]
                txt, kb = f"<b>#{html.escape(tag)}: {len(f)}</b>", _filter_kb(f, tag=tag)
            try:
                await q.message.edit_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
            except Exception: pass                           # noqa: BLE001
            return

        # --- создание новой задачи: выбор исполнителя → сразу разбор Gemini
        if cmd == "na":
            nd = context.user_data.get("new")
            if not nd:
                return await q.answer("Сессия истекла, начни заново.", show_alert=True)
            nd["assignee"] = uid if parts[1] == "self" else other_user(uid)
            await q.answer("Разбираю…")
            try: await q.message.delete()
            except Exception: pass                           # noqa: BLE001
            return await finalize_new(update, context)

        # --- остальное: операции над задачей tid
        tid = int(parts[1])
        res = get_task(tid)
        if not res:
            return await q.answer("Задача не найдена.", show_alert=True)
        t = res[0]
        if not can_act(uid, t):
            return await q.answer("Это не твоя задача.", show_alert=True)

        if cmd == "open":
            await q.answer(); await send_card(context, chat_id, tid, edit=q.message)

        elif cmd == "tg":
            toggle_subtask(tid, int(parts[2])); await q.answer("Отметил")
            await send_card(context, chat_id, tid, edit=q.message)

        elif cmd == "done":
            context.user_data["await"] = ("donecomment", tid)
            await q.answer()
            await context.bot.send_message(
                chat_id, "✍️ Оставь комментарий к выполнению — что именно сделано "
                "(обязательно). /cancel — отмена.")

        elif cmd == "reopen":
            set_status(tid, "open"); await q.answer("В работе")
            await send_card(context, chat_id, tid, edit=q.message)

        elif cmd == "del":
            await q.answer()
            await q.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🗑 Да, удалить", callback_data=f"delok|{tid}"),
                InlineKeyboardButton("Отмена", callback_data=f"open|{tid}")]]))

        elif cmd == "delok":
            delete_task(tid); await q.answer("Удалено")
            await q.message.edit_text("🗑 Задача удалена.")

        elif cmd == "edt":
            context.user_data["await"] = ("edittitle", tid); await q.answer()
            await context.bot.send_message(chat_id, "Новое название одним сообщением:")

        elif cmd == "dl":
            await q.answer(); await q.message.edit_reply_markup(reply_markup=deadline_menu(tid))

        elif cmd == "dls":
            code = parts[2]
            if code == "custom":
                context.user_data["await"] = ("editdeadline", tid); await q.answer()
                return await context.bot.send_message(chat_id, "Когда дедлайн? Напр.: «завтра 18:00».")
            set_deadline(tid, None if code == "none" else deadline_code(code))
            await q.answer("Дедлайн обновлён")
            await send_card(context, chat_id, tid, edit=q.message)

        elif cmd == "snz":
            await q.answer(); await q.message.edit_reply_markup(reply_markup=snooze_menu(tid))

        elif cmd == "sn":
            code = parts[2]
            if code == "custom":
                context.user_data["await"] = ("snooze_custom", tid); await q.answer()
                return await context.bot.send_message(chat_id, "Когда напомнить? Напр.: «18:00», «завтра 9:00».")
            when = snooze_time(code); set_remind(tid, when)
            await q.answer(f"Напомню {when.astimezone(TZ).strftime('%d.%m %H:%M')}")
            await send_card(context, chat_id, tid, edit=q.message)

        elif cmd == "add":
            context.user_data["await"] = ("subtask", tid); await q.answer()
            await context.bot.send_message(chat_id, "Текст новой подзадачи:")

        elif cmd == "subs":                                   # меню управления подзадачами
            await q.answer()
            txt, kb = subs_view(tid)
            await q.message.edit_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)

        elif cmd == "se":                                     # править подзадачу
            context.user_data["await"] = ("editsub", (tid, int(parts[2]))); await q.answer()
            await context.bot.send_message(chat_id, f"Новый текст подзадачи №{int(parts[2])+1}:")

        elif cmd == "sd":                                     # удалить подзадачу
            delete_subtask(tid, int(parts[2])); await q.answer("Удалил")
            txt, kb = subs_view(tid)
            await q.message.edit_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML)
            await refresh_stored_card(context, tid)

        elif cmd == "rec":                                    # меню повтора
            await q.answer(); await q.message.edit_reply_markup(reply_markup=recur_menu(tid))

        elif cmd == "rs":
            set_recur(tid, None if parts[2] == "none" else parts[2])
            await q.answer("Повтор обновлён")
            await send_card(context, chat_id, tid, edit=q.message)

        elif cmd == "tag":                                    # править теги
            context.user_data["await"] = ("edittags", tid); await q.answer()
            cur = t["tags"] or "—"
            await context.bot.send_message(
                chat_id, f"Текущие теги: {cur}\nПришли теги через запятую/пробел (или «-» чтобы убрать):")

        elif cmd == "asg":                                    # переназначить
            await q.answer(); await q.message.edit_reply_markup(reply_markup=assign_menu(tid, uid))

        elif cmd == "as":
            new_assignee = uid if parts[2] == "self" else other_user(uid)
            if new_assignee == t["chat_id"]:
                return await q.answer("Уже на нём.", show_alert=True)
            status = "open" if new_assignee == uid else "pending"
            set_assignee(tid, new_assignee, status)
            await q.answer("Переназначено")
            if new_assignee == uid:
                await send_card(context, chat_id, tid, edit=q.message)
            else:
                try: await q.message.edit_text(f"👤 Переназначено: {html.escape(uname(new_assignee))} "
                                               "(ждёт принятия).", parse_mode=ParseMode.HTML)
                except Exception: pass                       # noqa: BLE001
                try:
                    await send_card(context, new_assignee, tid,
                                    prefix=f"📥 <b>{html.escape(uname(uid))}</b> передал тебе задачу — "
                                           "прими, уточни или отклони:")
                except Exception:                            # noqa: BLE001
                    await context.bot.send_message(
                        chat_id, "Передал, но напарник ещё не запускал бота — получит после /start.")

        elif cmd == "re":
            await q.answer("Переразбиваю…")
            await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
            bd = await gemini_breakdown(t["title"])
            if bd.get("subtasks"):
                replace_subtasks(tid, bd); await send_card(context, chat_id, tid, edit=q.message)
            else:
                await context.bot.send_message(chat_id, "AI сейчас недоступен, попробуй позже.")

        elif cmd == "prio":
            await q.answer(); await q.message.edit_reply_markup(reply_markup=priority_menu(tid))

        elif cmd == "prs":
            set_priority(tid, int(parts[2])); await q.answer("Важность обновлена")
            await send_card(context, chat_id, tid, edit=q.message)

        elif cmd == "acc":                                    # принять поручение
            if uid != t["chat_id"]:
                return await q.answer("Принять может только исполнитель.", show_alert=True)
            set_status(tid, "open"); await q.answer("Принято ✅")
            await send_card(context, chat_id, tid, edit=q.message)
            if t["creator_id"] and t["creator_id"] != uid:
                try:
                    await context.bot.send_message(
                        t["creator_id"],
                        f"✅ {html.escape(uname(uid))} принял задачу: «{html.escape(t['title'])}»",
                        parse_mode=ParseMode.HTML)
                except Exception: pass                       # noqa: BLE001

        elif cmd == "dec":                                    # отклонить (с причиной)
            if uid != t["chat_id"]:
                return await q.answer("Отклонить может только исполнитель.", show_alert=True)
            context.user_data["await"] = ("decline", tid); await q.answer()
            await context.bot.send_message(chat_id, "Причина отказа одним сообщением:")

        elif cmd == "clr":                                    # уточнить у постановщика
            if uid != t["chat_id"]:
                return await q.answer("Уточняет исполнитель.", show_alert=True)
            context.user_data["await"] = ("clarify", tid); await q.answer()
            await context.bot.send_message(chat_id, "Что уточнить у постановщика? Напиши вопрос:")

        elif cmd == "thr":                                    # тред-обсуждение
            await q.answer()
            txt, kb = thread_view(tid)
            await q.message.edit_text(txt, reply_markup=kb, parse_mode=ParseMode.HTML,
                                      disable_web_page_preview=True)

        elif cmd == "tc":                                     # написать в тред
            context.user_data["await"] = ("threadcomment", tid); await q.answer()
            await context.bot.send_message(chat_id, "Сообщение в обсуждение:")

        elif cmd == "atc":                                    # прикрепить файл
            context.user_data["await"] = ("attach", tid); await q.answer()
            await context.bot.send_message(chat_id, "Пришли фото или документ (можно с подписью):")

        elif cmd == "ping":                                   # пинг другой стороне
            mate = t["creator_id"] if uid == t["chat_id"] else t["chat_id"]
            if not mate or mate == uid:
                return await q.answer("Некого пинговать.", show_alert=True)
            await q.answer("Пинганул 👉")
            try:
                await context.bot.send_message(
                    mate, f"👉 {html.escape(uname(uid))} пингует по задаче: «{html.escape(t['title'])}»",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                        "➡️ Открыть", callback_data=f"open|{tid}")]]), parse_mode=ParseMode.HTML)
            except Exception:                                # noqa: BLE001
                await context.bot.send_message(chat_id, "Не доставил — напарник ещё не запускал бота.")

        elif cmd == "accdone":                                # постановщик: принять работу
            if uid != t["creator_id"]:
                return await q.answer("Принимает постановщик.", show_alert=True)
            await q.answer("Принято 👍")
            try: await q.edit_message_reply_markup(reply_markup=None)
            except Exception: pass                           # noqa: BLE001
            if t["chat_id"] != uid:
                try:
                    await context.bot.send_message(
                        t["chat_id"], f"👍 {html.escape(uname(uid))} принял работу: «{html.escape(t['title'])}»",
                        parse_mode=ParseMode.HTML)
                except Exception: pass                       # noqa: BLE001

        elif cmd == "rework":                                 # постановщик: на доработку
            if uid != t["creator_id"]:
                return await q.answer("Возвращает постановщик.", show_alert=True)
            context.user_data["await"] = ("rework", tid); await q.answer()
            await context.bot.send_message(chat_id, "Что доработать? Напиши комментарий:")
        else:
            await q.answer()
    except Exception as e:                                    # noqa: BLE001
        log.exception("callback error: %s", e)
        try: await q.answer("Ошибка, попробуй ещё раз.", show_alert=True)
        except Exception: pass                               # noqa: BLE001


# ---------------------------------------------------------------- jobs
async def job_review(context):
    for uid in ALLOWED:
        try:
            txt = await build_review(uid)
            await context.bot.send_message(uid, "📈 <b>AI-ревью за неделю</b>\n\n" + html.escape(txt),
                                           parse_mode=ParseMode.HTML)
        except Exception as e:                               # noqa: BLE001
            log.info("review to %s skipped: %s", uid, e)


async def job_digest(context):
    for uid in ALLOWED:
        items = list_assigned(uid)
        if not items:
            continue
        lines = [f"☀️ <b>Доброе утро!</b> Задач на тебе: {len(items)}", ""]
        rows = []
        for t, n, d in items[:15]:
            prog = f" ({d}/{n})" if n else ""
            pe = PRIO.get(t["priority"] or 2, PRIO[2])[0]
            dl = ""
            if t["deadline"]:
                od = parse_iso(t["deadline"]) < now_utc()
                dl = f" — {'🔴 просрочено' if od else '📅 ' + fmt_local(t['deadline'])}"
            frm = f" (от {uname(t['creator_id'])})" if t["creator_id"] != uid else ""
            pend = " · 🆕 принять" if t["status"] == "pending" else ""
            lines.append(f"{pe} {html.escape(t['title'][:55])}{prog}{dl}{frm}{pend}")
            label = (t["title"][:28] + "…") if len(t["title"]) > 29 else t["title"]
            rows.append([InlineKeyboardButton(f"➡️ {label}", callback_data=f"open|{t['id']}")])
        rows.append([InlineKeyboardButton("🌅 План дня от AI", callback_data="plan")])
        try:
            await context.bot.send_message(uid, "\n".join(lines), parse_mode=ParseMode.HTML,
                                           reply_markup=InlineKeyboardMarkup(rows),
                                           disable_web_page_preview=True)
        except Exception as e:                               # noqa: BLE001
            log.info("digest to %s skipped: %s", uid, e)


async def _notify_creator(context, t, text):
    if t["creator_id"] and t["creator_id"] != t["chat_id"]:
        try:
            await context.bot.send_message(t["creator_id"], text, parse_mode=ParseMode.HTML)
        except Exception: pass                               # noqa: BLE001


async def job_reminders(context):
    now = now_utc()
    for uid in ALLOWED:
        # 1) личные «отложить»
        for r in due_personal(uid):
            set_remind(r["id"], None)
            await send_reminder(context, uid, r["id"], "⏰ <b>Напоминание:</b>")
        # 2) дедлайны: пред-день / пред-час / просрочка / эскалация
        for t in deadline_jobs(uid):
            tid = t["id"]; dl = parse_iso(t["deadline"]); title = html.escape(t["title"])
            if now < dl:
                if now >= dl - dt.timedelta(hours=1) and not t["pre_hour_notified"]:
                    set_flag(tid, "pre_hour_notified", 1)
                    await send_reminder(context, uid, tid, "⏳ <b>Через час дедлайн</b>")
                elif now >= dl - dt.timedelta(days=1) and not t["pre_day_notified"]:
                    set_flag(tid, "pre_day_notified", 1)
                    await send_reminder(context, uid, tid, "📅 <b>Завтра дедлайн</b>")
            else:  # просрочено
                if not t["deadline_notified"]:
                    set_flag(tid, "deadline_notified", 1)
                    await send_reminder(context, uid, tid, "🔴 <b>Дедлайн наступил!</b>")
                    await _notify_creator(context, t,
                        f"🔴 Дедлайн просрочен у {html.escape(uname(uid))}: «{title}»")
                else:  # эскалация раз в сутки + авто-подзатыльник
                    base = parse_iso(t["last_escalate"]) if t["last_escalate"] else dl
                    if (now - base).total_seconds() >= 86400:
                        set_last_escalate(tid, iso(now))
                        days = (now - dl).days
                        try:
                            await context.bot.send_message(
                                uid, f"👊 Подзатыльник за просрочку ({days} дн.): «{title}»\n"
                                "Закрой или перенеси дедлайн.", parse_mode=ParseMode.HTML,
                                reply_markup=reminder_kb(tid))
                        except Exception: pass               # noqa: BLE001
                        await _notify_creator(context, t,
                            f"⏳ {html.escape(uname(uid))} тянет просроченную задачу ({days} дн.): «{title}»")


# ---------------------------------------------------------------- init
async def post_init(app):
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_my_commands([
        BotCommand("new", "Новая задача"),
        BotCommand("tasks", "Мои задачи"),
        BotCommand("dashboard", "Дашборд (обзор)"),
        BotCommand("delegated", "Поручено мной"),
        BotCommand("progress", "Прогресс"),
        BotCommand("plan", "AI-план дня"),
        BotCommand("review", "AI-ревью недели"),
        BotCommand("help", "Помощь"),
        BotCommand("cancel", "Отменить ввод"),
    ])
    app.job_queue.run_daily(job_digest, time=dt.time(DIGEST_H, DIGEST_M, tzinfo=TZ), name="digest")
    app.job_queue.run_repeating(job_reminders, interval=900, first=30, name="reminders")
    # еженедельное AI-ревью — воскресенье 19:00 Киев
    app.job_queue.run_daily(job_review, time=dt.time(19, 0, tzinfo=TZ), days=(6,), name="review")
    log.info("assistant ready; users=%s, model=%s, tz=%s", ALLOWED, GEM_MODEL, TZ)


def main():
    init_db()
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("new", start_new))
    app.add_handler(CommandHandler("tasks", show_list))
    app.add_handler(CommandHandler("dashboard", show_dashboard))
    app.add_handler(CommandHandler("delegated", show_delegated))
    app.add_handler(CommandHandler("progress", show_progress))
    app.add_handler(CommandHandler("plan", show_plan))
    app.add_handler(CommandHandler("review", show_review))
    app.add_handler(CommandHandler("charts", show_charts))
    app.add_handler(CommandHandler("export", show_export))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, on_voice))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, on_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
