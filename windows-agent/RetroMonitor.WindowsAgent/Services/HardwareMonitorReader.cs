using System.Text.Json;
using LibreHardwareMonitor.Hardware;
using RetroMonitor.WindowsAgent.Models;

namespace RetroMonitor.WindowsAgent.Services;

public sealed class HardwareMonitorReader : IDisposable
{
    private readonly Computer _computer;
    private readonly object _gate = new();

    public HardwareMonitorReader()
    {
        _computer = new Computer
        {
            IsCpuEnabled = true,
            IsGpuEnabled = true,
            IsMemoryEnabled = true,
            IsMotherboardEnabled = true,
            IsControllerEnabled = true,
            IsNetworkEnabled = true,
            IsStorageEnabled = true
        };

        _computer.Open();
    }

    public HardwareSnapshot ReadHardware()
    {
        lock (_gate)
        {
            var sensors = SnapshotSensors();
            var cpuTemp = PickCpuTemperature(sensors);
            var cpuClock = PickCpuClock(sensors);
            var cpuPower = PickCpuPower(sensors);
            var gpuTemp = PickGpuMetric(sensors, "Temperature", "GPU Core", "Core");
            var gpuLoad = PickGpuMetric(sensors, "Load", "Core", "D3D", "GPU Core");
            var gpuClock = PickGpuMetric(sensors, "Clock", "Core");
            var gpuPower = PickGpuMetric(sensors, "Power", "Total", "Board", "Package");
            var fans = sensors.Where(IsFanSensor).Select(s => s.Value!.Value).ToArray();
            var diskTemp = sensors
                .Where(IsStorageTemperatureSensor)
                .Select(s => s.Value!.Value)
                .DefaultIfEmpty()
                .Max();
            var directSystemPower = sensors
                .Where(s => IsSensorType(s, "Power") && HasNamePart(s, "System", "Total", "Input"))
                .Select(s => s.Value!.Value)
                .DefaultIfEmpty()
                .Max();

            return new HardwareSnapshot
            {
                CpuTemp = Round1(cpuTemp),
                CpuClock = Round1(cpuClock),
                CpuPower = Round1(cpuPower),
                GpuTemp = Round1(gpuTemp),
                GpuLoad = Round1(gpuLoad),
                GpuClock = Round1(gpuClock),
                GpuPower = Round1(gpuPower),
                FanRpmMax = fans.Length > 0 ? Round1(fans.Max()) : null,
                FanRpmAvg = fans.Length > 0 ? Round1(fans.Average()) : null,
                DiskTempMax = diskTemp > 0 ? Round1(diskTemp) : null,
                SystemPowerDirect = directSystemPower > 0 ? Round1(directSystemPower) : null
            };
        }
    }

    public string DumpSensorsJson()
    {
        lock (_gate)
        {
            var sensors = SnapshotSensors()
                .Select(sensor => new SensorDump
                {
                    HardwareType = sensor.HardwareType,
                    HardwareName = sensor.HardwareName,
                    SensorType = sensor.SensorType,
                    SensorName = sensor.SensorName,
                    Identifier = sensor.Identifier,
                    Value = sensor.Value.HasValue ? Math.Round(sensor.Value.Value, 2) : null
                })
                .OrderBy(sensor => sensor.HardwareType)
                .ThenBy(sensor => sensor.HardwareName)
                .ThenBy(sensor => sensor.SensorType)
                .ThenBy(sensor => sensor.SensorName)
                .ToArray();

            return JsonSerializer.Serialize(sensors, new JsonSerializerOptions
            {
                WriteIndented = true
            });
        }
    }

    public void Dispose()
    {
        _computer.Close();
    }

    private List<RawSensor> SnapshotSensors()
    {
        var sensors = new List<RawSensor>();

        foreach (var hardware in _computer.Hardware)
        {
            UpdateRecursive(hardware);
            CollectRecursive(hardware, sensors);
        }

        return sensors;
    }

    private static void UpdateRecursive(IHardware hardware)
    {
        hardware.Update();
        foreach (var sub in hardware.SubHardware)
        {
            UpdateRecursive(sub);
        }
    }

