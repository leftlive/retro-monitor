# Contributing

Thanks for helping improve Retro Monitor.

## Development Setup

Python and Home Assistant tests:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

Go agent tests:

```bash
cd go-agent
go test ./...
```

Windows agent validation must run on Windows with the .NET 8 SDK:

```powershell
cd windows-agent\RetroMonitor.WindowsAgent
dotnet restore
dotnet build
dotnet run -- --dump-sensors
dotnet run
```

ESPHome configuration checks require a local `esphome/secrets.yaml`; start from `esphome/secrets.example.yaml`.

## Pull Request Guidelines

- Keep telemetry schema changes backward compatible.
- Do not commit local secrets, Wi-Fi credentials, private IPs, generated binaries, or device-specific package output.
- Keep generated build output out of Git; attach release artifacts to GitHub Releases instead.
- For hardware-specific changes, document the board, screen, and pin mapping used for validation.
- For Windows sensor changes, include a summary of `--dump-sensors` evidence without posting private machine identifiers.

## Documentation

Use generic examples such as `<router-ip>`, `<desktop-agent-ip>`, and `/path/to/retro-monitor`.
Avoid personal hostnames, local network addresses, and absolute user paths in public docs.
