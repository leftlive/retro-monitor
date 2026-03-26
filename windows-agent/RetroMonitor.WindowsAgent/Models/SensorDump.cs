namespace RetroMonitor.WindowsAgent.Models;

public sealed class SensorDump
{
    public string HardwareType { get; init; } = string.Empty;
    public string HardwareName { get; init; } = string.Empty;
    public string SensorType { get; init; } = string.Empty;
    public string SensorName { get; init; } = string.Empty;
    public string Identifier { get; init; } = string.Empty;
    public double? Value { get; init; }
}
