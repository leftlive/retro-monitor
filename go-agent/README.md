# Go Agent

This directory is the current macOS implementation of the long-running telemetry agent.

Current state:

- fixed telemetry schema
- background sampler with cached `/telemetry` snapshots
- HTTP server
- `mock` provider
- `macos` provider with direct AppleSMC, IOKit GPU stats, NVMe SMART disk temperature, and optional Intel Power Gadget whole-system power

Implemented on the current macOS provider:

- `cpu_temp`
- `cpu_load`
- `cpu_clock`
- `cpu_power`
- `gpu_temp`
- `gpu_load`
- `gpu_clock`
- `gpu_power`
- `memory_*`
- `fan_rpm_max`
- `fan_rpm_avg`
- `disk_temp_max`
- `disk_activity_percent`
- `net_up_bps`
- `net_down_bps`
- `system_power_estimated`

Remaining gaps:

- validate `cpu_power` source quality on this machine, where the current SMC keys resolve to `0`
- validate whether Intel Power Gadget `platform_power` is available on target hardware
- keep the Python package available as a prototype/reference surface until it is no longer useful for tests

## Run

```bash
cd go-agent
go run ./cmd/retro-monitor-agent --provider macos --host 0.0.0.0 --port 8126 --sample-interval 500ms
```

## Next Steps

- validate whole-system power against real-world hardware behavior
- decide whether the Python prototype should stay as a compatibility harness or move fully into archive
