# Home Assistant Communication Spec v1

This document defines the first stable communication contract between the local telemetry agent and the Home Assistant custom integration.

## Scope

This spec covers only the inbound telemetry path:

- `telemetry agent -> Home Assistant`

It does not yet define a write-back control API for:

- display mode
- OLED brightness
- page interval
- auto-rotate

Those controls currently exist only as local Home Assistant entities and are not pushed back to the agent in v1.

## Connection Model

- Home Assistant is the HTTP client.
- The telemetry agent is the HTTP server.
- Home Assistant polls the agent on a fixed interval.
- One config entry represents one telemetry endpoint.
- One telemetry endpoint represents one device snapshot.

## Endpoint

- Method: `GET`
- Path: `/telemetry`
- Example: `http://127.0.0.1:8125/telemetry`
- Response content type: `application/json`
- Character encoding: `utf-8`

## Polling Rules

- Integration config fields:
  - `host`
  - `port`
  - `scan_interval`
- Current default scan interval: `2` seconds
- Recommended production scan interval: `1-2` seconds
- The agent should return one full snapshot per request.
- The agent should not stream partial updates in v1.

## Success Response

- HTTP status must be `200 OK`.
- The body must be one complete JSON object.
- Every schema field must be present.
- Missing values must be encoded as `null`.
- The body must not omit fields based on availability.

Example:

```json
{
  "device_id": "iandeiMac.local",
  "hostname": "iandeiMac.local",
  "platform": "macos_hackintosh",
  "timestamp": "2026-03-26T09:00:00Z",
  "source_ok": true,
  "cpu_temp": 58.0,
  "cpu_load": 17.4,
  "cpu_clock": 3420.0,
  "cpu_power": 75.3,
  "gpu_temp": 54.0,
  "gpu_load": 21.0,
  "gpu_clock": 1139.0,
  "gpu_power": 38.0,
  "memory_used_mb": 25764.6,
  "memory_total_mb": 65536.0,
  "memory_percent": 50.8,
  "fan_rpm_max": 2951.0,
  "fan_rpm_avg": 678.8,
  "disk_temp_max": 41.0,
  "disk_activity_percent": 0.0,
  "net_up_bps": 0.0,
  "net_down_bps": 0.0,
  "system_power_estimated": null
}
```

## Failure Semantics

Transport-level failure:

- DNS failure
- connection refused
- timeout
- non-2xx response
- invalid JSON

Home Assistant behavior:

- coordinator update fails
- entities become unavailable until the next successful refresh

Payload-level degradation:

- HTTP status is still `200`
- JSON is still valid
- `source_ok=false`
- any subset of numeric fields may be `null`

Home Assistant behavior:

- entities remain available
- `source_ok` binary sensor turns off
- field entities expose `null` as unavailable state where Home Assistant applies it

## Timestamp Rules

- `timestamp` must be ISO 8601 in UTC
- Example: `2026-03-26T09:00:00Z`
- The timestamp represents sample creation time, not response send time
- The agent should generate a fresh timestamp for every new snapshot

## Field Mapping

The integration maps JSON fields directly to Home Assistant entities without additional derived calculations in v1.

Telemetry sensors:

- `cpu_temp`
- `cpu_load`
- `cpu_clock`
- `cpu_power`
- `gpu_temp`
- `gpu_load`
- `gpu_clock`
- `gpu_power`
- `memory_used_mb`
- `memory_total_mb`
- `memory_percent`
- `fan_rpm_max`
- `fan_rpm_avg`
- `disk_temp_max`
- `disk_activity_percent`
- `net_up_bps`
- `net_down_bps`
- `system_power_estimated`

Binary sensor:

- `source_ok`

Device identity attributes carried by the payload:

- `device_id`
- `hostname`
- `platform`
- `timestamp`

## Unit Contract

Home Assistant must treat the payload units as already normalized by the agent.

- temperatures: `°C`
- load and percent fields: `0-100`
- `cpu_clock` and `gpu_clock`: `MHz`
- `cpu_power`, `gpu_power`, `system_power_estimated`: `W`
- `memory_*_mb`: `MiB`
- `fan_*`: `RPM`
- `net_*_bps`: `bit/s`

Home Assistant must not apply a second unit conversion inside the integration logic.

## Validation Rules

The integration should reject malformed payloads conceptually if any of these break:

- body is not a JSON object
- required keys are missing
- `timestamp` is not a string
- `source_ok` is not a boolean

For the current scaffold, this validation is still light. The contract is now fixed even if the enforcement code remains minimal.

## Device Model

For v1, the device key should be derived from the payload identity rather than only from host and port once the integration is hardened.

Preferred identity priority:

1. `device_id`
2. `hostname`
3. configured `host:port`

The current scaffold still uses `host:port` as the config entry unique id.

## Refresh and Performance Expectations

- The agent should respond quickly enough for `1-2` second polling.
- The target budget for a local request should stay well below `500 ms`.
- The agent should avoid shelling out to CLI tools in the hot path.
- The response body should remain compact and deterministic.

## v1 Non-Goals

- authentication
- HTTPS
- push transport
- websocket streaming
- bulk multi-device response
- write-back display control
- history or trend arrays

## v2 Candidates

- payload schema version field
- response-side validation in the integration
- write-back control endpoint for OLED settings
- multi-device endpoint or device registry feed
- stronger staleness logic based on `timestamp`
