#!/bin/sh

echo "Content-Type: application/json"
echo "Cache-Control: no-store"
echo ""
exec /usr/local/bin/router_telemetry.sh
