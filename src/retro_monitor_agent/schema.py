from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional

TELEMETRY_FIELDS = (
    "device_id",
    "hostname",
    "platform",
    "timestamp",
    "source_ok",
    "cpu_temp",
    "cpu_load",
    "cpu_clock",
    "cpu_power",
    "gpu_temp",
    "gpu_load",
    "gpu_clock",
    "gpu_power",
    "memory_used_mb",
    "memory_total_mb",
    "memory_percent",
    "fan_rpm_max",
    "fan_rpm_avg",
    "disk_temp_max",
    "disk_activity_percent",
    "net_up_bps",
    "net_down_bps",
    "system_power_estimated",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class TelemetrySnapshot:
    device_id: str
    hostname: str
    platform: str
    timestamp: str
    source_ok: bool
    cpu_temp: Optional[float] = None
    cpu_load: Optional[float] = None
    cpu_clock: Optional[float] = None
    cpu_power: Optional[float] = None
    gpu_temp: Optional[float] = None
    gpu_load: Optional[float] = None
    gpu_clock: Optional[float] = None
    gpu_power: Optional[float] = None
    memory_used_mb: Optional[float] = None
    memory_total_mb: Optional[float] = None
    memory_percent: Optional[float] = None
    fan_rpm_max: Optional[float] = None
    fan_rpm_avg: Optional[float] = None
    disk_temp_max: Optional[float] = None
    disk_activity_percent: Optional[float] = None
    net_up_bps: Optional[float] = None
    net_down_bps: Optional[float] = None
    system_power_estimated: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {field: payload[field] for field in TELEMETRY_FIELDS}

    @classmethod
    def empty(cls, *, device_id: str, hostname: str, platform: str, source_ok: bool = False) -> "TelemetrySnapshot":
        return cls(
            device_id=device_id,
            hostname=hostname,
            platform=platform,
            timestamp=utc_now_iso(),
            source_ok=source_ok,
        )
