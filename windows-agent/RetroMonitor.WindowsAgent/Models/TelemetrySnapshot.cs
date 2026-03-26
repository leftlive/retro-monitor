using System.Text.Json.Serialization;

namespace RetroMonitor.WindowsAgent.Models;

public sealed class TelemetrySnapshot
{
    [JsonPropertyName("device_id")]
    public string DeviceId { get; set; } = string.Empty;

    [JsonPropertyName("hostname")]
    public string Hostname { get; set; } = string.Empty;

    [JsonPropertyName("platform")]
    public string Platform { get; set; } = string.Empty;

    [JsonPropertyName("timestamp")]
    public string Timestamp { get; set; } = string.Empty;

    [JsonPropertyName("source_ok")]
    public bool SourceOk { get; set; }

    [JsonPropertyName("cpu_temp")]
    public double? CpuTemp { get; set; }

    [JsonPropertyName("cpu_load")]
    public double? CpuLoad { get; set; }

    [JsonPropertyName("cpu_clock")]
    public double? CpuClock { get; set; }

    [JsonPropertyName("cpu_power")]
    public double? CpuPower { get; set; }

    [JsonPropertyName("gpu_temp")]
    public double? GpuTemp { get; set; }

    [JsonPropertyName("gpu_load")]
    public double? GpuLoad { get; set; }

    [JsonPropertyName("gpu_clock")]
    public double? GpuClock { get; set; }

    [JsonPropertyName("gpu_power")]
    public double? GpuPower { get; set; }

    [JsonPropertyName("memory_used_mb")]
    public double? MemoryUsedMb { get; set; }

    [JsonPropertyName("memory_total_mb")]
    public double? MemoryTotalMb { get; set; }

    [JsonPropertyName("memory_percent")]
    public double? MemoryPercent { get; set; }

    [JsonPropertyName("fan_rpm_max")]
    public double? FanRpmMax { get; set; }

    [JsonPropertyName("fan_rpm_avg")]
    public double? FanRpmAvg { get; set; }

    [JsonPropertyName("disk_temp_max")]
    public double? DiskTempMax { get; set; }

    [JsonPropertyName("disk_activity_percent")]
    public double? DiskActivityPercent { get; set; }

    [JsonPropertyName("net_up_bps")]
    public double? NetUpBps { get; set; }

    [JsonPropertyName("net_down_bps")]
    public double? NetDownBps { get; set; }

    [JsonPropertyName("system_power_estimated")]
    public double? SystemPowerEstimated { get; set; }

    public static TelemetrySnapshot Empty(string deviceId, string hostname, string platform)
    {
        return new TelemetrySnapshot
        {
            DeviceId = deviceId,
            Hostname = hostname,
            Platform = platform,
            Timestamp = DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
            SourceOk = false
        };
    }
}
