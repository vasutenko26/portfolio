#!/usr/bin/env python3
"""Собирает n8n-воркфлоу (JS-код корректно экранируется через json)."""
import json, os

ERR_WF = "autoErrHandler01"
OUT = os.path.dirname(os.path.abspath(__file__)) + "/automation"

def code_node(node_id, name, js, pos):
    return {"parameters": {"jsCode": js}, "id": node_id, "name": name,
            "type": "n8n-nodes-base.code", "typeVersion": 2, "position": pos}

def wf(wid, name, nodes, connections):
    return {"id": wid, "name": name, "nodes": nodes, "connections": connections,
            "settings": {"errorWorkflow": ERR_WF}, "active": False}

# ---------------- 1) Контактная форма → Telegram + CSV ----------------
contact_js = r"""
const req = $input.first().json;
const body = req.body || {};
const headers = req.headers || {};
const fs = require('fs');

// honeypot: скрытое поле company заполнено только ботами
if (body.company && String(body.company).trim() !== '') {
  return [{ json: { ok: true } }];
}

// rate limit: 3 заявки / 10 минут на IP
const ip = String(headers['x-forwarded-for'] || headers['x-real-ip'] || 'unknown').split(',')[0].trim();
const sd = $getWorkflowStaticData('global');
sd.hits = sd.hits || {};
const now = Date.now(), win = 10 * 60 * 1000, max = 3;
sd.hits[ip] = (sd.hits[ip] || []).filter(t => now - t < win);
if (sd.hits[ip].length >= max) {
  return [{ json: { ok: false, error: 'rate_limited' } }];
}

// валидация
const name = String(body.name || '').trim();
const email = String(body.email || '').trim();
const message = String(body.message || '').trim();
const lang = String(body.lang || 'en').trim().slice(0, 5);
const okEmail = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email);
if (!name || !okEmail || message.length < 2) {
  return [{ json: { ok: false, error: 'invalid' } }];
}
sd.hits[ip].push(now);

// 1) durable: пишем в CSV — заявка не теряется, даже если Telegram недоступен
const csv = '/files/leads.csv';
const esc = (s) => '"' + String(s).replace(/"/g, '""').replace(/\r?\n/g, ' ') + '"';
if (!fs.existsSync(csv)) fs.writeFileSync(csv, 'timestamp,ip,lang,name,email,message\n');
fs.appendFileSync(csv, [new Date().toISOString(), ip, lang, name, email, message].map(esc).join(',') + '\n');

// 2) Telegram
const token = $env.TELEGRAM_BOT_TOKEN, chat = $env.TELEGRAM_CHAT_ID;
const text = `\u{1F4E8} Новая заявка с сайта\n\n\u{1F464} ${name}\n✉️ ${email}\n\u{1F310} ${lang}\n\n${message}`;
try {
  await this.helpers.httpRequest({ method: 'POST', url: `https://api.telegram.org/bot${token}/sendMessage`, body: { chat_id: chat, text }, json: true });
} catch (e) {
  // не падаем молча: заявка уже в CSV, поднимаем ошибку -> error workflow шлёт алерт
  throw new Error('Telegram delivery failed: ' + e.message);
}
return [{ json: { ok: true } }];
"""

contact = wf("autoContactForm1", "01 Contact form -> Telegram + CSV", [
    {"parameters": {"httpMethod": "POST", "path": "contact", "responseMode": "lastNode",
                    "options": {"allowedOrigins": "https://davidvasutenko.fun"}},
     "id": "cf-webhook", "name": "Webhook", "type": "n8n-nodes-base.webhook",
     "typeVersion": 2, "position": [0, 0], "webhookId": "autoContactForm1"},
    code_node("cf-code", "Handle submission", contact_js, [240, 0]),
], {"Webhook": {"main": [[{"node": "Handle submission", "type": "main", "index": 0}]]}})

