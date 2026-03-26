import unittest
from unittest.mock import patch

from retro_monitor_agent.providers.macos import _estimate_system_power, _mounted_bsd_names


class MacOSTelemetryProviderTests(unittest.TestCase):
    def test_mounted_bsd_names_filters_and_deduplicates_devices(self) -> None:
        partitions = [
            type("Partition", (), {"device": "/dev/disk3s4s1"})(),
            type("Partition", (), {"device": "/dev/disk3s4s1"})(),
            type("Partition", (), {"device": "/dev/disk2s3"})(),
            type("Partition", (), {"device": "map auto_home"})(),
        ]

        with patch("retro_monitor_agent.providers.macos.psutil.disk_partitions", return_value=partitions):
            self.assertEqual(_mounted_bsd_names(), ["disk3s4s1", "disk2s3"])

    def test_system_power_uses_direct_value_when_available(self) -> None:
        self.assertEqual(_estimate_system_power(60.0, 40.0, 123.4), 123.4)

    def test_system_power_falls_back_to_conservative_estimate(self) -> None:
        self.assertEqual(_estimate_system_power(60.0, 40.0, None), 120.0)
        self.assertEqual(_estimate_system_power(60.0, None, None), 80.0)
        self.assertIsNone(_estimate_system_power(None, None, None))


if __name__ == "__main__":
    unittest.main()
