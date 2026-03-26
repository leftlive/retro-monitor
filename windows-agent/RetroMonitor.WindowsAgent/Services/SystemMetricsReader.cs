using System.Diagnostics;
using System.Net.NetworkInformation;
using System.Runtime.InteropServices;
using RetroMonitor.WindowsAgent.Models;

namespace RetroMonitor.WindowsAgent.Services;

public sealed class SystemMetricsReader : IDisposable
{
    private readonly PerformanceCounter? _cpuCounter;
    private readonly PerformanceCounter? _diskCounter;
    private readonly object _gate = new();
    private long _lastBytesSent;
    private long _lastBytesRecv;
    private DateTimeOffset _lastNetAt;
    private bool _netPrimed;

    public SystemMetricsReader()
    {
        _cpuCounter = CreateCounter("Processor", "% Processor Time", "_Total");
        _diskCounter = CreateCounter("PhysicalDisk", "% Disk Time", "_Total");
        _ = _cpuCounter?.NextValue();
        _ = _diskCounter?.NextValue();
    }

    public SystemSnapshot ReadFast()
    {
        var memory = ReadMemory();
        var cpu = ReadCounter(_cpuCounter);
        var disk = ClampPercent(ReadCounter(_diskCounter));
        var (up, down) = ReadNetworkRates();

        return new SystemSnapshot
        {
            CpuLoad = cpu,
            MemoryUsedMb = memory.MemoryUsedMb,
            MemoryTotalMb = memory.MemoryTotalMb,
            MemoryPercent = memory.MemoryPercent,
            DiskActivityPercent = disk,
            NetUpBps = up,
            NetDownBps = down
        };
    }

    public SystemSnapshot ReadMemory()
    {
        var status = new MEMORYSTATUSEX();
        status.dwLength = (uint)Marshal.SizeOf<MEMORYSTATUSEX>();

        if (!GlobalMemoryStatusEx(ref status))
        {
            return new SystemSnapshot();
        }

        var totalMb = status.ullTotalPhys / 1024.0 / 1024.0;
        var availMb = status.ullAvailPhys / 1024.0 / 1024.0;
        var usedMb = totalMb - availMb;
        var usedPercent = totalMb > 0 ? (usedMb / totalMb) * 100.0 : 0;

        return new SystemSnapshot
        {
            MemoryUsedMb = Round1(usedMb),
            MemoryTotalMb = Round1(totalMb),
            MemoryPercent = Round1(usedPercent)
        };
    }

    public void Dispose()
    {
        _cpuCounter?.Dispose();
        _diskCounter?.Dispose();
    }

    private (double? up, double? down) ReadNetworkRates()
    {
        lock (_gate)
        {
            long bytesSent = 0;
            long bytesRecv = 0;

            foreach (var nic in NetworkInterface.GetAllNetworkInterfaces())
            {
                if (nic.OperationalStatus != OperationalStatus.Up)
                {
                    continue;
                }

                if (nic.NetworkInterfaceType is NetworkInterfaceType.Loopback or NetworkInterfaceType.Tunnel)
                {
                    continue;
                }

                try
                {
                    var stats = nic.GetIPv4Statistics();
                    bytesSent += stats.BytesSent;
                    bytesRecv += stats.BytesReceived;
                }
                catch
                {
                    // Ignore interfaces without IPv4 stats.
                }
            }

            var now = DateTimeOffset.UtcNow;
            if (_netPrimed)
            {
                var elapsedSeconds = (now - _lastNetAt).TotalSeconds;
                if (elapsedSeconds > 0)
                {
                    var up = Math.Max(0, bytesSent - _lastBytesSent) * 8.0 / elapsedSeconds;
                    var down = Math.Max(0, bytesRecv - _lastBytesRecv) * 8.0 / elapsedSeconds;
                    _lastBytesSent = bytesSent;
                    _lastBytesRecv = bytesRecv;
                    _lastNetAt = now;
                    return (Round1(up), Round1(down));
                }
            }

            _lastBytesSent = bytesSent;
            _lastBytesRecv = bytesRecv;
            _lastNetAt = now;
            _netPrimed = true;
            return (null, null);
        }
    }

    private static PerformanceCounter? CreateCounter(string category, string counter, string instance)
    {
        try
        {
            return new PerformanceCounter(category, counter, instance);
        }
        catch
        {
            return null;
        }
    }

    private static double? ReadCounter(PerformanceCounter? counter)
    {
        if (counter is null)
        {
            return null;
        }

        try
        {
            return Round1(counter.NextValue());
        }
        catch
        {
            return null;
        }
    }

    private static double? ClampPercent(double? value)
    {
        if (!value.HasValue)
        {
            return null;
        }

        return Round1(Math.Clamp(value.Value, 0, 100));
    }

    private static double? Round1(double value) => Math.Round(value, 1);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GlobalMemoryStatusEx(ref MEMORYSTATUSEX lpBuffer);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    private struct MEMORYSTATUSEX
    {
        public uint dwLength;
        public uint dwMemoryLoad;
        public ulong ullTotalPhys;
        public ulong ullAvailPhys;
        public ulong ullTotalPageFile;
        public ulong ullAvailPageFile;
        public ulong ullTotalVirtual;
        public ulong ullAvailVirtual;
        public ulong ullAvailExtendedVirtual;
    }
}
