# Case — Observability stack

> Subheading proof: **3 provisioned dashboards · host + 16 containers + 5 endpoints · alert → Telegram in ~90s, verified · TLS expiry watched · zero click-ops**

## 01 — Brief

Monitoring was buried inside the DevOps case — a couple of panels, easy to miss. It
deserved its own, highly visual case: a real observability stack where the dashboards
sell the service on sight. Requirements: Prometheus + Grafana + exporters + blackbox +
Alertmanager, everything configured **as code** in the repo (no hand-clicked UI),
three ready dashboards, alerts to Telegram, and Grafana exposed under TLS behind a
login.

## 02 — What I did

- Stood up a self-contained stack: **Prometheus, Alertmanager, node_exporter,
  blackbox_exporter, Grafana**, plus a small Docker-API exporter for container metrics.
- **Everything as code**: scrape config, alert rules, Alertmanager routing, Grafana
  datasource and all three dashboards are JSON/YAML in the repo and provision on boot —
  `docker compose up -d` yields a populated Grafana with nothing to configure by hand.
- Three dashboards: **Host overview**, **Containers** (named, live CPU/RAM/net), and
  **Endpoints / Uptime** (per-endpoint up/down, **TLS days-left**, latency, 24h
  availability).
- **Alertmanager → «Фриланс сервер» Telegram bot**: high CPU/mem/disk, container down,
  endpoint down, TLS expiring < 14 days, scrape target down — with dedup, inhibition
  and resolved-notifications.
- Exposed Grafana via Caddy/TLS on `grafana.davidvasutenko.fun` **with login**
  (anonymous access switched off); internal components publish no host ports.
- Hit and solved a real environment constraint: this host runs Docker's containerd
  image store (`overlayfs` driver), on which **cAdvisor can't register containers**.
  Rather than ship a broken panel, I wrote a ~90-line non-root Docker-API exporter that
  reads `docker.sock` read-only and reports per-container metrics **with real names** —
  storage-driver-independent. (Stock cAdvisor config is kept in the README for
  overlay2 hosts.)

## 03 — Outcome

- Grafana **live** at `https://grafana.davidvasutenko.fun`, login-only, with three
  dashboards populated on first boot — no manual setup.
- **11 Prometheus targets up**: host, containers, 5 blackbox endpoints, app, and the
  stack's own components.
- Container metrics for all **16 running containers, by name**, despite the
  cAdvisor-incompatible storage driver.
- Alerting **verified end-to-end**: stopping a throwaway container fired
  `🔴 ContainerDown [critical]` to the «Фриланс сервер» bot within ~90s and resolved on
  restart; `TargetDown` also fired for a removed scrape target.
- TLS-expiry tracked on every public endpoint (≈88 days left at capture).
- Monitoring extracted from the DevOps case into its own reproducible stack; the old
  in-line Prometheus/Grafana were removed from the main compose.

---

## Screenshots to capture (live service, for the gallery)

1. **Host overview** — the gauges row (CPU/RAM/disk) + time-series, all green.
2. **Containers** — CPU/RAM per container with **real names** (caddy, n8n, wordpress…)
   and the running-count stat.
3. **Endpoints / Uptime** — the up/down tiles + **TLS days-left** tiles + the 24h
   availability table.
4. **Telegram alert** — the `🔴 ContainerDown [critical]` message (and the `✅`
   resolved) in the «Фриланс сервер» bot.
5. **Prometheus targets** — `/targets` page (or a Grafana table) showing all targets UP.
6. **Grafana login screen** — proof it's behind auth, not an open dashboard.

## Metrics / proofs for the subheading

- **`3 dashboards, 0 click-ops`** — everything provisions from the repo.
- **`alert → Telegram in ~90s`** — measured ContainerDown drill latency.
- **`11/11 targets up`** — scrape coverage across host, containers, endpoints.
- **`TLS expiry watched`** — cert days-left on every HTTPS endpoint.
- Optionally **`16 containers, by name`** — the container-metrics adaptation story.
