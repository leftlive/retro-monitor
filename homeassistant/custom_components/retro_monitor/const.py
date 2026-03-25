DOMAIN = "retro_monitor"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8125
DEFAULT_SCAN_INTERVAL = 2

DISPLAY_MODE_OPTIONS = ["summary", "diagnostics"]

TELEMETRY_SENSOR_FIELDS = (
    "cpu_temp",
    "cpu_load",
    "cpu_clock",
    "cpu_power",
    "gpu_temp",
    "gpu_load",
    "gpu_clock",
    "gpu_power",
    "memory_used_mb",
    "memory_total_mb",
    "memory_percent",
    "fan_rpm_max",
    "fan_rpm_avg",
    "disk_temp_max",
    "disk_activity_percent",
    "net_up_bps",
    "net_down_bps",
    "system_power_estimated",
)

