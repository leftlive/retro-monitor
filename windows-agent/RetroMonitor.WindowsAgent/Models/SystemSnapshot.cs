namespace RetroMonitor.WindowsAgent.Models;

public sealed class SystemSnapshot
{
    public double? CpuLoad { get; init; }
    public double? MemoryUsedMb { get; init; }
    public double? MemoryTotalMb { get; init; }
    public double? MemoryPercent { get; init; }
    public double? DiskActivityPercent { get; init; }
    public double? NetUpBps { get; init; }
    public double? NetDownBps { get; init; }
}