# ---------------- 2) Суточный отчёт по health сайта ----------------
health_js = r"""
const fs = require('fs');
const url = $env.SITE_HEALTH_URL || 'https://davidvasutenko.fun/';
const token = $env.TELEGRAM_BOT_TOKEN, chat = $env.TELEGRAM_CHAT_ID;

let status = 'DOWN', code = 0, ms = 0;
const t0 = Date.now();
try {
  const res = await this.helpers.httpRequest({ method: 'GET', url, returnFullResponse: true, timeout: 15000 });
  ms = Date.now() - t0;
  code = res.statusCode;
  status = (code >= 200 && code < 400) ? 'UP' : 'DEGRADED';
} catch (e) {
  ms = Date.now() - t0; status = 'DOWN'; code = 0;
}

// заявок за 24ч из CSV
let leads24 = 0;
try {
  const csv = '/files/leads.csv';
  if (fs.existsSync(csv)) {
    const lines = fs.readFileSync(csv, 'utf8').trim().split('\n').slice(1);
    const dayAgo = Date.now() - 24 * 60 * 60 * 1000;
    for (const ln of lines) {
      const m = ln.match(/^"([^"]+)"/);
      if (m && new Date(m[1]).getTime() >= dayAgo) leads24++;
    }
  }
} catch (e) {}

const icon = status === 'UP' ? '✅' : (status === 'DEGRADED' ? '⚠️' : '\u{1F534}');
const when = new Date().toLocaleString('uk-UA', { timeZone: 'Europe/Kyiv' });
const text = `\u{1F4CA} Суточный отчёт — davidvasutenko.fun\n\n${icon} Сайт: ${status} (HTTP ${code}, ${ms} ms)\n\u{1F4E8} Заявок за 24ч: ${leads24}\n\u{1F551} ${when}`;

await this.helpers.httpRequest({ method: 'POST', url: `https://api.telegram.org/bot${token}/sendMessage`, body: { chat_id: chat, text }, json: true });
return [{ json: { status, code, ms, leads24 } }];
"""

health = wf("autoHealthReport", "02 Daily health report -> Telegram", [
    {"parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": "0 9 * * *"}]}},
     "id": "hr-cron", "name": "Schedule 09:00 Kyiv", "type": "n8n-nodes-base.scheduleTrigger",
     "typeVersion": 1.2, "position": [0, 0]},
    code_node("hr-code", "Check & report", health_js, [240, 0]),
], {"Schedule 09:00 Kyiv": {"main": [[{"node": "Check & report", "type": "main", "index": 0}]]}})

# ---------------- 3) AI-intake (Gemini): классификация + черновик + эскалация ----------------
ai_js = r"""
const req = $input.first().json;
const body = req.body || {};
const token = $env.TELEGRAM_BOT_TOKEN, chat = $env.TELEGRAM_CHAT_ID;
const key = $env.GEMINI_API_KEY, model = $env.GEMINI_MODEL || 'gemini-2.5-flash';
const msg = String(body.message || body.text || '').trim();
if (!msg) return [{ json: { ok: false, error: 'empty' } }];

const prompt = `Ты — ассистент поддержки инженера инфраструктуры. Классифицируй входящее сообщение и подготовь короткий черновик ответа на языке сообщения.\nВерни СТРОГО JSON без markdown: {"category":"sales|support|spam|other","urgency":"low|medium|high","escalate":true|false,"draft":"текст черновика"}.\nСообщение: <<<${msg}>>>`;

let ai;
try {
  const res = await this.helpers.httpRequest({
    method: 'POST',
    url: `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${key}`,
    body: { contents: [{ parts: [{ text: prompt }] }], generationConfig: { temperature: 0.3, responseMimeType: 'application/json' } },
    json: true, timeout: 30000,
  });
  const txt = res.candidates[0].content.parts[0].text;
  ai = JSON.parse(txt);
} catch (e) {
  // внешний сервис не ответил -> поднимаем ошибку, error workflow шлёт алерт
  throw new Error('Gemini failed: ' + e.message);
}

const escalate = !!(ai.escalate || ai.urgency === 'high');
if (escalate) {
  const text = `\u{1F198} Эскалация (AI)\n\nКатегория: ${ai.category} | срочность: ${ai.urgency}\n\n✉️ ${msg}\n\n\u{1F4DD} Черновик: ${ai.draft}`;
  await this.helpers.httpRequest({ method: 'POST', url: `https://api.telegram.org/bot${token}/sendMessage`, body: { chat_id: chat, text }, json: true });
}
return [{ json: { ok: true, category: ai.category, urgency: ai.urgency, escalated: escalate, draft: ai.draft } }];
"""

ai = wf("autoAiIntake0001", "03 AI intake (Gemini) -> classify + escalate", [
    {"parameters": {"httpMethod": "POST", "path": "ai-intake", "responseMode": "lastNode",
                    "options": {"allowedOrigins": "*"}},
     "id": "ai-webhook", "name": "Webhook", "type": "n8n-nodes-base.webhook",
     "typeVersion": 2, "position": [0, 0], "webhookId": "autoAiIntake0001"},
    code_node("ai-code", "Classify & route", ai_js, [240, 0]),
], {"Webhook": {"main": [[{"node": "Classify & route", "type": "main", "index": 0}]]}})

os.makedirs(OUT, exist_ok=True)
for w in (contact, health, ai):
    fn = OUT + "/" + w["id"] + ".json"
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(w, f, ensure_ascii=False, indent=2)
    print("wrote", fn)
