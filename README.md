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
- `src/retro_monitor_agent/`: Python agent package
- `go-agent/`: future Go agent
- `homeassistant/custom_components/retro_monitor/`: HA integration scaffold
- `esphome/oled_display.example.yaml`: display-side template
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
python -m retro_monitor_agent --provider macos --port 8125
```

Then open:

```text
http://127.0.0.1:8125/telemetry
```

## Current Status

The agent is runnable now.
The Home Assistant integration and ESPHome template are intentionally conservative scaffolds; they are ready to extend, but still need live Home Assistant and hardware validation.
The long-term direction is now to move the agent to Go while keeping Python as the current prototype.
