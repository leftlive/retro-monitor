"""Payload validation for Retro Monitor desktop and router schemas."""

from __future__ import annotations

from .const import PROFILE_DESKTOP, PROFILE_ROUTER


class PayloadValidationError(Exception):
    """Raised when a telemetry payload does not conform to the schema."""


DESKTOP_REQUIRED_KEYS: frozenset[str] = frozenset(
    (
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
)

DESKTOP_NUMERIC_FIELDS: frozenset[str] = frozenset(
    (
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
)

ROUTER_REQUIRED_KEYS: frozenset[str] = frozenset(
    (
        "device_id",
        "hostname",
        "platform",
        "model",
        "timestamp",
        "source_ok",
        "wan_up",
        "wan_uptime_s",
        "wan_ip",
        "net_down_bps",
        "net_up_bps",
        "net_link_mbps",
        "net_util_percent",
        "cpu_temp",
        "cpu_load_percent",
        "memory_used_mb",
        "memory_total_mb",
        "memory_percent",
    )
)

ROUTER_NUMERIC_FIELDS: frozenset[str] = frozenset(
    (
        "wan_uptime_s",
        "net_down_bps",
        "net_up_bps",
        "net_link_mbps",
        "net_util_percent",
        "cpu_temp",
        "cpu_load_percent",
        "memory_used_mb",
        "memory_total_mb",
        "memory_percent",
    )
)


def detect_payload_profile(data: dict) -> str:
    """Return the payload profile based on the present key set."""
    keys = set(data.keys())
    if ROUTER_REQUIRED_KEYS.issubset(keys):
        return PROFILE_ROUTER
    if DESKTOP_REQUIRED_KEYS.issubset(keys):
        return PROFILE_DESKTOP
    raise PayloadValidationError("payload does not match a supported profile")


def _validate_common_fields(data: dict) -> None:
    ts = data["timestamp"]
    if not isinstance(ts, str):
        raise PayloadValidationError(
            f"'timestamp' must be a string, got {type(ts).__name__}"
        )

    sok = data["source_ok"]
    if not isinstance(sok, bool):
        raise PayloadValidationError(
            f"'source_ok' must be a boolean, got {type(sok).__name__}"
        )


def _validate_numeric_fields(data: dict, numeric_fields: frozenset[str]) -> None:
    for key in numeric_fields:
        value = data[key]
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, (int, float))
        ):
            raise PayloadValidationError(
                f"'{key}' must be a number or null, got {type(value).__name__}"
            )


def validate_payload(data: object) -> dict:
    """Validate a raw telemetry payload and return it as a typed dict."""
    if not isinstance(data, dict):
        raise PayloadValidationError(
            f"payload must be a JSON object, got {type(data).__name__}"
        )

    profile = detect_payload_profile(data)
    if profile == PROFILE_ROUTER:
        missing = ROUTER_REQUIRED_KEYS - data.keys()
        if missing:
            raise PayloadValidationError(
                f"payload is missing required router fields: {sorted(missing)}"
            )
        if not isinstance(data["wan_up"], bool):
            raise PayloadValidationError(
                f"'wan_up' must be a boolean, got {type(data['wan_up']).__name__}"
            )
        if not isinstance(data["wan_ip"], str):
            raise PayloadValidationError(
                f"'wan_ip' must be a string, got {type(data['wan_ip']).__name__}"
            )
        _validate_common_fields(data)
        _validate_numeric_fields(data, ROUTER_NUMERIC_FIELDS)
        return data

    missing = DESKTOP_REQUIRED_KEYS - data.keys()
    if missing:
        raise PayloadValidationError(
            f"payload is missing required fields: {sorted(missing)}"
        )
    _validate_common_fields(data)
    _validate_numeric_fields(data, DESKTOP_NUMERIC_FIELDS)
    return data
