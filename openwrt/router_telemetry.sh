#!/bin/sh

set -eu

STATE_FILE="/tmp/retro-monitor-router.state"

read_json() {
  jsonfilter -e "$1" 2>/dev/null || true
}

to_mib() {
  awk -v v="$1" 'BEGIN { printf "%.1f", v / 1024 / 1024 }'
}

calc_percent() {
  awk -v used="$1" -v total="$2" 'BEGIN {
    if (total <= 0) { print "0.0"; exit }
    printf "%.1f", (used / total) * 100
  }'
}

calc_rate_bps() {
  awk -v cur="$1" -v prev="$2" -v elapsed="$3" 'BEGIN {
    if (elapsed <= 0 || cur < prev) { print "0.0"; exit }
    printf "%.1f", ((cur - prev) * 8) / elapsed
  }'
}

uptime_seconds() {
  awk '{ printf "%.3f", $1 }' /proc/uptime 2>/dev/null || printf '0.000'
}

calc_load_percent() {
  awk -v load_raw="$1" -v cores="$2" 'BEGIN {
    if (cores <= 0) cores = 1
    load1 = load_raw / 65536.0
    percent = (load1 / cores) * 100.0
    if (percent < 0) percent = 0
    if (percent > 100) percent = 100
    printf "%.1f", percent
  }'
}

calc_net_util() {
  awk -v down="$1" -v up="$2" -v link="$3" 'BEGIN {
    if (link <= 0) { print "0.0"; exit }
    cap = link * 1000000.0
    peak = down
    if (up > peak) peak = up
    percent = (peak / cap) * 100.0
    if (percent < 0) percent = 0
    if (percent > 100) percent = 100
    printf "%.1f", percent
  }'
}

safe_json_string() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

BOARD_JSON="$(ubus call system board)"
INFO_JSON="$(ubus call system info)"
WAN_JSON="$(ubus call network.interface.wan status)"

HOSTNAME="$(printf '%s' "$BOARD_JSON" | read_json '@.hostname')"
MODEL="$(printf '%s' "$BOARD_JSON" | read_json '@.model')"
L3_DEVICE="$(printf '%s' "$WAN_JSON" | read_json '@["l3_device"]')"
PHY_DEVICE="$(printf '%s' "$WAN_JSON" | read_json '@.device')"
WAN_UP="$(printf '%s' "$WAN_JSON" | read_json '@.up')"
WAN_UPTIME_S="$(printf '%s' "$WAN_JSON" | read_json '@.uptime')"
WAN_IP="$(printf '%s' "$WAN_JSON" | read_json '@["ipv4-address"][0].address')"

if [ -n "${L3_DEVICE}" ]; then
  DEV_JSON="$(ubus call network.device status "{\"name\":\"${L3_DEVICE}\"}")"
else
  DEV_JSON='{}'
fi

RX_BYTES="$(printf '%s' "$DEV_JSON" | read_json '@.statistics.rx_bytes')"
TX_BYTES="$(printf '%s' "$DEV_JSON" | read_json '@.statistics.tx_bytes')"
LINK_SPEED_RAW="$(printf '%s' "$DEV_JSON" | read_json '@.speed')"
LINK_SPEED_MBPS="$(printf '%s' "$LINK_SPEED_RAW" | tr -cd '0-9')"

if [ -z "${LINK_SPEED_MBPS}" ] || [ "${LINK_SPEED_MBPS}" = "0" ]; then
  if [ -n "${PHY_DEVICE}" ]; then
    PHY_JSON="$(ubus call network.device status "{\"name\":\"${PHY_DEVICE}\"}" 2>/dev/null || true)"
    PHY_LINK_SPEED_RAW="$(printf '%s' "$PHY_JSON" | read_json '@.speed')"
    PHY_LINK_SPEED_MBPS="$(printf '%s' "$PHY_LINK_SPEED_RAW" | tr -cd '0-9')"
    if [ -n "${PHY_LINK_SPEED_MBPS}" ]; then
      LINK_SPEED_MBPS="${PHY_LINK_SPEED_MBPS}"
    fi
  fi
fi

[ -n "${RX_BYTES}" ] || RX_BYTES=0
[ -n "${TX_BYTES}" ] || TX_BYTES=0
[ -n "${LINK_SPEED_MBPS}" ] || LINK_SPEED_MBPS=0
[ -n "${WAN_UPTIME_S}" ] || WAN_UPTIME_S=0

MEM_TOTAL_KB="$(printf '%s' "$INFO_JSON" | read_json '@.memory.total')"
MEM_AVAILABLE_KB="$(printf '%s' "$INFO_JSON" | read_json '@.memory.available')"
LOAD_RAW="$(printf '%s' "$INFO_JSON" | read_json '@.load[0]')"

[ -n "${MEM_TOTAL_KB}" ] || MEM_TOTAL_KB=0
[ -n "${MEM_AVAILABLE_KB}" ] || MEM_AVAILABLE_KB=0
[ -n "${LOAD_RAW}" ] || LOAD_RAW=0

