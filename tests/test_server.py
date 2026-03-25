import json
import threading
import time
import unittest
from urllib.request import urlopen

from retro_monitor_agent.providers.mock import MockTelemetryProvider
from http.server import ThreadingHTTPServer

from retro_monitor_agent.schema import TELEMETRY_FIELDS
from retro_monitor_agent.server import create_handler


class TelemetryServerTests(unittest.TestCase):
    def test_telemetry_endpoint_serves_json(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(MockTelemetryProvider()))
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
            thread.join(timeout=1)

        self.assertEqual(tuple(payload.keys()), TELEMETRY_FIELDS)
        self.assertEqual(payload["platform"], "mock")


if __name__ == "__main__":
    unittest.main()
