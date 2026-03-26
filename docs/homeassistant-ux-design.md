# Home Assistant Integration — UX Design Document

> Version: v1 · Last updated: 2026-03-26

## 1. Target Audience

Home-lab enthusiasts who run Home Assistant and want a single dashboard  
for their PC hardware telemetry alongside other smart-home sensors.

Assumed knowledge:

- Familiar with adding custom integrations via HACS or manual copy.
- Comfortable with Lovelace dashboards.
- **Not** expected to understand the internal telemetry protocol or field encoding.

---

## 2. Primary Use Cases

| # | Scenario | What the user sees |
|---|----------|--------------------|
| 1 | **Glanceable health** | A Lovelace card showing CPU / GPU load, temps and fan speed |
| 2 | **Anomaly alerting** | HA automations that fire when `cpu_temp > 85` or `source_ok` turns off |
| 3 | **Historical trends** | Energy dashboard integration for power draw; HA history for temps |
| 4 | **Multi-device fleet** (future v2) | Separate device cards per monitored PC |

---

## 3. Role of Home Assistant in the System

```
 ┌─────────────┐       GET /telemetry        ┌────────────────┐
 │  Telemetry  │ ◄──── (poll every 2 s) ──── │ Home Assistant  │
 │    Agent    │                              │  Integration   │
 └──────┬──────┘                              └───────┬────────┘
        │                                             │
  local sensors                                Lovelace / Automations
```

- HA is the **observation and configuration hub**, not the data source.
- HA does **not** transform units — the agent normalizes everything.
- HA provides **entity state, history, alerting** on top of raw telemetry.

---

## 4. Entity Hierarchy

### 4.1 Core Sensors (default-visible)

These appear in entity lists and auto-complete by default.

| Entity Name | Protocol Field | Unit | Why core |
|-------------|---------------|------|----------|
| CPU Temperature | `cpu_temp` | °C | Primary health indicator |
| CPU Load | `cpu_load` | % | Primary utilization metric |
| CPU Clock | `cpu_clock` | MHz | Performance context |
| CPU Power | `cpu_power` | W | Power / thermal budget |
| GPU Temperature | `gpu_temp` | °C | Primary GPU indicator |
| GPU Load | `gpu_load` | % | GPU utilization |
| GPU Clock | `gpu_clock` | MHz | Performance context |
| GPU Power | `gpu_power` | W | Power budget |
| Memory Used | `memory_used_mb` | MiB | Active consumption |
| Memory Usage | `memory_percent` | % | Quick utilization glance |
| Fan Speed (Max) | `fan_rpm_max` | RPM | Cooling health indicator |
| Disk Activity | `disk_activity_percent` | % | I/O bottleneck signal |
| Network Upload | `net_up_bps` | bit/s | Traffic monitoring |
| Network Download | `net_down_bps` | bit/s | Traffic monitoring |

### 4.2 Diagnostic Sensors (hidden by default)

Accessible via "Show all" in the HA UI. Useful for troubleshooting but not
needed on a daily dashboard.

| Entity Name | Protocol Field | Unit | Why diagnostic |
|-------------|---------------|------|----------------|
| Memory Total | `memory_total_mb` | MiB | Static value, rarely changes |
| Fan Speed (Average) | `fan_rpm_avg` | RPM | Less actionable than max RPM |
| Disk Temperature (Max) | `disk_temp_max` | °C | Secondary to disk activity |
| System Power (Estimated) | `system_power_estimated` | W | Not yet reliably populated |

### 4.3 Binary Sensor (diagnostic)

| Entity Name | Protocol Field | Category |
|-------------|---------------|----------|
| Data Source OK | `source_ok` | DIAGNOSTIC |

- Extra attributes: `sample_timestamp`, `agent_platform`.
- When **off**: data is degraded — sensors still show values but should be
  treated with caution.

### 4.4 Config Entities (local-only OLED controls)

| Entity Name | Type | Default | Category |
|-------------|------|---------|----------|
| Display Mode | Select | `summary` | CONFIG |
| Display Brightness | Number (0–255) | 180 | CONFIG |
| Display Page Interval | Number (5–60 s) | 10 | CONFIG |
| Display Auto Rotate | Switch | on | CONFIG |

> **v1 status**: These are local HA state only. They are **not** pushed to
> the agent until a v2 write-back API is implemented. They exist so users
> can pre-configure their preferences and so automations can reference them
> today (e.g. "dim display at night" automation that writes target brightness).

---

## 5. Degraded & Failure States

### 5.1 Three-tier model

