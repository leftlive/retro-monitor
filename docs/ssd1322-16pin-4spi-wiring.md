# SSD1322 16-Pin 4SPI Wiring

This document fixes the wiring contract for the current 16-pin SSD1322 OLED module when used in `4SPI` mode with an ESP32.

## Scope

This mapping applies to the module pinout provided by the current vendor image.
The bottom note in that image indicates:

- `D1 = SDA`
- `D0 = SCL`
- `D2-D7` left unconnected
- `RD` tied to `GND`
- `WR` tied to `GND`

## OLED Module Pinout

| OLED Pin | Label | Meaning | ESP32 Connection |
| --- | --- | --- | --- |
| 1 | `VSS` | Ground | `GND` |
| 2 | `VCC` | Power input | `3V3` or module-rated supply |
| 3 | `NC` | No connect | Leave open |
| 4 | `SCL` | SPI clock (`D0`) | `GPIO18` |
| 5 | `SDA` | SPI MOSI (`D1`) | `GPIO23` |
| 6 | `D2` | Parallel data | Leave open |
| 7 | `D3` | Parallel data | Leave open |
| 8 | `D4` | Parallel data | Leave open |
| 9 | `D5` | Parallel data | Leave open |
| 10 | `D6` | Parallel data | Leave open |
| 11 | `D7` | Parallel data | Leave open |
| 12 | `RD` | Read strobe | Tie to `GND` |
| 13 | `WR` | Write strobe | Tie to `GND` |
| 14 | `DC` | Data/command select | `GPIO16` |
| 15 | `RES` | Reset | `GPIO17` |
| 16 | `CS` | Chip select | `GPIO5` |

## ESPHome Signal Mapping

The current ESPHome demo file uses the same control mapping:

- `CLK` -> `GPIO18`
- `MOSI` -> `GPIO23`
- `CS` -> `GPIO5`
- `DC` -> `GPIO16`
- `RESET` -> `GPIO17`

See:

- `/path/to/retro-monitor/esphome/oled_display_p1_demo.yaml`

## Wiring Notes

- This module is being used in `4SPI` mode, not parallel mode.
- `D2-D7` must remain unconnected for this mode.
- `RD` and `WR` should be tied low as shown in the vendor pinout note.
- `VCC` must follow the module's rated supply voltage. Confirm the module power requirement before applying `5V`.
- ESP32 logic level is `3.3V`, which matches the signal wiring assumed by the current demo.

## First-Hardware Validation Checklist

- Confirm the OLED module really uses SSD1322 and `256x64`.
- Confirm the board's `VCC` requirement before power-on.
- Confirm `RD` and `WR` are tied to `GND`.
- Confirm `SCL` and `SDA` are not swapped.
- Confirm `CS`, `DC`, and `RES` match the ESPHome YAML.
