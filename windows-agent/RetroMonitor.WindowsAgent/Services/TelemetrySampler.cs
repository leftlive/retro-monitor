using Microsoft.Extensions.Options;
using RetroMonitor.WindowsAgent.Configuration;
using RetroMonitor.WindowsAgent.Models;

namespace RetroMonitor.WindowsAgent.Services;

public sealed class TelemetrySampler : BackgroundService
{
    private readonly WindowsTelemetryProvider _provider;
    private readonly ILogger<TelemetrySampler> _logger;
    private readonly TimeSpan _interval;
    private readonly object _gate = new();
    private TelemetrySnapshot? _snapshot;

    public TelemetrySampler(
        WindowsTelemetryProvider provider,
        IOptions<AgentOptions> options,
        ILogger<TelemetrySampler> logger)
    {
        _provider = provider;
        _logger = logger;
        _interval = TimeSpan.FromMilliseconds(Math.Max(100, options.Value.SampleIntervalMilliseconds));
    }

    public TelemetrySnapshot? Current()
    {
        lock (_gate)
        {
            return _snapshot is null
                ? null
                : Clone(_snapshot);
        }
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await SampleOnce(stoppingToken);

        using var timer = new PeriodicTimer(_interval);
        while (!stoppingToken.IsCancellationRequested && await timer.WaitForNextTickAsync(stoppingToken))
        {
            await SampleOnce(stoppingToken);
        }
    }

    private async Task SampleOnce(CancellationToken cancellationToken)
    {
        try
        {
            var snapshot = await _provider.SampleAsync(cancellationToken);
            lock (_gate)
            {
                _snapshot = snapshot;
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "retro-monitor windows sampler failed");
            lock (_gate)
            {
                if (_snapshot is not null)
                {
                    _snapshot.SourceOk = false;
                    _snapshot.Timestamp = DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");
                }
            }
        }
    }

    private static TelemetrySnapshot Clone(TelemetrySnapshot source)
    {
        return new TelemetrySnapshot
        {
            DeviceId = source.DeviceId,
            Hostname = source.Hostname,
            Platform = source.Platform,
            Timestamp = source.Timestamp,
            SourceOk = source.SourceOk,
            CpuTemp = source.CpuTemp,
            CpuLoad = source.CpuLoad,
            CpuClock = source.CpuClock,
            CpuPower = source.CpuPower,
            GpuTemp = source.GpuTemp,
            GpuLoad = source.GpuLoad,
            GpuClock = source.GpuClock,
            GpuPower = source.GpuPower,
            MemoryUsedMb = source.MemoryUsedMb,
            MemoryTotalMb = source.MemoryTotalMb,
            MemoryPercent = source.MemoryPercent,
            FanRpmMax = source.FanRpmMax,
            FanRpmAvg = source.FanRpmAvg,
            DiskTempMax = source.DiskTempMax,
            DiskActivityPercent = source.DiskActivityPercent,
            NetUpBps = source.NetUpBps,
            NetDownBps = source.NetDownBps,
            SystemPowerEstimated = source.SystemPowerEstimated
        };
    }
}
