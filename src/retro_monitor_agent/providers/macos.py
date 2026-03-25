from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

import socket

import psutil

from retro_monitor_agent.apple_smc import AppleSMC
from retro_monitor_agent.iokit import read_nvme_temperature_max, search_service_plane_property
from retro_monitor_agent.schema import TelemetrySnapshot, utc_now_iso

from .base import TelemetryProvider


def _mib(value_bytes: int) -> float:
    return round(value_bytes / (1024 * 1024), 1)


def _round_optional(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 1)


def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def _extract_gpu_stats() -> Dict[str, float]:
    stats = search_service_plane_property("PerformanceStatistics", class_substring="AMDRadeon")
    if not isinstance(stats, dict):
        return {}

    payload: Dict[str, float] = {}
    mappings = {
        "gpu_load": "GPU Activity(%)",
        "gpu_clock": "Core Clock(MHz)",
        "gpu_power": "Total Power(W)",
        "gpu_temp": "Temperature(C)",
    }
    for output_key, input_key in mappings.items():
        value = stats.get(input_key)
        if isinstance(value, (int, float)):
            payload[output_key] = round(float(value), 1)
    return payload


def _mounted_bsd_names() -> List[str]:
    names = []
    seen = set()
    for partition in psutil.disk_partitions(all=False):
        device = partition.device
        if not device.startswith("/dev/"):
            continue
        bsd_name = device.split("/")[-1]
        if bsd_name in seen:
            continue
        seen.add(bsd_name)
        names.append(bsd_name)
    return names


class MacOSTelemetryProvider(TelemetryProvider):
    def __init__(self, device_id: Optional[str] = None, hostname: Optional[str] = None) -> None:
        self._hostname = hostname or socket.gethostname()
        self._device_id = device_id or self._hostname
        self._platform = "macos_hackintosh"

        try:
            self._smc = AppleSMC()
        except RuntimeError:
            self._smc = None

        self._last_net_sample = self._net_sample()
        self._last_disk_sample = self._disk_sample()
        psutil.cpu_percent(interval=None)

    def _net_sample(self) -> Tuple[float, int, int]:
        counters = psutil.net_io_counters()
        return time.monotonic(), counters.bytes_sent, counters.bytes_recv

    def _disk_sample(self) -> Optional[Tuple[float, float]]:
        counters = psutil.disk_io_counters()
        if counters is None:
            return None
        busy_ms = float(counters.read_time + counters.write_time)
        return time.monotonic(), busy_ms

    def _network_rates(self) -> Tuple[Optional[float], Optional[float]]:
        current = self._net_sample()
        previous = self._last_net_sample
        self._last_net_sample = current
        elapsed = current[0] - previous[0]
        if elapsed <= 0:
            return None, None
        up_bps = ((current[1] - previous[1]) * 8.0) / elapsed
        down_bps = ((current[2] - previous[2]) * 8.0) / elapsed
        return round(max(up_bps, 0.0), 1), round(max(down_bps, 0.0), 1)

    def _disk_activity_percent(self) -> Optional[float]:
        current = self._disk_sample()
        previous = self._last_disk_sample
        self._last_disk_sample = current
        if current is None or previous is None:
            return None
        elapsed_ms = (current[0] - previous[0]) * 1000.0
        if elapsed_ms <= 0:
            return None
        busy_delta = current[1] - previous[1]
        return round(max(0.0, min(100.0, (busy_delta / elapsed_ms) * 100.0)), 1)

    def _fan_speeds(self) -> List[float]:
        if self._smc is None:
            return []
        fan_count = self._smc.fan_count()
        if fan_count is None:
            return []
        speeds: List[float] = []
        for fan_index in range(fan_count):
            speed = self._smc.fan_speed(fan_index)
            if speed is not None:
                speeds.append(round(speed, 1))
        return speeds

    def sample(self) -> TelemetrySnapshot:
        cpu_freq = psutil.cpu_freq()
        virtual_memory = psutil.virtual_memory()
        gpu_stats = _extract_gpu_stats()
        fan_speeds = self._fan_speeds()
        net_up_bps, net_down_bps = self._network_rates()

        snapshot = TelemetrySnapshot.empty(
            device_id=self._device_id,
            hostname=self._hostname,
            platform=self._platform,
            source_ok=True,
        )
        snapshot.timestamp = utc_now_iso()
        snapshot.cpu_temp = _round_optional(self._smc.cpu_temperature() if self._smc else None)
        snapshot.cpu_load = round(psutil.cpu_percent(interval=None), 1)
        snapshot.cpu_clock = round(cpu_freq.current, 1) if cpu_freq and cpu_freq.current else None
        snapshot.cpu_power = _round_optional(self._smc.cpu_power() if self._smc else None)
        snapshot.gpu_temp = _round_optional(gpu_stats.get("gpu_temp"))
        snapshot.gpu_load = _round_optional(gpu_stats.get("gpu_load"))
        snapshot.gpu_clock = _round_optional(gpu_stats.get("gpu_clock"))
        snapshot.gpu_power = _round_optional(gpu_stats.get("gpu_power"))
        snapshot.memory_used_mb = _mib(virtual_memory.used)
        snapshot.memory_total_mb = _mib(virtual_memory.total)
        snapshot.memory_percent = round(float(virtual_memory.percent), 1)
        snapshot.fan_rpm_max = max(fan_speeds) if fan_speeds else None
        snapshot.fan_rpm_avg = _mean(fan_speeds)
        snapshot.disk_temp_max = _round_optional(read_nvme_temperature_max(_mounted_bsd_names()))
        snapshot.disk_activity_percent = self._disk_activity_percent()
        snapshot.net_up_bps = net_up_bps
        snapshot.net_down_bps = net_down_bps
        snapshot.system_power_estimated = None
        snapshot.source_ok = any(
            value is not None
            for value in (
                snapshot.cpu_temp,
                snapshot.cpu_load,
                snapshot.gpu_temp,
                snapshot.gpu_load,
                snapshot.memory_percent,
                snapshot.net_up_bps,
                snapshot.net_down_bps,
            )
        )
        return snapshot
