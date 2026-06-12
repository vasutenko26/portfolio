import express from 'express';
import client from 'prom-client';

const app = express();
app.disable('x-powered-by');

// ---- Prometheus метрики ----
const register = new client.Registry();
register.setDefaultLabels({ app: 'portfolio-app' });
client.collectDefaultMetrics({ register });

const httpRequests = new client.Counter({
  name: 'app_http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['route', 'status'],
  registers: [register],
});
const httpLatency = new client.Histogram({
  name: 'app_http_request_duration_seconds',
  help: 'HTTP request latency',
  labelNames: ['route'],
  buckets: [0.005, 0.01, 0.05, 0.1, 0.5, 1],
  registers: [register],
});
const up = new client.Gauge({ name: 'app_up', help: '1 if the service is up', registers: [register] });
up.set(1);

const START = Date.now();
const VERSION = process.env.APP_VERSION || 'dev';

app.use((req, res, next) => {
  const end = httpLatency.startTimer({ route: req.path });
  res.on('finish', () => {
    end();
    httpRequests.inc({ route: req.path, status: res.statusCode });
  });
  next();
});

app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    version: VERSION,
    uptime_s: Math.round((Date.now() - START) / 1000),
    ts: new Date().toISOString(),
  });
});

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

app.get('/', (req, res) => {
  res.type('html').send(`<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>portfolio-app · status</title>
<style>
  :root{--bg:#0E1116;--surface:#161A21;--line:#232A34;--text:#E6EAF0;--muted:#8B94A3;--accent:#3DD68C;--mono:ui-monospace,"JetBrains Mono",monospace}
  *{box-sizing:border-box}body{margin:0;font-family:var(--mono);background:var(--bg);color:var(--text);min-height:100vh;display:grid;place-items:center}
  .card{background:linear-gradient(180deg,var(--surface),#1B212B);border:1px solid var(--line);border-radius:14px;padding:2rem 2.4rem;min-width:320px;box-shadow:0 30px 70px -30px #000}
  .dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px var(--accent);margin-right:.5rem;animation:p 2.4s infinite}
  @keyframes p{0%{box-shadow:0 0 0 0 rgba(61,214,140,.5)}70%{box-shadow:0 0 0 8px rgba(61,214,140,0)}100%{box-shadow:0 0 0 0 rgba(61,214,140,0)}}
  h1{font-size:1.1rem;margin:0 0 1.2rem;font-weight:600}.row{display:flex;justify-content:space-between;gap:2rem;padding:.4rem 0;border-bottom:1px dashed var(--line);font-size:.85rem}
  .row:last-child{border:0}.k{color:var(--muted)}.v{color:var(--accent)}.ep{margin-top:1.2rem;font-size:.75rem;color:var(--muted)}.ep a{color:var(--text)}
</style></head>
<body><div class="card">
  <h1><span class="dot"></span>portfolio-app — operational</h1>
  <div class="row"><span class="k">version</span><span class="v" id="ver">…</span></div>
  <div class="row"><span class="k">uptime</span><span class="v" id="up">…</span></div>
  <div class="row"><span class="k">host time</span><span class="v" id="ts">…</span></div>
  <p class="ep">endpoints: <a href="/health">/health</a> · <a href="/metrics">/metrics</a></p>
</div>
<script>
  fetch('/health').then(r=>r.json()).then(d=>{
    document.getElementById('ver').textContent=d.version;
    document.getElementById('up').textContent=d.uptime_s+'s';
    document.getElementById('ts').textContent=new Date(d.ts).toLocaleTimeString();
  }).catch(()=>{});
</script>
</body></html>`);
});

const port = Number(process.env.PORT) || 3000;
if (process.env.NODE_ENV !== 'test') {
  app.listen(port, () => console.log(`portfolio-app listening on :${port} (v${VERSION})`));
}

export { app };