    private static void CollectRecursive(IHardware hardware, List<RawSensor> sensors)
    {
        sensors.AddRange(hardware.Sensors.Select(sensor => new RawSensor(
            hardware.HardwareType.ToString(),
            hardware.Name,
            sensor.SensorType.ToString(),
            sensor.Name,
            sensor.Identifier.ToString(),
            sensor.Value)));

        foreach (var sub in hardware.SubHardware)
        {
            CollectRecursive(sub, sensors);
        }
    }

    private static double? PickCpuTemperature(IEnumerable<RawSensor> sensors)
    {
        var preferred = sensors
            .Where(s => IsCpuSensor(s) && IsSensorType(s, "Temperature") && HasNamePart(s, "Package", "Tctl", "Tdie"))
            .Select(s => s.Value!.Value)
            .ToArray();

        if (preferred.Length > 0)
        {
            return preferred.Max();
        }

        return MaxOrNull(sensors
            .Where(s => IsCpuSensor(s) && IsSensorType(s, "Temperature"))
            .Select(s => s.Value!.Value));
    }

    private static double? PickCpuClock(IEnumerable<RawSensor> sensors)
    {
        var preferred = sensors
            .Where(s => IsCpuSensor(s) && IsSensorType(s, "Clock") && HasNamePart(s, "Core Average", "Bus Speed", "Effective Clock"))
            .Select(s => s.Value!.Value)
            .ToArray();

        if (preferred.Length > 0)
        {
            return preferred.Max();
        }

        return MaxOrNull(sensors
            .Where(s => IsCpuSensor(s) && IsSensorType(s, "Clock"))
            .Select(s => s.Value!.Value));
    }

    private static double? PickCpuPower(IEnumerable<RawSensor> sensors)
    {
        var preferred = sensors
            .Where(s => IsCpuSensor(s) && IsSensorType(s, "Power") && HasNamePart(s, "Package", "CPU Package", "Total"))
            .Select(s => s.Value!.Value)
            .ToArray();

        if (preferred.Length > 0)
        {
            return preferred.Max();
        }

        return MaxOrNull(sensors
            .Where(s => IsCpuSensor(s) && IsSensorType(s, "Power"))
            .Select(s => s.Value!.Value));
    }

    private static double? PickGpuMetric(IEnumerable<RawSensor> sensors, string sensorType, params string[] preferredNames)
    {
        var candidates = sensors.Where(s => IsGpuSensor(s) && IsSensorType(s, sensorType)).ToArray();
        if (candidates.Length == 0)
        {
            return null;
        }

        if (preferredNames.Length > 0)
        {
            var preferred = candidates
                .Where(s => HasNamePart(s, preferredNames))
                .Select(s => s.Value!.Value)
                .ToArray();

            if (preferred.Length > 0)
            {
                return preferred.Max();
            }
        }

        return MaxOrNull(candidates.Select(s => s.Value!.Value));
    }

    private static bool IsCpuSensor(RawSensor sensor) => sensor.HardwareType == "Cpu";

    private static bool IsGpuSensor(RawSensor sensor) =>
        sensor.HardwareType is "GpuNvidia" or "GpuAmd" or "GpuIntel";

    private static bool IsFanSensor(RawSensor sensor) =>
        IsSensorType(sensor, "Fan") && sensor.Value.HasValue;

    private static bool IsStorageTemperatureSensor(RawSensor sensor) =>
        sensor.HardwareType == "Storage" && IsSensorType(sensor, "Temperature") && sensor.Value.HasValue;

    private static bool IsSensorType(RawSensor sensor, string type) =>
        sensor.SensorType.Equals(type, StringComparison.OrdinalIgnoreCase) && sensor.Value.HasValue;

    private static bool HasNamePart(RawSensor sensor, params string[] parts) =>
        parts.Any(part => sensor.SensorName.Contains(part, StringComparison.OrdinalIgnoreCase));

    private static double? Round1(double? value) => value.HasValue ? Math.Round(value.Value, 1) : null;

    private static double? MaxOrNull(IEnumerable<float> values)
    {
        var snapshot = values.ToArray();
        return snapshot.Length > 0 ? snapshot.Max() : null;
    }

    private sealed record RawSensor(
        string HardwareType,
        string HardwareName,
        string SensorType,
        string SensorName,
        string Identifier,
        float? Value);
}
