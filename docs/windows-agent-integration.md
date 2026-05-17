# Windows Agent Integration

This document defines the Windows-native telemetry agent path for Retro Monitor.

## Goal

Provide a Windows telemetry endpoint without changing the existing Home Assistant or OLED-side contract.

The Windows agent must continue to expose:

- `GET /telemetry`
- one full JSON object
- all schema fields always present
- missing values represented as `null`

## Current Implementation

The Windows implementation lives under:

- `windows-agent/RetroMonitor.WindowsAgent/`

It is intentionally isolated from the current Go/macOS agent so the Windows path can evolve without destabilizing the existing stack.

## Current Status

The Windows agent is complete and has passed target-machine validation.

Validated on the Windows target:

1. `dotnet restore`
2. `dotnet build`
3. `dotnet run -- --dump-sensors`
4. `dotnet run`
5. `GET http://127.0.0.1:8125/telemetry`
6. full desktop schema with `platform="windows"`
7. Windows Service installation and startup
8. Home Assistant `Retro Monitor` config entry
9. `desktop_current_*` aggregation consuming Windows data

The current macOS workspace cannot re-run the Windows `.NET 8 SDK` validation because it only has a .NET runtime. Treat the Windows target-machine validation as the source of truth for this platform.

## Technology Choice

- Runtime model: `.NET 8`
- Sensor library: `LibreHardwareMonitorLib`
- Service model: ASP.NET Core + background sampler
- Deployment target: Windows Service

## Field Sources

### LibreHardwareMonitor-backed

- `cpu_temp`
- `cpu_clock`
- `cpu_power`
- `gpu_temp`
- `gpu_load`
- `gpu_clock`
- `gpu_power`
- `fan_rpm_max`
- `fan_rpm_avg`
- `disk_temp_max`
- `system_power_estimated` direct sensor only if available

### Windows-native API / counters

- `cpu_load`
- `memory_used_mb`
- `memory_total_mb`
- `memory_percent`
- `disk_activity_percent`
- `net_up_bps`
- `net_down_bps`

### Derived / estimated

- `system_power_estimated`
  - use direct system/platform power sensor if one exists
  - otherwise estimate as `cpu_power + gpu_power + base_watts`

## Sampling Model

- background sampler, not request-driven
- default sample interval: `500ms`
- default slow sensor interval: `2000ms`
- `/telemetry` returns the latest cached snapshot

## Device Identity

- `hostname`: `Environment.MachineName`
- `device_id`: Windows `MachineGuid`, with hostname fallback
- `platform`: `windows`

## Operational Notes

- Some sensors may require elevated privileges on Windows.
- LibreHardwareMonitor support varies by motherboard, storage controller, and GPU driver stack.
- New hardware may require running `--dump-sensors` again and adjusting heuristics.
- `system_power_estimated` is still an estimate unless a direct system/platform power sensor is available.

## Regression Steps On Windows

1. `dotnet restore`
2. `dotnet build`
3. `dotnet run -- --dump-sensors`
4. confirm CPU/GPU/fan/storage sensors are visible
5. `dotnet run`
6. open `http://127.0.0.1:8125/telemetry`
7. verify full schema and field coverage
8. install as Windows Service
9. add or reload the `retro_monitor` entry in Home Assistant
10. verify `desktop_current_*` can select the Windows source

## Recommended Maintenance Work

1. Preserve the v1 telemetry schema.
2. Re-run `--dump-sensors` when moving to different hardware.
3. Add Windows-side automated tests when the Windows build environment is available in CI or a repeatable target VM.
4. Keep service install, firewall rule, and package output behavior documented in `windows-agent/README.md`.
