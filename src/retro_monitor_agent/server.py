from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import List, Optional

from retro_monitor_agent.providers import MacOSTelemetryProvider, MockTelemetryProvider, TelemetryProvider


def build_provider(name: str) -> TelemetryProvider:
    if name == "mock":
        return MockTelemetryProvider()
    if name == "macos":
        return MacOSTelemetryProvider()
    raise ValueError(f"unsupported provider: {name}")


def create_handler(provider: TelemetryProvider) -> type[BaseHTTPRequestHandler]:
    class TelemetryHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/telemetry":
                self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
                return

            payload = provider.sample().to_dict()
            body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    return TelemetryHandler


def serve(provider: TelemetryProvider, host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), create_handler(provider))
    print(f"retro-monitor-agent serving on http://{host}:{port}/telemetry")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retro Monitor telemetry agent")
    parser.add_argument("--provider", choices=("mock", "macos"), default="mock")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8125, type=int)
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    provider = build_provider(args.provider)
    serve(provider, args.host, args.port)
    return 0
