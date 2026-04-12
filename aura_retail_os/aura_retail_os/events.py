from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, DefaultDict, List, Tuple, Type


@dataclass(frozen=True)
class Event:
    """Base event type."""
    name: str


@dataclass(frozen=True)
class LowStockEvent(Event):
    product_id: str
    current_stock: int

    def __init__(self, product_id: str, current_stock: int) -> None:
        object.__setattr__(self, "name", "LowStockEvent")
        object.__setattr__(self, "product_id", product_id)
        object.__setattr__(self, "current_stock", current_stock)


@dataclass(frozen=True)
class HardwareFailureEvent(Event):
    module_name: str
    reason: str

    def __init__(self, module_name: str, reason: str) -> None:
        object.__setattr__(self, "name", "HardwareFailureEvent")
        object.__setattr__(self, "module_name", module_name)
        object.__setattr__(self, "reason", reason)


@dataclass(frozen=True)
class EmergencyModeActivated(Event):
    reason: str

    def __init__(self, reason: str) -> None:
        object.__setattr__(self, "name", "EmergencyModeActivated")
        object.__setattr__(self, "reason", reason)


@dataclass(frozen=True)
class TransactionCompleted(Event):
    transaction_id: str

    def __init__(self, transaction_id: str) -> None:
        object.__setattr__(self, "name", "TransactionCompleted")
        object.__setattr__(self, "transaction_id", transaction_id)


@dataclass(frozen=True)
class TransactionFailed(Event):
    transaction_id: str
    reason: str

    def __init__(self, transaction_id: str, reason: str) -> None:
        object.__setattr__(self, "name", "TransactionFailed")
        object.__setattr__(self, "transaction_id", transaction_id)
        object.__setattr__(self, "reason", reason)


Subscriber = Callable[[Event], None]


class EventBus:
    """Simple priority-aware event bus (Observer pattern)."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[Type[Event], List[Tuple[int, Subscriber]]] = defaultdict(list)

    def subscribe(self, event_type: Type[Event], handler: Subscriber, priority: int = 0) -> None:
        self._subscribers[event_type].append((priority, handler))
        self._subscribers[event_type].sort(key=lambda item: item[0], reverse=True)

    def publish(self, event: Event) -> None:
        for etype, handlers in self._subscribers.items():
            if isinstance(event, etype):
                for _, handler in handlers:
                    handler(event)

    def clear(self) -> None:
        self._subscribers.clear()
