namespace RetroMonitor.WindowsAgent.Configuration;

public sealed class AgentOptions
{
    public string Host { get; set; } = "0.0.0.0";
    public int Port { get; set; } = 8125;
    public string Platform { get; set; } = "windows";
    public int SampleIntervalMilliseconds { get; set; } = 500;
    public int SlowIntervalMilliseconds { get; set; } = 2000;
    public double SystemPowerBaseWatts { get; set; } = 20.0;
}
