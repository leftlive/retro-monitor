"""Payload validation for the retro-monitor telemetry schema v1."""

from __future__ import annotations


class PayloadValidationError(Exception):
    """Raised when a telemetry payload does not conform to the schema."""


# Every key that MUST be present in every response.
REQUIRED_KEYS: frozenset[str] = frozenset(
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

# Keys whose value must be ``int | float | None``.
NUMERIC_FIELDS: frozenset[str] = frozenset(
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

# Identity fields carried alongside measurement data.
IDENTITY_FIELDS: frozenset[str] = frozenset(
    ("device_id", "hostname", "platform", "timestamp")
)


def validate_payload(data: object) -> dict:
    """Validate a raw telemetry payload and return it as a typed dict.

    Raises ``PayloadValidationError`` for any structural violation.
    A payload with ``source_ok=false`` or fields set to ``null`` is still
    considered **valid** — those are degradation signals, not schema errors.
    """

    if not isinstance(data, dict):
        raise PayloadValidationError(
            f"payload must be a JSON object, got {type(data).__name__}"
        )

    # --- required keys -------------------------------------------------------
    missing = REQUIRED_KEYS - data.keys()
    if missing:
        raise PayloadValidationError(
            f"payload is missing required fields: {sorted(missing)}"
        )

    # --- timestamp must be a string ------------------------------------------
    ts = data["timestamp"]
    if not isinstance(ts, str):
        raise PayloadValidationError(
            f"'timestamp' must be a string, got {type(ts).__name__}"
        )

    # --- source_ok must be a boolean -----------------------------------------
    sok = data["source_ok"]
    if not isinstance(sok, bool):
        raise PayloadValidationError(
            f"'source_ok' must be a boolean, got {type(sok).__name__}"
        )

    # --- numeric fields must be number | null --------------------------------
    for key in NUMERIC_FIELDS:
        value = data[key]
        if value is not None and not isinstance(value, (int, float)):
            raise PayloadValidationError(
                f"'{key}' must be a number or null, got {type(value).__name__}"
            )

    return data
