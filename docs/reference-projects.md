# Reference Projects

These projects are the reference sources behind the current Go macOS agent and the earlier Python prototype.

## exelban/stats

Primary reference for:

- macOS telemetry module boundaries
- GPU, disk, network, and memory collection patterns
- separation between sampling logic and presentation logic
- NVMe SMART access without shelling out to `smartctl`

Reason:

- broad device coverage
- active project
- closest match to a long-running local monitor

Use as:

- the structural mother repo for module layout
- the baseline for what the Go agent should eventually cover

Concrete source entrypoints:

- `references/stats/Modules/GPU/reader.swift`
  - how `PerformanceStatistics` is normalized for utilization, temperature, and clock values
- `references/stats/Modules/Disk/readers.swift`
  - how NVMe SMART data is fetched through IOKit
  - how per-disk activity deltas are computed
- `references/stats/SMC/smc.swift`
  - broader SMC data type decoding than the current project implementation

Absorb into this project:

- keep the current `PerformanceStatistics` path for AMD GPU telemetry
- keep the ported NVMe SMART path as the reference implementation for `disk_temp_max`
- reuse the module boundaries for the Go rewrite

## beltex/SMCKit

Primary reference for:

- AppleSMC communication model
- fan and temperature sensor key handling
- Intel Mac sensor access patterns
- a cleaner model for enumerating known keys and data types

Reason:

- focused SMC library
- MIT licensed
- easier to translate into a Go CGO layer than larger UI projects

Use as:

- the direct reference for a future Go SMC package

Concrete source entrypoint:

- `references/SMCKit/SMCKit/SMC.swift`
  - the best current source for the `SMCParamStruct`, selectors, and fan accessors

Absorb into this project:

- use its struct definitions and error model as the preferred shape for the Go SMC layer
- keep the Python `apple_smc.py` prototype compatible with the same mental model while it remains in the repo
- extend support for more SMC data types only when a new schema field actually needs them

## CloverHackyColor/HWMonitorSMC2

Primary reference for:

- Hackintosh-specific sensor coverage
- AMD GPU metrics through IOKit / IORegistry
- practical mapping between sensor names and exposed telemetry

Reason:

- closest reference for Intel Hackintosh + AMD Radeon setups
- confirms the viability of using `PerformanceStatistics` for GPU data

Use as:

- the reference for Hackintosh-specific GPU and sensor compatibility work

Concrete source entrypoints:

- `references/HWMonitorSMC2/HWMonitorSMC/HWMonitorSensors/SystemKit/Graphics.swift`
  - confirms the exact `PerformanceStatistics` keys worth using on AMD Radeon
- `references/HWMonitorSMC2/smcwrite/smcwrite/smc.c`
  - a compact C reference for direct AppleSMC calls on Hackintosh

Absorb into this project:

- treat it as the compatibility reference when `Stats` and local hardware behavior disagree
- prefer its GPU field mapping for Hackintosh AMD cards
- use it to validate sensor naming, not as the primary architecture template

## Recommended Direction

- Treat `go-agent/` as the active macOS service path.
- Keep `src/retro_monitor_agent/` as the earlier prototype/reference surface until the Go and Windows implementations no longer need it for comparison.
- Use these references for future parity fixes, especially power-source quality, SMC data type coverage, and hardware-specific GPU/NVMe behavior.

## Field Mapping Priority

Highest-value next absorptions:

1. `system_power_estimated`
   - source templates: `Stats` power aggregation plus whichever system-total SMC keys are stable on target hardware
   - goal: use direct low-level sources first, and keep Intel Power Gadget only as an optional fallback path
   - current finding on this machine: Intel Power Gadget package power works, but platform power is unavailable

Fields already validated in the macOS implementation/prototype lineage:

- `cpu_temp`, `cpu_power`, `fan_rpm_max`, `fan_rpm_avg` via direct AppleSMC access
- `gpu_temp`, `gpu_load`, `gpu_clock`, `gpu_power` via direct `PerformanceStatistics`
- `disk_temp_max` via direct NVMe SMART access through `IONVMeSMARTInterface`
- `cpu_load`, `cpu_clock`, `memory_*`, `net_*`, `disk_activity_percent` without CLI
