# Third-Party Hardware References

This repository does not redistribute vendor datasheets, product manuals, service manuals, or other copyrighted third-party reference files unless their license clearly allows redistribution.

The hardware notes in this project were informed by local/private reference material for:

- SSD1322 256x64 OLED modules
- ESP32-C3 SuperMini boards
- 016ST106INK VFD modules
- VFD controller timing and segment mapping references

When rebuilding the hardware research context, collect the relevant vendor files locally and do not commit them unless the redistribution rights are clear.

## Recommended Local Folder

Use a private, ignored folder such as:

```text
references/hardware/
```

The top-level `.gitignore` already ignores `references/`.

## Public Documentation Rule

Public docs should describe the derived wiring, firmware, and validation results, not mirror copyrighted PDFs or manuals.
