from __future__ import annotations

import argparse
import json
import signal
import threading
import time
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


class TelemetrySampler:
    def __init__(self, provider: TelemetryProvider, interval: float) -> None:
        self._provider = provider
        self._interval = interval
        self._payload: Optional[dict] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="telemetry-sampler")

    def start(self) -> None:
        self.sample_once()
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=max(1.0, self._interval * 2))

    def sample_once(self) -> dict:
        payload = self._provider.sample().to_dict()
        with self._lock:
            self._payload = payload
        return payload

    def current_payload(self) -> Optional[dict]:
        with self._lock:
            if self._payload is None:
                return None
            return dict(self._payload)

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval):
            try:
                self.sample_once()
            except Exception:
                with self._lock:
                    if self._payload is None:
                        continue
                    degraded = dict(self._payload)
                    degraded["source_ok"] = False
                    self._payload = degraded


def create_handler(sampler: TelemetrySampler) -> type[BaseHTTPRequestHandler]:
    class TelemetryHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/telemetry":
                self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
                return

            payload = sampler.current_payload()
            if payload is None:
                self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Telemetry unavailable")
                return
            body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    return TelemetryHandler


def serve(provider: TelemetryProvider, host: str, port: int, sample_interval: float) -> None:
    sampler = TelemetrySampler(provider, sample_interval)
    sampler.start()
    server = ThreadingHTTPServer((host, port), create_handler(sampler))
    stop_event = threading.Event()

    def _shutdown(*_args: object) -> None:
        stop_event.set()
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    print(f"retro-monitor-agent serving on http://{host}:{port}/telemetry")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        sampler.stop()


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retro Monitor telemetry agent")
    parser.add_argument("--provider", choices=("mock", "macos"), default="mock")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8125, type=int)
    parser.add_argument("--sample-interval", default=0.5, type=float)
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    provider = build_provider(args.provider)
    serve(provider, args.host, args.port, args.sample_interval)
    return 0
