import unittest

from retro_monitor_agent.providers.mock import MockTelemetryProvider
from retro_monitor_agent.schema import TELEMETRY_FIELDS, TelemetrySnapshot


class TelemetrySchemaTests(unittest.TestCase):
    def test_empty_snapshot_contains_all_fields(self) -> None:
        snapshot = TelemetrySnapshot.empty(device_id="dev-1", hostname="host-1", platform="macos_hackintosh")
        payload = snapshot.to_dict()
        self.assertEqual(tuple(payload.keys()), TELEMETRY_FIELDS)
        self.assertFalse(payload["source_ok"])
        self.assertIsNone(payload["cpu_temp"])

    def test_mock_provider_returns_complete_payload(self) -> None:
        payload = MockTelemetryProvider().sample().to_dict()
        self.assertEqual(tuple(payload.keys()), TELEMETRY_FIELDS)
        self.assertTrue(payload["source_ok"])
        self.assertEqual(payload["device_id"], "mock-device")
        self.assertEqual(payload["memory_total_mb"], 32768.0)


if __name__ == "__main__":
    unittest.main()
