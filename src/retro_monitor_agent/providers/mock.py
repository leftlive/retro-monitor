from __future__ import annotations

import socket
from typing import Optional

from retro_monitor_agent.schema import TelemetrySnapshot, utc_now_iso

from .base import TelemetryProvider


class MockTelemetryProvider(TelemetryProvider):
    def __init__(self, device_id: str = "mock-device", hostname: Optional[str] = None) -> None:
        self._device_id = device_id
        self._hostname = hostname or socket.gethostname()

    def sample(self) -> TelemetrySnapshot:
        return TelemetrySnapshot(
            device_id=self._device_id,
            hostname=self._hostname,
            platform="mock",
            timestamp=utc_now_iso(),
            source_ok=True,
            cpu_temp=54.2,
            cpu_load=21.4,
            cpu_clock=3875.0,
            cpu_power=48.6,
            gpu_temp=49.1,
            gpu_load=17.0,
            gpu_clock=1425.0,
            gpu_power=62.3,
            memory_used_mb=12288.0,
            memory_total_mb=32768.0,
            memory_percent=37.5,
            fan_rpm_max=1320.0,
            fan_rpm_avg=1080.0,
            disk_temp_max=41.0,
            disk_activity_percent=12.0,
            net_up_bps=4_800_000.0,
            net_down_bps=18_500_000.0,
            system_power_estimated=126.0,
        )
