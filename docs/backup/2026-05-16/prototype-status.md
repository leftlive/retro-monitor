# Prototype Status

This document captures the current Python prototype baseline after local real-machine validation.

## Current Baseline

Validated on this machine through the local endpoint:

- command:
  - `PYTHONPATH=src python3 -m retro_monitor_agent --provider macos --host 127.0.0.1 --port 8125`
- endpoint:
  - `http://127.0.0.1:8125/telemetry`

Latest successful sample during validation:

```json
{
  "device_id": "iandeiMac.local",
  "hostname": "iandeiMac.local",
  "platform": "macos_hackintosh",
  "timestamp": "2026-03-25T17:08:45Z",
  "source_ok": true,
  "cpu_temp": 58.0,
  "cpu_load": 0.0,
  "cpu_clock": 3420,
  "cpu_power": 57.7,
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

Sampling model:

- the agent now samples on a fixed background interval
- `/telemetry` returns the latest cached snapshot
- the current default sample interval is `0.5` seconds
- request frequency no longer changes the sampling cadence

## What Is Actually Working

Working now without shelling out to CLI tools:

- direct AppleSMC path:
  - `cpu_temp`
  - `cpu_power`
  - `fan_rpm_max`
  - `fan_rpm_avg`
- direct IORegistry `PerformanceStatistics` path:
  - `gpu_temp`
  - `gpu_load`
  - `gpu_clock`
  - `gpu_power`
- direct NVMe SMART path via IOKit plug-in interface:
  - `disk_temp_max`
- process-local system sampling:
  - `cpu_load`
  - `cpu_clock`
  - `memory_used_mb`
  - `memory_total_mb`
  - `memory_percent`
  - `net_up_bps`
  - `net_down_bps`
  - `disk_activity_percent`

Current caveat:

- `system_power_estimated`
  - optional Intel Power Gadget platform-power path is wired in
  - current machine still reports platform energy as unavailable
  - the published value falls back to a conservative estimate: `cpu_power + gpu_power + 20W base`
  - this is useful for display and trend context, but should not be treated as wall power

## Reference Absorption

The current prototype has already absorbed these ideas:

- from `SMCKit`:
  - direct AppleSMC open/read model
  - fan count and fan current speed access pattern
- from `HWMonitorSMC2`:
  - AMD GPU metrics from `PerformanceStatistics`
  - the exact Radeon-oriented keys worth trusting
  - package power key naming for Intel Hackintosh
- from `Stats`:
  - modular collector structure
  - delta-based sampling for disk and network activity
  - NVMe SMART access through `IONVMeSMARTInterface`
  - SMC power data type decoding such as `sp96`
- from Intel Power Gadget:
  - optional library-backed platform power path without shelling out to CLI tools

## Current Integration Status

The Python agent is no longer the only active prototype surface:

- Home Assistant now consumes the macOS endpoint at `192.168.50.199:8125/telemetry`
- HA exposes hidden display payload sources for aggregation
- `desktop_current_*` template entities provide the stable computer state consumed by OLED and VFD
- OLED and VFD controls now live on their ESPHome devices, not in the `retro_monitor` integration

## Current Todo

- keep “whole-system power” as an estimation caveat until a better direct source is available
- validate Windows desktop provider against the same schema and `desktop_current_*` aggregation layer
- move the mature telemetry paths into the Go agent after the Python contract is stable
