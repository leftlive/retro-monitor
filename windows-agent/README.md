# Windows Agent

This directory contains the first Windows-native telemetry agent for Retro Monitor.

## Goals

- keep the existing `GET /telemetry` contract unchanged
- sample in the background and return cached snapshots
- use `LibreHardwareMonitor` for hardware sensors
- use Windows-native counters and APIs for CPU, memory, network, and disk activity

## Status

This implementation is intentionally isolated from the current Go/macOS agent so the Windows path can move faster without destabilizing the existing stack.

The local environment used to create this scaffold only has the .NET runtime, not the SDK, so the project files and source are in place but were not compiled here. Build and validation should happen on a Windows machine with the .NET 8 SDK installed.

## Build

On Windows:

```powershell
cd C:\path\to\retro-monitor\windows-agent\RetroMonitor.WindowsAgent
dotnet restore
dotnet build
dotnet run
```

Then open:

```text
http://127.0.0.1:8125/telemetry
```

## Optional Sensor Dump

To inspect raw LibreHardwareMonitor sensors on a target Windows machine:

```powershell
dotnet run -- --dump-sensors
```

This is intended to help lock per-machine sensor mappings before service installation.

## Configuration

Settings live in `appsettings.json` under `RetroMonitor`.

Default values:

- host: `0.0.0.0`
- port: `8125`
- sample interval: `500ms`
- slow interval: `2000ms`
- system power base watts: `20`

## Notes

- Missing fields must return `null`, never be omitted.
- Some hardware sensors require administrator privileges on Windows.
- `LibreHardwareMonitor` coverage varies by motherboard, GPU, and storage controller. The agent should degrade gracefully by returning partial data with `source_ok=true` when enough key metrics are still available.
