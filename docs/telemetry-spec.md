# Telemetry Schema v1

This document fixes the first version of the desktop telemetry contract.

For the Home Assistant transport contract built on top of this schema, see `docs/homeassistant-communication-spec.md`.

## Transport

- Endpoint: `GET /telemetry`
- Content type: `application/json`
- Response shape: one complete JSON object
- Missing sensor policy: every field is always present; unavailable values are `null`
- Timestamp format: ISO 8601 in UTC, for example `2026-03-26T08:00:00Z`

## Field Definitions

| Field | Type | Unit | Notes |
| --- | --- | --- | --- |
| `device_id` | string | n/a | Stable unique device id |
| `hostname` | string | n/a | Host name |
| `platform` | string | enum-like | Example: `macos_hackintosh`, `windows` |
| `timestamp` | string | ISO 8601 UTC | Sampling time |
| `source_ok` | boolean | n/a | `true` when the sample is trustworthy |
| `cpu_temp` | number or `null` | `°C` | Primary CPU temperature |
| `cpu_load` | number or `null` | `%` | Total CPU load from `0` to `100` |
| `cpu_clock` | number or `null` | `MHz` | Primary current CPU frequency |
| `cpu_power` | number or `null` | `W` | Estimated CPU power |
| `gpu_temp` | number or `null` | `°C` | Primary GPU temperature |
| `gpu_load` | number or `null` | `%` | Total GPU load from `0` to `100` |
| `gpu_clock` | number or `null` | `MHz` | Current GPU frequency |
| `gpu_power` | number or `null` | `W` | Estimated GPU power |
| `memory_used_mb` | number or `null` | `MiB` | Used memory |
| `memory_total_mb` | number or `null` | `MiB` | Total memory |
| `memory_percent` | number or `null` | `%` | Memory usage |
| `fan_rpm_max` | number or `null` | `RPM` | Highest fan speed |
| `fan_rpm_avg` | number or `null` | `RPM` | Average fan speed |
| `disk_temp_max` | number or `null` | `°C` | Highest disk temperature |
| `disk_activity_percent` | number or `null` | `%` | Disk activity |
| `net_up_bps` | number or `null` | `bit/s` | Current upload rate |
| `net_down_bps` | number or `null` | `bit/s` | Current download rate |
| `system_power_estimated` | number or `null` | `W` | Estimated total system power |

## Error Semantics

- `source_ok=false` means the sample is degraded or stale.
- Individual fields may still contain valid values when `source_ok=false`.
- Providers should prefer returning partial data with `null` values over failing the entire response.
