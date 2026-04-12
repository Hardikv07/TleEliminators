from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import random


class DispenserInterface(ABC):
    @abstractmethod
    def dispense(self, product_id: str, quantity: int) -> bool:
        raise NotImplementedError


class MockDispenser(DispenserInterface):
    def __init__(self, fail_rate: float = 0.0, name: str = "StandardDispenser") -> None:
        self.fail_rate = fail_rate
        self.name = name

    def dispense(self, product_id: str, quantity: int) -> bool:
        return random.random() >= self.fail_rate


class SensorManager:
    def __init__(self) -> None:
        self.health_ok = True

    def set_health(self, ok: bool) -> None:
        self.health_ok = ok

    def diagnostics(self) -> dict[str, str]:
        return {"sensors": "OK" if self.health_ok else "FAULT"}


@dataclass
class FailureContext:
    product_id: str
    quantity: int
    attempts: int = 0
    resolved: bool = False
    message: str = ""


class FailureHandler(ABC):
    def __init__(self, next_handler: "FailureHandler | None" = None) -> None:
        self.next_handler = next_handler

    def set_next(self, next_handler: "FailureHandler") -> "FailureHandler":
        self.next_handler = next_handler
        return next_handler

    def handle(self, context: FailureContext) -> bool:
        if self.can_handle(context):
            self.process(context)
            if context.resolved:
                return True
        if self.next_handler:
            return self.next_handler.handle(context)
        return context.resolved

    @abstractmethod
    def can_handle(self, context: FailureContext) -> bool:
        raise NotImplementedError

    @abstractmethod
    def process(self, context: FailureContext) -> None:
        raise NotImplementedError


class RetryHandler(FailureHandler):
    def can_handle(self, context: FailureContext) -> bool:
        return context.attempts < 1

    def process(self, context: FailureContext) -> None:
        context.attempts += 1
        # Deterministic demo behavior: recover immediately for p1, fail otherwise.
        context.resolved = context.product_id == "p1"
        context.message = "Auto-retry succeeded" if context.resolved else "Auto-retry failed"


class RecalibrationHandler(FailureHandler):
    def can_handle(self, context: FailureContext) -> bool:
        return not context.resolved

    def process(self, context: FailureContext) -> None:
        # Deterministic fallback: p1 can be recalibrated successfully, others fail.
        context.resolved = context.product_id == "p1"
        context.message = "Recalibration succeeded" if context.resolved else "Recalibration failed"


class TechnicianAlertHandler(FailureHandler):
    def can_handle(self, context: FailureContext) -> bool:
        return True

    def process(self, context: FailureContext) -> None:
        context.resolved = False
        context.message = "Technician alert issued"


class HardwareMonitor:
    def __init__(self, sensor_manager: SensorManager, handler_chain: FailureHandler) -> None:
        self.sensor_manager = sensor_manager
        self.handler_chain = handler_chain

    def diagnostics(self) -> dict[str, str]:
        return self.sensor_manager.diagnostics()

    def resolve_failure(self, product_id: str, quantity: int) -> FailureContext:
        context = FailureContext(product_id=product_id, quantity=quantity)
        self.handler_chain.handle(context)
        return context
