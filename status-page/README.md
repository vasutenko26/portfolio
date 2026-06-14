# Status page & uptime monitoring — `status.davidvasutenko.fun`

Public status page for the self-hosted stack, built on **Uptime Kuma** in Docker.
HTTP + TLS-expiry checks on every public service, a public page with incident
history and 24h/7d/30d uptime, and **down/up alerts to the «Фриланс сервер» Telegram
bot** — the same bot the rest of the infra plumbing (backups, server reports) uses for
technical alerts. Exposed only through Caddy with automatic TLS on the `status.`
subdomain.

This directly backs the site's hero copy ("green dashboard", "uptime 99.98%"): the
claim is now a live, public link, not a screenshot.

## Why Uptime Kuma (vs blackbox_exporter + a static page)

Both were on the table. Kuma wins here because it ships the whole package — HTTP
**and** certificate-expiry probes, a hosted public status page with incident
timeline and per-window uptime, and native Telegram notifications — in one small
container, with no extra page to build or host. A `blackbox_exporter` + static-site
build would be more moving parts for the same outcome. Prometheus/Grafana already
cover deep metrics in the `/observability` case; this case is specifically the
**customer-facing uptime** angle.

## What this demonstrates

> **Monitoring & uptime as a service.** Sells: DevOps / monitoring — "I watch your
> services and tell you (and your customers) when something breaks, before they ask."

- Black-box monitoring of real public endpoints (DNS → Caddy → TLS → app), not just
  localhost.
- **TLS certificate expiry** tracking — a common, embarrassing outage prevented.
- A clean public status page clients can subscribe to, with honest incident history.
- Alerting wired into existing on-call (the «Фриланс сервер» bot, where all infra
  technical alerts land).
- Least-privilege deploy: no host ports, `no-new-privileges`, secrets via env,
  reverse-proxy-only exposure.

## Layout

```
docker-compose.yml      uptime-kuma (no host ports) + provision (profile) + drill-target (profile)
.env.example            all variables; real secrets never committed
provision/
  provision.py          idempotent provisioning via Kuma's socket.io API
  monitors.yml          declarative monitors + public-status-page definition
  Dockerfile            python:3.12-slim, non-root (uid 10001)
  requirements.txt      uptime-kuma-api, PyYAML
```

The Caddy block lives in the repo-root `Caddyfile` (see "Caddy" below).

## Monitors

| Service | URL | Up when |
|---|---|---|
| Portfolio site | `https://davidvasutenko.fun` | `2xx` |
| n8n (automation) | `https://n8n.davidvasutenko.fun` | `2xx` or `401` (Basic-Auth = alive) |
| Grafana (observability) | `https://grafana.davidvasutenko.fun` | `2xx` |
| App (CI/CD demo) | `https://app.davidvasutenko.fun/health` | `2xx` |
| Status page | `https://status.davidvasutenko.fun` | `2xx` |
| RAG assistant | `https://rag.davidvasutenko.fun` | pending project #3 — disabled, not published |

Every monitor is an HTTP check with TLS-expiry notification on (`ignoreTls: false`).
Edit `provision/monitors.yml` and re-run the provision step to change the set —
it is idempotent.

## Run

Prereqs: the main `portfolio` stack is up (it owns the `portfolio_internal`
network and the Caddy proxy), and a DNS **A record** for `status.davidvasutenko.fun`
points at this server (required for Caddy to issue the TLS cert).

```bash
cp .env.example .env            # fill KUMA_ADMIN_*, SERVER_BOT_TOKEN/SERVER_CHAT_ID
                                # (the «Фриланс сервер» bot — infra technical alerts)

# 1) bring up Uptime Kuma (internal only, no host ports)
docker compose up -d

# 2) provision: Telegram notification + monitors + public status page (idempotent)
docker compose --profile provision run --rm provision

# 3) publish via Caddy: the status block is already in the repo-root Caddyfile,
#    reload the running proxy to pick it up
docker compose -p portfolio exec caddy caddy reload --config /etc/caddy/Caddyfile
```

Open `https://status.davidvasutenko.fun` → it redirects to the public page
`/status/status`. The admin UI is at `/dashboard`.

## Caddy

Already added to the repo-root `Caddyfile`:

```caddy
status.davidvasutenko.fun {
	encode zstd gzip
	header {
		-Server
		Strict-Transport-Security "max-age=31536000;"
		X-Content-Type-Options "nosniff"
	}

	# Root → public status page (login UI stays on /dashboard).
	@root path /
	redir @root /status/status 302

	reverse_proxy uptime-kuma:3001
}
```

## Alert drill (reproducible proof)

Triggers a **real** down→up alert in Telegram and an incident on the page, using a
disposable target so nothing real is touched:

```bash
# 1) start the disposable target and add a hidden drill monitor
docker compose --profile drill up -d drill-target
DRILL=true docker compose --profile provision run --rm provision   # monitor goes UP

# 2) kill the target → Kuma fires a DOWN alert to Telegram + opens an incident
docker compose --profile drill stop drill-target
#    ... capture the Telegram message and the incident on the dashboard ...

# 3) bring it back → UP/recovery alert, incident resolves
docker compose --profile drill start drill-target

# 4) tear down the drill (remove the monitor manually in the UI if desired)
docker compose --profile drill down
```

The drill monitor is hidden from the public page (`published: false`), so the public
status stays clean.

## Security model

- **No host ports.** `uptime-kuma` only `expose`s 3001 on `portfolio_internal`;
  the public internet reaches it solely through Caddy (TLS). The admin dashboard is
  on the same TLS subdomain — protect the admin password accordingly.
- **`no-new-privileges`** on the container; provision image runs as a non-root user.
- **Secrets via env only** (`.env` is gitignored). The «Фриланс сервер» bot token and
  Kuma admin credentials never enter the repo.
- Monitors hit **public** URLs, so a green board proves the full external path
  (DNS, certificate, proxy, app), the same thing a visitor experiences.

> Note: the upstream `louislam/uptime-kuma` image runs its process as root inside the
> container (its entrypoint manages `/app/data`). Privilege is contained via
> `no-new-privileges`, a named volume, and no host port publishing.