MEM_USED_KB=$((MEM_TOTAL_KB - MEM_AVAILABLE_KB))
[ "${MEM_USED_KB}" -ge 0 ] || MEM_USED_KB=0

MEM_TOTAL_MB="$(to_mib "${MEM_TOTAL_KB}")"
MEM_USED_MB="$(to_mib "${MEM_USED_KB}")"
MEM_PERCENT="$(calc_percent "${MEM_USED_KB}" "${MEM_TOTAL_KB}")"

CORES="$(grep -c '^processor' /proc/cpuinfo 2>/dev/null || true)"
[ -n "${CORES}" ] || CORES=1
CPU_LOAD_PERCENT="$(calc_load_percent "${LOAD_RAW}" "${CORES}")"

CPU_TEMP_MILLIC=""
for zone in /sys/class/thermal/thermal_zone*/temp; do
  [ -f "${zone}" ] || continue
  value="$(cat "${zone}" 2>/dev/null || true)"
  case "${value}" in
    ''|*[!0-9]*)
      continue
      ;;
  esac
  if [ -z "${CPU_TEMP_MILLIC}" ] || [ "${value}" -gt "${CPU_TEMP_MILLIC}" ]; then
    CPU_TEMP_MILLIC="${value}"
  fi
done
[ -n "${CPU_TEMP_MILLIC}" ] || CPU_TEMP_MILLIC=0
CPU_TEMP="$(awk -v v="${CPU_TEMP_MILLIC}" 'BEGIN { printf "%.1f", v / 1000.0 }')"

NOW_TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
NOW_UPTIME_S="$(uptime_seconds)"

NET_UP_BPS="0.0"
NET_DOWN_BPS="0.0"
if [ -f "${STATE_FILE}" ]; then
  # shellcheck disable=SC2034
  read -r PREV_UPTIME PREV_RX PREV_TX PREV_DOWN PREV_UP < "${STATE_FILE}" || true
  if [ -n "${PREV_UPTIME:-}" ] && [ -n "${PREV_RX:-}" ] && [ -n "${PREV_TX:-}" ]; then
    ELAPSED="$(awk -v cur="${NOW_UPTIME_S}" -v prev="${PREV_UPTIME}" 'BEGIN { printf "%.3f", cur - prev }')"
    NET_DOWN_BPS="$(calc_rate_bps "${RX_BYTES}" "${PREV_RX}" "${ELAPSED}")"
    NET_UP_BPS="$(calc_rate_bps "${TX_BYTES}" "${PREV_TX}" "${ELAPSED}")"
    if awk -v elapsed="${ELAPSED}" 'BEGIN { exit !(elapsed < 0.75) }'; then
      [ -n "${PREV_DOWN:-}" ] && NET_DOWN_BPS="${PREV_DOWN}"
      [ -n "${PREV_UP:-}" ] && NET_UP_BPS="${PREV_UP}"
    fi
  fi
fi
printf '%s %s %s %s %s\n' "${NOW_UPTIME_S}" "${RX_BYTES}" "${TX_BYTES}" "${NET_DOWN_BPS}" "${NET_UP_BPS}" > "${STATE_FILE}"

NET_UTIL_PERCENT="$(calc_net_util "${NET_DOWN_BPS}" "${NET_UP_BPS}" "${LINK_SPEED_MBPS}")"

DEVICE_ID="$(safe_json_string "${HOSTNAME:-router}")"
HOSTNAME_JSON="$(safe_json_string "${HOSTNAME:-router}")"
MODEL_JSON="$(safe_json_string "${MODEL:-OpenWrt Router}")"
WAN_IP_JSON="$(safe_json_string "${WAN_IP:-}")"

if [ "${WAN_UP}" = "true" ]; then
  WAN_UP_JSON=true
else
  WAN_UP_JSON=false
fi

cat <<EOF
{
  "device_id": "${DEVICE_ID}",
  "hostname": "${HOSTNAME_JSON}",
  "platform": "openwrt_istoreos",
  "model": "${MODEL_JSON}",
  "timestamp": "${NOW_TS}",
  "source_ok": true,
  "wan_up": ${WAN_UP_JSON},
  "wan_uptime_s": ${WAN_UPTIME_S},
  "wan_ip": "${WAN_IP_JSON}",
  "net_down_bps": ${NET_DOWN_BPS},
  "net_up_bps": ${NET_UP_BPS},
  "net_link_mbps": ${LINK_SPEED_MBPS},
  "net_util_percent": ${NET_UTIL_PERCENT},
  "cpu_temp": ${CPU_TEMP},
  "cpu_load_percent": ${CPU_LOAD_PERCENT},
  "memory_used_mb": ${MEM_USED_MB},
  "memory_total_mb": ${MEM_TOTAL_MB},
  "memory_percent": ${MEM_PERCENT}
}
EOF
