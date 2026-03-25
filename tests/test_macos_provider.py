import unittest
from unittest.mock import patch

from retro_monitor_agent.providers.macos import _mounted_bsd_names


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


if __name__ == "__main__":
    unittest.main()
