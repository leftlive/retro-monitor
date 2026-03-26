# Windows Agent Integration

This document defines the first Windows-native telemetry agent path for Retro Monitor.

## Goal

Add a Windows telemetry endpoint without changing the existing Home Assistant or OLED-side contract.

The Windows agent must continue to expose:

- `GET /telemetry`
- one full JSON object
- all schema fields always present
- missing values represented as `null`

## Current Implementation

The Windows implementation lives under:

- `windows-agent/RetroMonitor.WindowsAgent/`

It is intentionally isolated from the current Go/macOS agent so the Windows path can move faster without destabilizing the existing stack.

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

## Known Limits

- This code was created in an environment that had the .NET runtime but not the SDK, so it was not compiled here.
- Final build and sensor validation must happen on a Windows machine with the .NET 8 SDK.
- Some sensors may require elevated privileges on Windows.
- LibreHardwareMonitor support varies by motherboard, storage controller, and GPU driver stack.
- First-machine sensor mapping may require running `--dump-sensors` once and adjusting heuristics.

## Validation Steps On Windows

1. `dotnet restore`
2. `dotnet run -- --dump-sensors`
3. confirm CPU/GPU/fan/storage sensors are visible
4. `dotnet run`
5. open `http://127.0.0.1:8125/telemetry`
6. verify full schema and field coverage
7. install as Windows Service
8. add a new `retro_monitor` entry in Home Assistant

## Recommended Next Work

1. compile on a real Windows target
2. lock the first-machine sensor naming heuristics
3. add unit tests after the build environment is available
4. validate service installation and restart behavior
