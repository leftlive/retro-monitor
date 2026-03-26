namespace RetroMonitor.WindowsAgent.Models;

public sealed class SlowMetrics
{
    public double? CpuTemp { get; init; }
    public double? CpuClock { get; init; }
    public double? CpuPower { get; init; }
    public double? GpuTemp { get; init; }
    public double? GpuLoad { get; init; }
    public double? GpuClock { get; init; }
    public double? GpuPower { get; init; }
    public double? MemoryUsedMb { get; init; }
    public double? MemoryTotalMb { get; init; }
    public double? MemoryPercent { get; init; }
    public double? FanRpmMax { get; init; }
    public double? FanRpmAvg { get; init; }
    public double? DiskTempMax { get; init; }
    public double? SystemPowerEstimated { get; init; }
}
