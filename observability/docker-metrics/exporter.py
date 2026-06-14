#!/usr/bin/env python3
"""
Маленький экспортёр метрик контейнеров поверх Docker API.

Зачем не cAdvisor: этот хост использует storage-driver "overlayfs" (containerd
image store / snapshotter), на котором cAdvisor не может определить RW-layer и
вообще не регистрирует docker-контейнеры → нет ни имён, ни метрик. Экспортёр
читает docker.sock (read-only, группа docker) и отдаёт CPU/RAM/сеть с понятными
ИМЕНАМИ контейнеров, не завися от драйвера хранилища.

Метрики:
  docker_container_up{name,id,image}                 1 running / 0 stopped
  docker_container_cpu_percent{name}
  docker_container_memory_usage_bytes{name}
  docker_container_memory_limit_bytes{name}
  docker_container_network_receive_bytes_total{name}
  docker_container_network_transmit_bytes_total{name}
"""
import time
import threading
import logging

import docker
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("docker-metrics")
client = docker.from_env()


def cpu_percent(s: dict) -> float | None:
    try:
        c = s["cpu_stats"]; p = s["precpu_stats"]
        cd = c["cpu_usage"]["total_usage"] - p["cpu_usage"]["total_usage"]
        sd = c["system_cpu_usage"] - p.get("system_cpu_usage", 0)
        ncpu = c.get("online_cpus") or len(c["cpu_usage"].get("percpu_usage") or [1])
        return round((cd / sd) * ncpu * 100, 2) if sd > 0 and cd > 0 else 0.0
    except (KeyError, TypeError, ZeroDivisionError):
        return None


class DockerCollector:
    def collect(self):
        up = GaugeMetricFamily("docker_container_up", "1 if running, 0 if stopped",
                               labels=["name", "id", "image"])
        cpu = GaugeMetricFamily("docker_container_cpu_percent", "CPU %", labels=["name"])
        mem = GaugeMetricFamily("docker_container_memory_usage_bytes", "Memory bytes", labels=["name"])
        lim = GaugeMetricFamily("docker_container_memory_limit_bytes", "Memory limit bytes", labels=["name"])
        rx = CounterMetricFamily("docker_container_network_receive_bytes_total", "Net RX", labels=["name"])
        tx = CounterMetricFamily("docker_container_network_transmit_bytes_total", "Net TX", labels=["name"])

        try:
            containers = client.containers.list(all=True)
        except Exception as e:  # noqa: BLE001
            log.warning("docker list failed: %s", e)
            yield up
            return

        running = [c for c in containers if c.status == "running"]
        stats: dict[str, dict] = {}

        def grab(c):
            try:
                stats[c.id] = c.stats(stream=False)
            except Exception:  # noqa: BLE001
                pass

        threads = [threading.Thread(target=grab, args=(c,)) for c in running]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        for c in containers:
            name = c.name
            image = (c.image.tags[0] if c.image and c.image.tags
                     else (c.image.short_id if c.image else "unknown"))
            up.add_metric([name, c.id[:12], image], 1 if c.status == "running" else 0)
            s = stats.get(c.id)
            if not s:
                continue
            pct = cpu_percent(s)
            if pct is not None:
                cpu.add_metric([name], pct)
            try:
                ms = s["memory_stats"]
                usage = ms["usage"] - ms.get("stats", {}).get("inactive_file", 0)
                mem.add_metric([name], usage)
                lim.add_metric([name], ms.get("limit", 0))
            except (KeyError, TypeError):
                pass
            nets = s.get("networks") or {}
            if nets:
                rx.add_metric([name], sum(n.get("rx_bytes", 0) for n in nets.values()))
                tx.add_metric([name], sum(n.get("tx_bytes", 0) for n in nets.values()))

        yield up
        yield cpu
        yield mem
        yield lim
        yield rx
        yield tx


if __name__ == "__main__":
    REGISTRY.register(DockerCollector())
    start_http_server(9101)
    log.info("docker-metrics exporter on :9101")
    while True:
        time.sleep(3600)
