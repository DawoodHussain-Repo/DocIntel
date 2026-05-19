"""Local Chroma telemetry shim to disable broken product telemetry calls."""

from __future__ import annotations

from chromadb.telemetry.product import ProductTelemetryClient, ProductTelemetryEvent
from overrides import override


class NoOpProductTelemetryClient(ProductTelemetryClient):
    """Drop Chroma product telemetry events to keep server logs clean."""

    @override
    def capture(self, event: ProductTelemetryEvent) -> None:
        return None
