import json
import threading
import time
import unittest
from urllib.request import urlopen

from retro_monitor_agent.providers.mock import MockTelemetryProvider
from http.server import ThreadingHTTPServer

from retro_monitor_agent.providers.base import TelemetryProvider
from retro_monitor_agent.schema import TELEMETRY_FIELDS
from retro_monitor_agent.server import TelemetrySampler, create_handler


class IncrementingProvider(TelemetryProvider):
    def __init__(self) -> None:
        self.calls = 0

    def sample(self):
        self.calls += 1
        return MockTelemetryProvider().sample().__class__(
            **{
                **MockTelemetryProvider().sample().to_dict(),
                "cpu_load": float(self.calls),
            }
        )


class TelemetryServerTests(unittest.TestCase):
    def test_telemetry_endpoint_serves_json(self) -> None:
        sampler = TelemetrySampler(MockTelemetryProvider(), 1.0)
        sampler.start()
        server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(sampler))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.05)

        try:
            with urlopen(f"http://127.0.0.1:{server.server_port}/telemetry") as response:
                self.assertEqual(response.status, 200)
                payload = json.loads(response.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
            sampler.stop()
            thread.join(timeout=1)

        self.assertEqual(tuple(payload.keys()), TELEMETRY_FIELDS)
        self.assertEqual(payload["platform"], "mock")

    def test_requests_reuse_cached_snapshot(self) -> None:
        provider = IncrementingProvider()
        sampler = TelemetrySampler(provider, 10.0)
        sampler.start()
        server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(sampler))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.05)

        try:
            with urlopen(f"http://127.0.0.1:{server.server_port}/telemetry") as response:
                first = json.loads(response.read().decode("utf-8"))
            with urlopen(f"http://127.0.0.1:{server.server_port}/telemetry") as response:
                second = json.loads(response.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
            sampler.stop()
            thread.join(timeout=1)

        self.assertEqual(first["cpu_load"], second["cpu_load"])
        self.assertEqual(provider.calls, 1)

    def test_sampler_refreshes_in_background(self) -> None:
        provider = IncrementingProvider()
        sampler = TelemetrySampler(provider, 0.1)
        sampler.start()
        first = sampler.current_payload()
        time.sleep(0.25)
        second = sampler.current_payload()
        sampler.stop()

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertNotEqual(first["cpu_load"], second["cpu_load"])
        self.assertGreaterEqual(provider.calls, 2)


if __name__ == "__main__":
    unittest.main()
