# Case — Public status page & uptime monitoring

> Subheading proof: **5/5 services green · public TLS status page live · down→up alert delivered to Telegram, verified · TLS expiry watched**

## 01 — Brief

The portfolio's hero copy promises a "green dashboard" and "99.98% uptime." That
claim needed to be a live, public link a visitor (or a client) can open and check —
not a screenshot. The brief: stand up a public status page for the self-hosted stack,
monitor every public service end-to-end, alert on outages through the existing
on-call channel, and expose it under TLS on a `status.` subdomain.

## 02 — What I did

- Deployed **Uptime Kuma** in Docker, isolated in its own compose project, attached
  to the shared proxy network. No host ports — reachable only through Caddy with
  automatic TLS on `status.davidvasutenko.fun`.
- Wrote an **idempotent provisioner** (Python over Kuma's socket.io API, config in
  `monitors.yml`) so the whole setup — Telegram notification, monitors, public status
  page — is reproducible from code instead of clicked together in a UI.
- Configured **HTTP + TLS-certificate-expiry** monitors on every public endpoint:
  portfolio site, n8n, Grafana, the CI/CD app, and the status page itself. Each probes
  the **public** URL, so green proves the full path: DNS → Caddy → certificate → app.
- Wired **down/up alerts into the «Фриланс сервер» Telegram bot** — the channel where
  all infra technical alerts (backups, server reports) already land.
- Built a **reproducible alert drill** on a disposable target (`traefik/whoami`) so the
  alert path can be proven on demand without touching real services.

## 03 — Outcome

- Public status page **live** at `https://status.davidvasutenko.fun` behind Caddy with
  a valid Let's Encrypt cert, per-service status, 24h/7d/30d uptime and an incident
  timeline — the literal "green dashboard."
- **5/5 services up**, all monitored end-to-end over their public HTTPS URLs.
- Alert path **verified with a real drill**: stopping the test target delivered a
  `🔴 Down` (`connect EHOSTUNREACH`) message to the «Фриланс сервер» bot and opened an
  incident; restarting delivered a recovery `✅ Up` — three state changes, each
  delivered to the right bot.
- Certificate-expiry monitoring on every HTTPS endpoint — a routine, avoidable outage
  now caught weeks ahead.
- Everything reproducible from `docker compose up -d` + one provision command;
  secrets via env, container with `no-new-privileges`, no public ports.

---

## Screenshots to capture (live service, for the gallery)

1. **Public status page** — all services green with the uptime bars (the hero shot).
2. **Per-service detail** — a monitor page showing the response-time graph and the
   **TLS certificate "valid for N days"** badge.
3. **Telegram alert** — the `🔴 Down` + recovery `✅ Up` messages from the drill in the
   «Фриланс сервер» bot (proof the on-call wiring is real).
4. **Incident timeline** — the status page showing the recorded incident from the drill.
5. **Uptime windows** — the 24h / 7d / 30d toggle with the percentages.
6. **Dashboard / monitor list** — the admin view listing all monitors green, intervals
   and TLS checks visible (shows it's configured, not faked).

## Metrics / proofs for the subheading

- **Uptime:** real percentage straight off the page (e.g. "uptime 100% · 7d") — let it
  accrue a few days before pinning the headline number to match the site's "99.98%."
- **`down → alert in ~40s`** — measured drill latency (20s interval, 1 retry).
- **`TLS expiry watched`** — certificate days-remaining tracked on every endpoint.
- **`5 services, one on-call bot`** — scope + that alerts land in «Фриланс сервер».
