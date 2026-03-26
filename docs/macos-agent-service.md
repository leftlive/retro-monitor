# macOS Agent Service

This project now includes a native `LaunchAgent` setup for keeping the telemetry agent running in the background on macOS.

The LaunchAgent now runs the Go agent binary, not the earlier Python module.

## Files

- `deploy/macos/com.ian.retromonitor.agent.plist.template`
- `scripts/install_macos_agent.sh`
- `scripts/uninstall_macos_agent.sh`

## Install

```bash
cd /Users/ian/retro-monitor
./scripts/install_macos_agent.sh
```

This installs a user LaunchAgent at:

```text
~/Library/LaunchAgents/com.ian.retromonitor.agent.plist
```

The service runs:

```text
/Users/ian/retro-monitor/go-agent/bin/retro-monitor-agent --provider macos --host 0.0.0.0 --port 8125 --sample-interval 500ms
```

The install script automatically rebuilds the Go binary before loading the service.

## Logs

```text
~/Library/Logs/retro-monitor/agent.stdout.log
~/Library/Logs/retro-monitor/agent.stderr.log
```

## Useful Commands

Check service state:

```bash
launchctl print gui/$(id -u)/com.ian.retromonitor.agent
```

Restart service:

```bash
launchctl kickstart -k gui/$(id -u)/com.ian.retromonitor.agent
```

Remove service:

```bash
cd /Users/ian/retro-monitor
./scripts/uninstall_macos_agent.sh
```
