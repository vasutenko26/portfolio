const chat = document.getElementById("chat");
const filesEl = document.getElementById("files");
const fileInput = document.getElementById("file");
const askForm = document.getElementById("ask");
const qInput = document.getElementById("q");
const sendBtn = document.getElementById("send");

function esc(s) {
  return s.replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function addMsg(cls, html) {
  const div = document.createElement("div");
  div.className = "msg " + cls;
  div.innerHTML = html;
  chat.appendChild(div);
  div.scrollIntoView({ behavior: "smooth", block: "end" });
  return div;
}

// Превращает [n] в кликабельные чипы, раскрывающие источник.
function renderAnswer(answer, sources) {
  const byN = {};
  sources.forEach(s => (byN[s.n] = s));
  const withCites = esc(answer).replace(/\[(\d+)\]/g, (m, n) =>
    byN[n] ? `<a class="cite" href="#src-${n}" title="${esc(byN[n].label)}">[${n}]</a>` : m
  );
  let html = `<div class="answer">${withCites}</div>`;
  if (sources.length) {
    html += `<div class="sources">`;
    sources.forEach(s => {
      const loc = esc(s.label);
      html += `<details class="src" id="src-${s.n}">
        <summary><span class="num">[${s.n}]</span>${loc}<span class="score">score ${s.score}</span></summary>
        <div class="snippet">${esc(s.snippet)}</div>
      </details>`;
    });
    html += `</div>`;
  }
  return html;
}

async function uploadFile(file) {
  const chip = document.createElement("span");
  chip.className = "chip";
  chip.textContent = `${file.name} — загрузка…`;
  filesEl.appendChild(chip);
  try {
    const fd = new FormData();
    fd.append("file", file);
    const r = await fetch("/api/ingest", { method: "POST", body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || r.status);
    chip.className = "chip ok";
    chip.textContent = `${file.name} · ${d.chunks} фрагм.`;
  } catch (e) {
    chip.className = "chip err";
    chip.textContent = `${file.name} · ошибка: ${e.message}`;
  }
}

fileInput.addEventListener("change", async () => {
  for (const f of fileInput.files) await uploadFile(f);
  fileInput.value = "";
});

askForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = qInput.value.trim();
  if (!q) return;
  addMsg("user", esc(q));
  qInput.value = "";
  sendBtn.disabled = true;
  const pending = addMsg("bot", `<span class="typing">думаю…</span>`);
  try {
    const r = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q }),
    });
    const d = await r.json();
    if (!r.ok) {
      pending.className = "msg bot error";
      pending.innerHTML = `Ошибка: ${esc(d.detail || String(r.status))}`;
    } else if (!d.found) {
      pending.className = "msg bot notfound";
      pending.innerHTML = esc(d.answer);
    } else {
      pending.className = "msg bot";
      pending.innerHTML = renderAnswer(d.answer, d.sources);
    }
  } catch (e) {
    pending.className = "msg bot error";
    pending.innerHTML = `Сеть/сервер недоступен: ${esc(e.message)}`;
  } finally {
    sendBtn.disabled = false;
    qInput.focus();
  }
});

// Показать активный провайдер LLM + уже загруженные документы.
(async () => {
  try {
    const h = await (await fetch("/healthz")).json();
    document.getElementById("provider").textContent = `LLM: ${h.provider} · ${h.model} · embeddings: self-hosted`;
  } catch {}
  try {
    const s = await (await fetch("/api/stats")).json();
    (s.files || []).forEach(f => {
      const chip = document.createElement("span");
      chip.className = "chip ok";
      chip.textContent = f;
      filesEl.appendChild(chip);
    });
  } catch {}
})();
