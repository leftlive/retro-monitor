# OLED Control Requirements

This document captures the deferred v2 control requirements for the SSD1322 display path.
It is intentionally separate from the telemetry schema and current Home Assistant polling contract.

## Purpose

The current Home Assistant integration already exposes several OLED-related entities, but they are local-only preferences.
They do not yet write back to the agent or the ESP32 display node.

This document defines the preferred control model before implementing a real write-back path.

## Current State

Current Home Assistant control entities:

- `select.display_mode`
- `number.display_page_interval`
- `number.display_brightness`
- `switch.display_auto_rotate`

Current limitations:

- values are stored only inside Home Assistant
- no write-back API exists on the agent
- the ESP32 display does not consume these values as live controls
- naming is still scaffold-oriented rather than product-oriented

## Design Goals

- keep everyday controls simple and obvious
- separate high-frequency user actions from low-frequency configuration
- avoid exposing raw device-level parameters when a user-friendly abstraction is better
- keep Home Assistant as the central control surface
- allow future write-back without breaking entity semantics

## Recommended V2 Control Model

### Primary Controls

These should be the main user-facing controls in Home Assistant.

- `Display Power`
  - type: `switch`
  - purpose: turn the OLED on/off or enter a sleep state
  - reason: more useful than forcing brightness to zero

- `Brightness`
  - type: `number`
  - range: `0-100`
  - unit: `%`
  - purpose: user-facing brightness level
  - implementation note: the device may still map this to `0-255` internally

- `Current Page`
  - type: `select`
  - examples:
    - `P1 Core`
    - `P2 Trend`
    - `P3 Network`
  - purpose: choose the active page directly
  - reason: clearer than abstract mode names such as `summary`

### Behaviour Controls

These control how the display behaves over time.

- `Auto Rotate`
  - type: `switch`
  - purpose: enable or disable automatic page rotation

- `Auto Rotate Interval`
  - type: `number`
  - range: `5-60`
  - unit: `s`
  - purpose: how long to stay on each page before rotating

## Controls To Avoid As Primary UX

These may exist later as advanced settings, but should not be the main public controls.

- raw brightness `0-255`
- animation speed
- render refresh rate
- raw page mode strings such as `summary` or `diagnostics`
- font/theme/debug toggles

## Entity Naming Recommendations

Use product-style names that match what users see on the device.

Recommended names:

- `Display Power`
- `Brightness`
- `Current Page`
- `Auto Rotate`
- `Auto Rotate Interval`

Names to retire or rename:

- `Display Mode` -> replace with `Current Page`
- `Display Page Interval` -> rename to `Auto Rotate Interval`
- `Display Brightness` -> keep concept, change unit model to `%`

## Functional Requirements

### FR-1 Write-Back Path

Home Assistant control changes must be able to propagate to the display system.

Possible implementation paths:

- `HA -> Agent -> ESP32`
- `HA -> ESPHome API entity/state path`

Recommended direction:

- use the agent as the control contract owner
- let ESP32 consume resolved display settings from the same upstream source

### FR-2 Persistence

Control values must survive:

- Home Assistant restart
- macOS agent restart
- ESP32 reboot

Recommended persistence behavior:

- Home Assistant stores the user preference
- agent resolves and exposes the effective control state
- ESP32 restores the latest effective state after reconnect

### FR-3 Degraded Behavior

If the control path is unavailable:

- telemetry display should continue to work
- control entities should remain visible
- UI should clearly indicate that a control is not currently applied if acknowledgment is added later

### FR-4 Page Semantics

The page selector must map to real page contracts, not internal placeholders.

Examples:

- `P1 Core`
- `P2 Trend`
- `P3 Network`

This requires page definitions to be frozen before implementing the final select options.

## Non-Goals For V2

- per-widget customization from Home Assistant
- arbitrary layout editing from Home Assistant
- font switching as a user control
- real-time animation tuning from Home Assistant

## Suggested Implementation Order

1. Freeze the page model (`P1`, `P2`, `P3`, etc.)
2. Replace scaffold naming in HA entities with the recommended control names
3. Add a write-back contract to the agent
4. Make ESP32 consume live control state
5. Add recovery and persistence validation across reboots

## Open Questions

- Should `Display Power` mean true blanking, panel sleep, or a low-brightness standby state?
- Should `Current Page` be writable when `Auto Rotate` is on, or should manual selection temporarily suspend rotation?
- Should brightness be linear or perceptually mapped before being sent to the display?
- Should control acknowledgment be surfaced in Home Assistant as separate diagnostic entities?
