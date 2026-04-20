# Retro Monitor

Retro Monitor is a local telemetry and display project for desktop, router, OLED,
and VFD monitoring devices.
The repository currently includes:

- A fixed v1 telemetry schema
- A Python telemetry agent with `mock`, `macos`, and fixed-rate cached sampling
- A Go migration target with a runnable HTTP agent skeleton
- A Home Assistant custom integration for telemetry entities
- Home Assistant template aggregation for `desktop_current_*`
- ESPHome firmware for SSD1322 OLED and ESP32-C3 VFD terminals
- Basic tests for schema and agent behavior

## Repository Layout

- `docs/project-progress-zh.md`: current project progress and ownership summary
- `docs/telemetry-spec.md`: fixed telemetry contract
- `docs/homeassistant-communication-spec.md`: Home Assistant polling and payload contract
- `docs/homeassistant-ux-design-zh.md`: current HA entity and control ownership model
- `docs/reference-projects.md`: reference mapping for `Stats`, `SMCKit`, and `HWMonitorSMC2`
- `docs/ssd1322-16pin-4spi-wiring.md`: wiring contract for the current 16-pin SSD1322 module
- `docs/oled-preview.md`: local browser preview workflow for SSD1322 layout tuning
- `docs/p2-trend-page-plan-zh.md`: P2 折线趋势页的效果设计与两阶段实现路径
- `docs/openwrt-router-integration.md`: low-cost router integration path for an OpenWrt/iStoreOS device
- `docs/macos-agent-service.md`: LaunchAgent setup for a persistent macOS telemetry service
- `docs/vfd-progress-zh.md`: ESP32-C3 VFD branch progress
- `docs/backup/`: outdated handoff and superseded design notes
- `src/retro_monitor_agent/`: Python agent package
- `go-agent/`: future Go agent
- `homeassistant/custom_components/retro_monitor/`: HA integration
- `homeassistant/packages/retro_monitor_desktop_current.yaml`: desktop source aggregation package
- `esphome/oled_display_p1_demo.yaml`: current SSD1322 OLED firmware
- `esphome/vfd_016st106ink_ha_monitor.yaml`: current ESP32-C3 VFD firmware
- `tools/oled-preview/index.html`: zero-dependency local OLED preview
- `openwrt/router_telemetry.sh`: minimal OpenWrt-side telemetry snapshot script
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

The agent now uses a fixed-rate background sampler and `/telemetry` returns the latest cached snapshot instead of sampling on every request.
The current default sample interval is `0.5` seconds.
The Home Assistant integration is now telemetry-only; display controls live on the OLED and VFD ESPHome devices.
The OLED and VFD devices consume the shared `desktop_current_*` HA entities.
The long-term direction remains moving the mature telemetry paths to Go while keeping Python as the current prototype.

## macOS Background Service

To keep the macOS telemetry provider running as a persistent user service:

```bash
cd /Users/ian/retro-monitor
./scripts/install_macos_agent.sh
```
