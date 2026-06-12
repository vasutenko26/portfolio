import { test, after } from 'node:test';
import assert from 'node:assert';
import { app } from './server.js';

const server = app.listen(0);
const base = () => `http://127.0.0.1:${server.address().port}`;
after(() => server.close());

test('/health returns ok', async () => {
  const r = await fetch(base() + '/health');
  assert.equal(r.status, 200);
  const j = await r.json();
  assert.equal(j.status, 'ok');
  assert.ok(typeof j.uptime_s === 'number');
});

test('/metrics exposes Prometheus format', async () => {
  const r = await fetch(base() + '/metrics');
  assert.equal(r.status, 200);
  const txt = await r.text();
  assert.match(txt, /app_up 1/);
  assert.match(txt, /app_http_requests_total/);
});

test('/ returns status page', async () => {
  const r = await fetch(base() + '/');
  assert.equal(r.status, 200);
  assert.match(await r.text(), /operational/);
});
