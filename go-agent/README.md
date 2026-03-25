# Go Agent

This directory is the migration target for the long-running telemetry agent.

Current state:

- fixed telemetry schema
- HTTP server
- `mock` provider
- `macos` provider skeleton backed by Go libraries for CPU, memory, network, and disk activity

Not yet implemented:

- direct AppleSMC access in Go
- direct IOKit GPU metrics in Go
- disk SMART temperature in Go
- CPU power and system power estimation

## Run

```bash
cd go-agent
go run ./cmd/retro-monitor-agent --provider mock --port 8126
```

## Next Steps

- add a Go SMC package based on `SMCKit` and the current Python prototype
- add an IOKit bridge for GPU metrics based on `HWMonitorSMC2`
- replace placeholder `macos` fields with direct sensor reads

