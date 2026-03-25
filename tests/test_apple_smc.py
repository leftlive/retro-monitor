import unittest

from retro_monitor_agent.apple_smc import _decode_numeric


class AppleSMCTests(unittest.TestCase):
    def test_decode_sp96(self) -> None:
        self.assertAlmostEqual(_decode_numeric(bytes.fromhex("0e84"), "sp96"), 58.0625)

    def test_decode_sp78(self) -> None:
        self.assertAlmostEqual(_decode_numeric(bytes.fromhex("3200"), "sp78"), 50.0)

    def test_decode_float(self) -> None:
        self.assertAlmostEqual(_decode_numeric(bytes.fromhex("b72b3442"), "flt "), 45.04269027709961)


if __name__ == "__main__":
    unittest.main()
