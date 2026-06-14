# Observability stack — Prometheus + Grafana + Alertmanager

Self-contained monitoring stack for the whole server, configured **as code** (no
click-ops): metrics collection, three ready-made Grafana dashboards provisioned from
JSON, and Alertmanager routing alerts to Telegram. Grafana is exposed via Caddy with
TLS on `grafana.davidvasutenko.fun`, **behind a login** (no anonymous access).

`docker compose up -d` brings up Grafana already populated — nothing to set up by hand.

## What this demonstrates

> **DevOps / monitoring as a service.** Sells: "I instrument your servers and
> containers, put the numbers on a dashboard, and page you in Telegram before your
> users notice — all reproducible from a git repo, not a fragile hand-clicked setup."

- Metrics as code: Prometheus scrape config, alert rules, Alertmanager routing,
  Grafana datasource **and** dashboards all live in this repo and provision on boot.
- Three layers of visibility: **host** (node_exporter), **containers**
  (Docker API exporter), **external endpoints** (blackbox: HTTP + TLS expiry).
- Real alerting wired to existing on-call (Alertmanager → «Фриланс сервер» Telegram).
- Secure exposure: Grafana login-only behind Caddy/TLS; internal components never
  publish host ports.

## Stack

| Component | Role |
|---|---|
| Prometheus | scrape + rules + evaluation (15s) |
| Alertmanager | routes firing alerts → Telegram, dedup/inhibit/resolve |
| node_exporter | host metrics (CPU, RAM, disk, net) |
| docker-metrics | per-container CPU/RAM/net + up, with friendly names (see note) |
| blackbox_exporter | HTTP probes + TLS-cert expiry on public endpoints |
| Grafana | dashboards (provisioned), login required |

### Note on container metrics (cAdvisor vs docker-metrics)

cAdvisor was the first choice. This host runs Docker's **containerd image store**
(storage driver `overlayfs`, Docker 26+), with which cAdvisor cannot determine a
container's read-write layer and therefore **refuses to register any Docker
container** — no names, no metrics (`failed to identify the read-write layer ID`).

So container metrics come from a tiny **Docker-API exporter** (`./docker-metrics`,
~90 lines, non-root, reads `docker.sock` read-only as the `docker` group). It exports
CPU/RAM/network/up **with real container names**, independent of the storage driver.
On a host with the `overlay2` driver you can swap in stock cAdvisor instead:

```yaml
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.49.1
    privileged: true
    devices: [/dev/kmsg]
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    networks: [obs]
```
(and point the Prometheus `docker` job at `cadvisor:8080`).

## Dashboards

| Dashboard | Shows |
|---|---|
| **Host overview** | CPU / RAM / disk gauges, uptime, CPU-by-mode, memory, network, per-mount disk |
| **Containers** | running count, CPU/RAM/net per container (named), memory table |
| **Endpoints / Uptime** | per-endpoint up/down, TLS days-left, probe latency, 24h availability |

All under `grafana/dashboards/*.json`, loaded by the provisioning config — edit the
JSON, restart Grafana, done.

## Alerts (Alertmanager → Telegram)

| Alert | Fires when |
|---|---|
| HostHighCPU / HostHighMemory | > 90% for 5m |
| HostLowDisk | disk > 90% full for 5m |
| ContainerDown | a container is not running for 1m |
| EndpointDown | blackbox probe failing for 2m |
| TLSCertExpiringSoon | certificate expires in < 14 days |
| TargetDown | Prometheus can't scrape a target for 2m |

Rules in `prometheus/alerts.yml`; routing/format in
`alertmanager/alertmanager.tmpl.yml` (bot token + chat id rendered from env at start,
never committed). All alerts go to the **«Фриланс сервер»** bot.

## Run

Prereqs: the main `portfolio` stack is up (owns the `portfolio_internal` network and
Caddy), and a DNS record for `grafana.davidvasutenko.fun` points here.

```bash
cp .env.example .env     # GRAFANA_ADMIN_PASSWORD, SERVER_BOT_TOKEN/SERVER_CHAT_ID, DOCKER_GID
docker compose up -d     # Grafana comes up already provisioned

# Publish Grafana via Caddy (block already in the repo-root Caddyfile):
docker compose -p portfolio restart caddy
```

Grafana: `https://grafana.davidvasutenko.fun` (login with `admin` / `GRAFANA_ADMIN_PASSWORD`).
Prometheus and Alertmanager have **no host ports** — reach them for debugging via
`docker compose exec prometheus wget -qO- http://localhost:9090/...`.

## Caddy

```caddy
grafana.davidvasutenko.fun {
	encode zstd gzip
	header {
		-Server
		Strict-Transport-Security "max-age=31536000;"
		X-Content-Type-Options "nosniff"
	}
	reverse_proxy obs-grafana:3000
}
```

## Alert drill (reproducible proof)

```bash
docker run -d --name obs-alert-drill alpine sleep 900   # container goes up=1
# ~35s later it shows in the Containers dashboard
docker stop obs-alert-drill                             # up=0 → ContainerDown fires
#   ~90s later: 🔴 ContainerDown [critical] in the «Фриланс сервер» bot
docker rm -f obs-alert-drill                            # alert resolves → ✅
```

## Security model

- **No host ports** on Prometheus / Alertmanager / exporters; only the `obs` network
  internally, plus Grafana/Prometheus on `portfolio_internal` for Caddy and app scraping.
- **Grafana login required** — anonymous access disabled.
- **docker-metrics** runs non-root and mounts `docker.sock` **read-only**, accessed via
  the `docker` group (`group_add`), never as root.
- **Secrets via env only**: Grafana admin password and the Telegram bot token are in
  the gitignored `.env`; the Alertmanager config template carries placeholders.
