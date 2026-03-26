# OLED Preview

This repository now includes a local browser preview for the current `256x64` SSD1322 `P1` layout.

Path:

- `tools/oled-preview/index.html`

## Why This Exists

The ESPHome iteration loop is too slow for layout tuning:

1. edit YAML
2. compile
3. flash
4. inspect hardware

The preview reduces that loop to:

1. open browser
2. tweak font sizes / y positions / digit spacing
3. validate the composition visually
4. only flash when the layout is already close

## What It Simulates

- The current three-column `P1` page
- `256x64` SSD1322 aspect ratio
- Current font stack direction:
  - header: `UNSCII`
  - big digits: `MatrixSans`
  - other small text: `IBM Plex Mono`
- Header line, column dividers, unit placement, and stat rows
- A simple monochrome OLED-like glow

## What It Does Not Simulate Perfectly

- Exact SSD1322 pixel behavior
- Real panel brightness and ghosting
- Hardware offset quirks
- ESPHome text rasterization differences

It is a fast composition tool, not a pixel-perfect emulator.

## Why The Web Preview Can Drift From Real Hardware

The main mismatch comes from renderer differences:

- Browser canvas uses its own font rasterizer and metrics.
- ESPHome renders fonts through a different bitmap pipeline.
- The same `y` coordinate can produce a visibly different occupied pixel footprint.
- Large digits and compact stat rows are the most sensitive areas.

To reduce that mismatch, the preview now includes hardware compensation controls:

- `Big Bias Y`
- `Unit Bias Y`
- `Stat Bias Y`
- `Bar Bias Y`

These let the preview visually track the real SSD1322 result more closely after one hardware comparison.

## Run It

Serve the repository root:

```bash
cd /Users/ian/retro-monitor
python3 -m http.server 4173
```

Then open:

```text
http://127.0.0.1:4173/tools/oled-preview/index.html
```

## Suggested Workflow

1. Use the `Normal / Stress / Offline` presets.
2. Use the wider sliders to explore more aggressive changes for:
   - `headerSize`
   - `sectionSize`
   - `bigSize`
   - `statSize`
   - `lineY`
   - `sectionY`
   - `bigY`
   - `unitY`
   - `statY`
   - `digitStep`
3. Paste a real telemetry JSON snapshot into `Custom JSON` when needed.
4. Use `Export Layout` to copy the current layout JSON.
5. Use `Import Layout` to load a previous layout JSON and continue from that point.
6. Paste the final JSON back into the chat so the same values can be applied to firmware.
7. Once the preview is acceptable, copy the final values back into:
   - `esphome/oled_display_p1_demo.yaml`
8. Flash only for final hardware verification.
