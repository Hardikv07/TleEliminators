from __future__ import annotations


class CityMonitorService:
    """Example observer that receives system events."""

    def __init__(self) -> None:
        self.events: list[str] = []

    def on_event(self, event) -> None:
        self.events.append(f"{event.name}:{event}")
