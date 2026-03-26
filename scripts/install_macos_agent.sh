#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.ian.retromonitor.agent"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$LABEL.plist"
TEMPLATE_PATH="$REPO_ROOT/deploy/macos/$LABEL.plist.template"
LOG_DIR="$HOME/Library/Logs/retro-monitor"
STDOUT_PATH="$LOG_DIR/agent.stdout.log"
STDERR_PATH="$LOG_DIR/agent.stderr.log"
GO_BIN="${GO_BIN:-$(command -v go)}"
AGENT_BIN_PATH="${AGENT_BIN_PATH:-$REPO_ROOT/go-agent/bin/retro-monitor-agent}"

mkdir -p "$LAUNCH_AGENTS_DIR" "$LOG_DIR"

if [[ ! -x "$GO_BIN" ]]; then
  echo "go not found" >&2
  exit 1
fi

mkdir -p "$(dirname "$AGENT_BIN_PATH")"

(
  cd "$REPO_ROOT/go-agent"
  "$GO_BIN" build -o "$AGENT_BIN_PATH" ./cmd/retro-monitor-agent
)

python3 - <<PY
from pathlib import Path

template = Path("$TEMPLATE_PATH").read_text()
plist = (
    template
    .replace("__AGENT_BIN__", "$AGENT_BIN_PATH")
    .replace("__WORKDIR__", "$REPO_ROOT")
    .replace("__STDOUT__", "$STDOUT_PATH")
    .replace("__STDERR__", "$STDERR_PATH")
)
Path("$PLIST_PATH").write_text(plist)
PY

chmod 644 "$PLIST_PATH"

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl enable "gui/$(id -u)/$LABEL"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo "Installed LaunchAgent: $PLIST_PATH"
echo "Label: $LABEL"
echo "Binary: $AGENT_BIN_PATH"
echo "Logs:"
echo "  stdout: $STDOUT_PATH"
echo "  stderr: $STDERR_PATH"