```
Tier 1: Transport Failure
  ├── DNS / connection refused / timeout / non-2xx / invalid JSON
  ├── coordinator raises UpdateFailed
  └── ALL entities → unavailable

Tier 2: Payload Validation Error
  ├── Valid HTTP 200 + JSON, but schema violated
  ├── coordinator raises UpdateFailed + WARNING log
  └── ALL entities → unavailable

Tier 3: Degraded Payload (source_ok=false)
  ├── Valid schema, but agent signals data is stale/unreliable
  ├── coordinator returns data normally
  ├── source_ok binary sensor → off
  ├── individual null fields → unknown
  └── non-null fields → still shown with last value
```

### 5.2 What the user sees

| Situation | Entity state | Dashboard |
|-----------|-------------|-----------|
| Agent healthy | Normal values | ✅ All cards green |
| Agent healthy, `source_ok=false` | Values shown, binary sensor off | ⚠️ Warning badge possible |
| Agent healthy, `cpu_temp=null` | CPU Temp shows "Unknown" | One card shows "—" |
| Agent unreachable | All entities "Unavailable" | ❌ Cards greyed out |
| Agent returns malformed JSON | All entities "Unavailable" | ❌ Cards greyed out |

---

## 6. Device Model

### 6.1 Current (v1)

- **One config entry = one device** in the HA device registry.
- Device identity derived from payload: `device_id` (primary), then `hostname`, then config `host:port`.
- Device name = `hostname` from payload (e.g. `iandeiMac.local`).
- Device model = `platform` from payload (e.g. `macos_hackintosh`).
- `configuration_url` links to the agent endpoint for quick status check.

### 6.2 Future multi-device (v2)

When multiple PCs are monitored:

- Each agent endpoint creates a separate config entry + device.
- `device_id` ensures stable identity even if IP changes.
- Entities are scoped per-device via `unique_id = {entry_id}_{field}`.
- Users see separate device cards in the dashboard, one per monitored PC.

---

## 7. Config Flow UX

### 7.1 Fields

| Field | Default | Validation |
|-------|---------|-----------|
| Host | `127.0.0.1` | String |
| Port | `8125` | 1–65535 |
| Scan interval | `2` s | 1–60 s |

### 7.2 Connection test

Before saving, the integration performs `GET /telemetry` against the provided
endpoint and validates the response against the full schema. Failure modes:

| Error | Message shown |
|-------|--------------|
| Network unreachable | "Cannot connect to the telemetry agent." |
| Valid HTTP but invalid schema | "The endpoint responded but returned an invalid telemetry payload." |
| Duplicate endpoint | "This agent endpoint is already configured." |

---

## 8. Dashboard Recommendations

### Recommended Lovelace cards

1. **Glance card** — CPU temp / CPU load / GPU temp / GPU load / Memory Usage
2. **Sensor card** — Fan Speed (Max) with graph
3. **History graph** — CPU Power + GPU Power stacked for energy trend
4. **Conditional card** — Show warning when `source_ok` = off

### Entity naming for auto-complete

All entity IDs follow `sensor.retro_monitor_{field}`. The human-readable names
are designed for natural language:

- ✅ "CPU Temperature" not ~~"cpu_temp"~~
- ✅ "Fan Speed (Max)" not ~~"Fan RPM Max"~~
- ✅ "Network Upload" not ~~"Net Upload"~~

---

## 9. Why This Design Is Better Than the Scaffold

| Aspect | Scaffold | v1 |
|--------|----------|-----|
| Entity hierarchy | Flat — all 18 sensors equal | 14 core + 4 diagnostic |
| Error handling | Single `try/except` | Three-tier (transport / validation / degradation) |
| Payload validation | None | Full schema check on every refresh |
| Config flow | No connection test | Live test + clear error messages |
| `source_ok=false` | Silent — treated same as success | Binary sensor + logged degradation |
| Device identity | May fail on first load | Cached `last_device_info` survives errors |
| OLED entities | Orphaned from device | Attached to device, marked CONFIG |
| Entity naming | Engineering names (`Fan RPM Max`) | User-friendly (`Fan Speed (Max)`) |

---

## 10. Items Requiring Main Agent Cooperation

These cannot be resolved in the HA integration alone:

1. **`system_power_estimated`** — currently always `null`. The main agent needs to
   stabilize a real data source before this sensor becomes useful.
2. **Write-back API (v2)** — OLED control entities are local-only. A future
   `POST /control` endpoint is needed to push settings to the agent/display.
3. **Schema version field** — a `schema_version` key in the payload would allow
   the integration to gracefully handle future protocol changes.
