# Retro Monitor

Retro Monitor is a fresh project scaffold for an ESP32 + SSD1322 desktop monitor.
The repository currently includes:

- A fixed v1 telemetry schema
- A Python telemetry agent with `mock` and `macos` providers
- A Go migration target with a runnable HTTP agent skeleton
- A Home Assistant custom integration skeleton
- An ESPHome display template
- Basic tests for schema and agent behavior

## Repository Layout

- `docs/telemetry-spec.md`: fixed telemetry contract
- `docs/homeassistant-communication-spec.md`: Home Assistant polling and payload contract
- `docs/reference-projects.md`: reference mapping for `Stats`, `SMCKit`, and `HWMonitorSMC2`
- `docs/ssd1322-16pin-4spi-wiring.md`: wiring contract for the current 16-pin SSD1322 module
- `docs/oled-preview.md`: local browser preview workflow for SSD1322 layout tuning
- `docs/macos-agent-service.md`: LaunchAgent setup for a persistent macOS telemetry service
- `src/retro_monitor_agent/`: Python agent package
- `go-agent/`: future Go agent
- `homeassistant/custom_components/retro_monitor/`: HA integration scaffold
- `esphome/oled_display.example.yaml`: display-side template
- `tools/oled-preview/index.html`: zero-dependency local OLED preview
- `tests/`: unit tests for the agent and schema

## Quick Start

Create and activate a virtual environment, then run the mock server:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m retro_monitor_agent --provider mock --port 8125
```

To serve partial real data from the current macOS host:

```bash
python -m retro_monitor_agent --provider macos --port 8125 --sample-interval 0.5
```

Then open:

```text
http://127.0.0.1:8125/telemetry
```

## Current Status

The agent is runnable now.
The agent now uses a fixed-rate background sampler and `/telemetry` returns the latest cached snapshot instead of sampling on every request.
The current default sample interval is `0.5` seconds.
The Home Assistant integration and ESPHome template are intentionally conservative scaffolds; they are ready to extend, but still need live Home Assistant and hardware validation.
The long-term direction is now to move the agent to Go while keeping Python as the current prototype.

## macOS Background Service

To keep the macOS telemetry provider running as a persistent user service:

```bash
cd /Users/ian/retro-monitor
./scripts/install_macos_agent.sh
```
