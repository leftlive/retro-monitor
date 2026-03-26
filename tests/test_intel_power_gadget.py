import unittest
from unittest.mock import Mock, patch
from typing import Optional

from retro_monitor_agent.intel_power_gadget import IntelPowerGadget


class IntelPowerGadgetTests(unittest.TestCase):
    def test_platform_power_returns_none_when_platform_energy_unavailable(self) -> None:
        fake_library = self._fake_library(platform_available=False)

        with patch("retro_monitor_agent.intel_power_gadget.os.path.exists", return_value=True):
            with patch("retro_monitor_agent.intel_power_gadget.ctypes.cdll.LoadLibrary", return_value=fake_library):
                gadget = IntelPowerGadget()
                self.assertIsNone(gadget.platform_power())
                gadget.close()

    def test_platform_power_requires_two_samples(self) -> None:
        fake_library = self._fake_library(platform_available=True, power=123.4)

        with patch("retro_monitor_agent.intel_power_gadget.os.path.exists", return_value=True):
            with patch("retro_monitor_agent.intel_power_gadget.ctypes.cdll.LoadLibrary", return_value=fake_library):
                gadget = IntelPowerGadget()
                self.assertIsNone(gadget.platform_power())
                self.assertAlmostEqual(gadget.platform_power(), 123.4)
                gadget.close()

    def _fake_library(self, *, platform_available: bool, power: Optional[float] = None):
        sample_ids = iter([101, 202, 303])

        def pg_initialize():
            return True

        def pg_shutdown():
            return True

        def pg_is_platform_energy_available(_package_index, available_ptr):
            available_ptr._obj.value = platform_available
            return True

        def pg_read_sample(_package_index, sample_ptr):
            sample_ptr._obj.value = next(sample_ids)
            return True

        def pg_sample_release(_sample_id):
            return True

        def pg_sample_get_platform_power(_sample1, _sample2, power_ptr, energy_ptr):
            if power is None:
                return False
            power_ptr._obj.value = power
            energy_ptr._obj.value = 1.0
            return True

        library = Mock()
        library.PG_Initialize = Mock(side_effect=pg_initialize)
        library.PG_Shutdown = Mock(side_effect=pg_shutdown)
        library.PG_IsPlatformEnergyAvailable = Mock(side_effect=pg_is_platform_energy_available)
        library.PG_ReadSample = Mock(side_effect=pg_read_sample)
        library.PGSample_Release = Mock(side_effect=pg_sample_release)
        library.PGSample_GetPlatformPower = Mock(side_effect=pg_sample_get_platform_power)
        return library


if __name__ == "__main__":
    unittest.main()
