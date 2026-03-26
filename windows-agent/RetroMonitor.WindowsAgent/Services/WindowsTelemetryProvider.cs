using System.Globalization;
using System.Runtime.Versioning;
using Microsoft.Extensions.Options;
using RetroMonitor.WindowsAgent.Configuration;
using RetroMonitor.WindowsAgent.Models;

namespace RetroMonitor.WindowsAgent.Services;

[SupportedOSPlatform("windows")]
public sealed class WindowsTelemetryProvider : IDisposable
{
    private readonly AgentOptions _options;
    private readonly HardwareMonitorReader _hardware;
    private readonly SystemMetricsReader _system;
    private readonly ILogger<WindowsTelemetryProvider> _logger;
    private readonly string _hostname;
    private readonly string _deviceId;
    private readonly object _gate = new();
    private SlowMetrics? _slowMetrics;
    private DateTimeOffset _slowAt;

    public WindowsTelemetryProvider(
        IOptions<AgentOptions> options,
        HardwareMonitorReader hardware,
        SystemMetricsReader system,
        ILogger<WindowsTelemetryProvider> logger)
    {
        _options = options.Value;
        _hardware = hardware;
        _system = system;
        _logger = logger;
        _hostname = Environment.MachineName;
        _deviceId = WindowsIdentityHelper.GetStableDeviceId(_hostname);
    }

    public Task<TelemetrySnapshot> SampleAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        var snapshot = TelemetrySnapshot.Empty(_deviceId, _hostname, _options.Platform);
        snapshot.Timestamp = DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture);

        var fast = _system.ReadFast();
        snapshot.CpuLoad = fast.CpuLoad;
        snapshot.DiskActivityPercent = fast.DiskActivityPercent;
        snapshot.NetUpBps = fast.NetUpBps;
        snapshot.NetDownBps = fast.NetDownBps;

        var slow = GetSlowMetrics();
        snapshot.CpuTemp = slow.CpuTemp;
        snapshot.CpuClock = slow.CpuClock;
        snapshot.CpuPower = slow.CpuPower;
        snapshot.GpuTemp = slow.GpuTemp;
        snapshot.GpuLoad = slow.GpuLoad;
        snapshot.GpuClock = slow.GpuClock;
        snapshot.GpuPower = slow.GpuPower;
        snapshot.MemoryUsedMb = slow.MemoryUsedMb;
        snapshot.MemoryTotalMb = slow.MemoryTotalMb;
        snapshot.MemoryPercent = slow.MemoryPercent;
        snapshot.FanRpmMax = slow.FanRpmMax;
        snapshot.FanRpmAvg = slow.FanRpmAvg;
        snapshot.DiskTempMax = slow.DiskTempMax;
        snapshot.SystemPowerEstimated = slow.SystemPowerEstimated;

        snapshot.SourceOk =
            HasValue(snapshot.CpuTemp) ||
            HasValue(snapshot.CpuLoad) ||
            HasValue(snapshot.GpuTemp) ||
            HasValue(snapshot.GpuLoad) ||
            HasValue(snapshot.MemoryPercent) ||
            HasValue(snapshot.NetUpBps) ||
            HasValue(snapshot.NetDownBps);

        return Task.FromResult(snapshot);
    }

    public void Dispose()
    {
        _hardware.Dispose();
        _system.Dispose();
    }

    private SlowMetrics GetSlowMetrics()
    {
        lock (_gate)
        {
            if (_slowMetrics is not null &&
                DateTimeOffset.UtcNow - _slowAt < TimeSpan.FromMilliseconds(Math.Max(500, _options.SlowIntervalMilliseconds)))
            {
                return _slowMetrics;
            }

            _slowMetrics = CollectSlowMetrics();
            _slowAt = DateTimeOffset.UtcNow;
            return _slowMetrics;
        }
    }

    private SlowMetrics CollectSlowMetrics()
    {
        var hardware = _hardware.ReadHardware();
        var memory = _system.ReadMemory();
        var systemPower = hardware.SystemPowerDirect;

        if (!HasValue(systemPower))
        {
            var estimate = (_options.SystemPowerBaseWatts) +
                           (hardware.CpuPower ?? 0) +
                           (hardware.GpuPower ?? 0);
            systemPower = estimate > 0 ? Round1(estimate) : null;
        }

        return new SlowMetrics
        {
            CpuTemp = hardware.CpuTemp,
            CpuClock = hardware.CpuClock,
            CpuPower = hardware.CpuPower,
            GpuTemp = hardware.GpuTemp,
            GpuLoad = hardware.GpuLoad,
            GpuClock = hardware.GpuClock,
            GpuPower = hardware.GpuPower,
            MemoryUsedMb = memory.MemoryUsedMb,
            MemoryTotalMb = memory.MemoryTotalMb,
            MemoryPercent = memory.MemoryPercent,
            FanRpmMax = hardware.FanRpmMax,
            FanRpmAvg = hardware.FanRpmAvg,
            DiskTempMax = hardware.DiskTempMax,
            SystemPowerEstimated = systemPower
        };
    }

    private static bool HasValue(double? value) => value.HasValue;

    private static double? Round1(double? value) => value.HasValue ? Math.Round(value.Value, 1) : null;
}
