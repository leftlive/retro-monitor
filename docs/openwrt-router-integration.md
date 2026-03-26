# OpenWrt Router Integration

This document defines the lowest-cost integration path for bringing the OpenWrt router into the existing Retro Monitor service system.

## Goal

Add a router page that visually follows the current `P1` layout:

- first column: `NET`
- second column: `CPU`
- third column: `MEM`

The router page should stay simple and only use data that OpenWrt can read directly from its own system interfaces.

## Constraints

- do not introduce a heavy new stack
- do not require extra metrics daemons
- prefer existing OpenWrt-native data sources
- keep Home Assistant as the display hub
- keep Mac telemetry and router telemetry as separate devices

## Recommended Data Path

The Home Assistant container on this machine runs with `host` networking.
That means Home Assistant can reach services bound to `127.0.0.1` on the OpenWrt host directly.

Recommended path:

1. run a tiny router telemetry endpoint on the OpenWrt host
2. bind it to `127.0.0.1:<port>`
3. let Home Assistant poll that endpoint locally
4. expose router entities as a second device
5. let ESP32 consume those entities on a dedicated router page

This is the most cost-effective path because it avoids:

- LAN round-trips
- SSH polling from Home Assistant
- extra monitoring suites such as Prometheus/collectd
- mixing router fields into the Mac telemetry schema

## Data Sources

Only direct OpenWrt-native sources are used:

- `ubus call system board`
  - hostname / model / platform identity
- `ubus call system info`
  - load / memory
- `ubus call network.interface.wan status`
  - WAN status / uptime / L3 device
- `ubus call network.device status '{"name":"<l3_device>"}'`
  - byte counters / link speed / carrier
- `/sys/class/thermal/thermal_zone*/temp`
  - CPU/package temperature fallback
- `/proc/cpuinfo`
  - CPU core count

## Minimal Router Schema

Keep router telemetry separate from the Mac schema.

Recommended v1 router payload:

- `device_id`
- `hostname`
- `platform`
- `timestamp`
- `source_ok`
- `wan_up`
- `wan_uptime_s`
- `wan_ip`
- `net_down_bps`
- `net_up_bps`
- `net_link_mbps`
- `net_util_percent`
- `cpu_temp`
- `cpu_load_percent`
- `memory_used_mb`
- `memory_total_mb`
- `memory_percent`

Notes:

- `cpu_load_percent` may be estimated from load average and CPU core count
- `net_up_bps` / `net_down_bps` require delta sampling from previous byte counters
- `net_util_percent` is optional if link speed cannot be resolved

## Router P1 Field Mapping

The router page should mirror the structure of the Mac `P1` page, but with the first panel replaced by network status.

### NET panel

- title: `NET`
- main value: `net_down_bps` rendered in Mbps
- line 1: `UP <net_up_bps>`
- line 2: `WAN UP` or `WAN DOWN`
- progress blocks: `net_util_percent`

### CPU panel

- title: `CPU`
- main value: `cpu_temp`
- unit: `C`
- line 1: `LD <cpu_load_percent>`
- line 2: optional `WAN <uptime>` or device temp fallback
- progress blocks: `cpu_load_percent`

### MEM panel

- title: `MEM`
- main value: `memory_percent`
- unit: `%`
- line 1: `USE <used>/<total>`
- line 2: optional `IP <wan_ip>` or reserved diagnostic slot
- progress blocks: `memory_percent`

## Why Not Reuse The Mac Schema

The router is not a GPU-bearing desktop host.
Forcing router WAN metrics into `gpu_*` style fields would create semantic debt and make both Home Assistant and ESP32 logic harder to maintain.

Recommended rule:

- Mac telemetry remains one device schema
- OpenWrt telemetry becomes a second device schema
- Home Assistant is responsible for presenting both as separate devices

## Implementation Order

1. create a tiny OpenWrt-local telemetry script
2. wrap it in a localhost-only HTTP endpoint
3. validate the JSON payload manually on the router
4. decide whether to extend the existing HA integration or add a router-specific lightweight integration path
5. build the router OLED page after entities are stable

## Lowest-Development First Step

The lowest-cost first implementation is a shell script that:

- reads `ubus`
- reads `/proc` and `/sys/class/thermal`
- keeps one small state file under `/tmp`
- outputs a single JSON snapshot

This script can later be exposed through a trivial local HTTP wrapper.
