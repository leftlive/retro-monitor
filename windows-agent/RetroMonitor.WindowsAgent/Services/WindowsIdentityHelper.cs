using Microsoft.Win32;

namespace RetroMonitor.WindowsAgent.Services;

public static class WindowsIdentityHelper
{
    private const string MachineGuidPath = @"SOFTWARE\Microsoft\Cryptography";
    private const string MachineGuidName = "MachineGuid";

    public static string GetStableDeviceId(string fallback)
    {
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(MachineGuidPath, false);
            var value = key?.GetValue(MachineGuidName) as string;
            if (!string.IsNullOrWhiteSpace(value))
            {
                return value;
            }
        }
        catch
        {
            // Fall back to hostname below.
        }

        return fallback;
    }
}
