from __future__ import annotations

from abc import ABC, abstractmethod

from retro_monitor_agent.schema import TelemetrySnapshot


class TelemetryProvider(ABC):
    @abstractmethod
    def sample(self) -> TelemetrySnapshot:
        """Return a complete telemetry snapshot."""

