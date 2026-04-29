"""
All 8 Design Patterns for Aura Retail OS.
Each pattern is clearly separated and easy to explain in a viva.
"""
import copy
import json
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable, List, Tuple, Type, Any


# ============================================================
# 1. STRATEGY PATTERN - Dynamic Pricing
# ============================================================

class PricingStrategy(ABC):
    """Base class for pricing strategies."""
    @abstractmethod
    def calculate(self, base_price: float, quantity: int) -> float:
        pass

class StandardPricing(PricingStrategy):
    """Normal pricing - no modification."""
    def calculate(self, base_price: float, quantity: int) -> float:
        return round(base_price * quantity, 2)

class DiscountPricing(PricingStrategy):
    """15% discount on all items."""
    def calculate(self, base_price: float, quantity: int) -> float:
        return round(base_price * quantity * 0.85, 2)

class EmergencyPricing(PricingStrategy):
    """10% markup during emergencies."""
    def calculate(self, base_price: float, quantity: int) -> float:
        return round(base_price * quantity * 1.10, 2)


# ============================================================
# 2. STATE PATTERN - Kiosk Operating Modes
# ============================================================

class KioskMode(ABC):
    """Base class for kiosk operating modes."""
    name = "Unknown"

    @abstractmethod
    def can_purchase(self):
        """Returns (allowed: bool, reason: str)."""
        pass

class ActiveMode(KioskMode):
    name = "active"
    def can_purchase(self):
        return True, "Purchases allowed"

class PowerSavingMode(KioskMode):
    name = "power_saving"
    def can_purchase(self):
        return False, "Kiosk is in power-saving mode. Customer operations suspended."

class MaintenanceMode(KioskMode):
    name = "maintenance"
    def can_purchase(self):
        return False, "Kiosk is under maintenance"

class EmergencyMode(KioskMode):
    name = "emergency"
    def can_purchase(self):
        return True, "Emergency: limited to 2 essential items"


# ============================================================
# 3. COMMAND PATTERN - Transactions
# ============================================================

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass
    @abstractmethod
    def undo(self):
        pass

class PurchaseCommand(Command):
    """Executes a purchase operation."""
    def __init__(self, kiosk, product_id, quantity, user_id="USER001"):
        self.kiosk = kiosk
        self.product_id = product_id
        self.quantity = quantity
        self.user_id = user_id
        self.result = None

    def execute(self):
        self.result = self.kiosk._do_purchase(self.product_id, self.quantity, self.user_id)
        return self.result

    def undo(self):
        return self.kiosk._undo_last()

class RefundCommand(Command):
    """Executes a refund operation."""
    def __init__(self, kiosk, transaction_id):
        self.kiosk = kiosk
        self.transaction_id = transaction_id

    def execute(self):
        return self.kiosk._do_refund(self.transaction_id)

    def undo(self):
        return None

class RestockCommand(Command):
    """Executes a restock operation."""
    def __init__(self, kiosk, product_id, quantity):
        self.kiosk = kiosk
        self.product_id = product_id
        self.quantity = quantity

    def execute(self):
        return self.kiosk._do_restock(self.product_id, self.quantity)

    def undo(self):
        return self.kiosk._undo_last()


# ============================================================
# 4. OBSERVER PATTERN - Event System (Priority-Aware)
# ============================================================

class EventManager:
    """Priority-aware publish/subscribe event system.
    Higher-priority handlers execute first (e.g. emergency events)."""

    def __init__(self):
        self._subscribers = {}      # event_type -> [(priority, handler), ...]
        self._log = []

    def subscribe(self, event_type: str, handler: Callable, priority: int = 0):
        """Subscribe to an event. Higher priority = executed first."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append((priority, handler))
        # Sort descending so high-priority runs first
        self._subscribers[event_type].sort(key=lambda x: x[0], reverse=True)

    def publish(self, event_type: str, data: dict = None):
        """Publish an event. All subscribers are notified in priority order."""
        entry = {"type": event_type, "data": data or {}}
        self._log.append(entry)
        for _, handler in self._subscribers.get(event_type, []):
            handler(data)

    def get_log(self):
        return self._log[-50:]

    def clear(self):
        self._subscribers.clear()
        self._log.clear()


# ============================================================
# 5. MEMENTO PATTERN - Inventory Rollback
# ============================================================

class InventoryMemento:
    """Stores a snapshot of inventory state."""
    def __init__(self, state):
        self._state = copy.deepcopy(state)

    def get_state(self):
        return copy.deepcopy(self._state)


class MementoManager:
    """Manages save/restore of inventory snapshots."""
    def __init__(self):
        self._snapshots = []

    def save(self, inventory_dict):
        mem = InventoryMemento(inventory_dict)
        self._snapshots.append(mem)
        return mem

    def restore(self):
        if self._snapshots:
            return self._snapshots.pop().get_state()
        return None

    def has_snapshot(self):
        return len(self._snapshots) > 0

    def count(self):
        return len(self._snapshots)


# ============================================================
# 6. FACTORY PATTERN - Kiosk Creation
# ============================================================

class KioskFactory:
    """Creates different types of kiosks with preset inventory."""

    PRESETS = {
        "pharmacy": {
            "id": "pharmacy-01", "location": "City Hospital",
            "products": ["p1", "p2"]
        },
        "food": {
            "id": "food-01", "location": "Metro Station",
            "products": ["f1", "f2"]
        },
        "emergency": {
            "id": "relief-01", "location": "Relief Camp Sector 7",
            "products": ["e1", "e2"]
        },
    }

    @staticmethod
    def create(kiosk_type):
        """Create a kiosk of the given type."""
        if kiosk_type not in KioskFactory.PRESETS:
            raise ValueError(f"Unknown kiosk type: {kiosk_type}")
        return KioskFactory.PRESETS[kiosk_type]


# ============================================================
# 7. SINGLETON PATTERN - Central Registry
# ============================================================

class CentralRegistry:
    """Singleton that holds global configuration."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.config = {
                    "currency": "INR",
                    "emergency_purchase_limit": 2,
                    "low_stock_threshold": 3,
                }
                cls._instance.kiosks = {}
                cls._instance.status = {
                    "mode": "active",
                    "hardware_ok": True,
                    "network_ok": True,
                    "last_event": None,
                }
        return cls._instance

    def register_kiosk(self, kiosk_id, info):
        self.kiosks[kiosk_id] = info

    def get_config(self):
        return self.config

    def update_status(self, **kwargs):
        self.status.update(kwargs)

    def get_status(self):
        return self.status

    def snapshot(self):
        return {
            "config": dict(self.config),
            "status": dict(self.status),
            "kiosks": dict(self.kiosks),
        }


# ============================================================
# 8. CHAIN OF RESPONSIBILITY - Failure Handling
# ============================================================

class FailureHandler(ABC):
    """Base handler in the chain."""
    def __init__(self, next_handler=None):
        self.next_handler = next_handler

    def handle(self, error):
        if self.can_handle(error):
            return self.process(error)
        if self.next_handler:
            return self.next_handler.handle(error)
        return {"resolved": False, "message": "Unhandled error", "handler": "None"}

    @abstractmethod
    def can_handle(self, error):
        pass
    @abstractmethod
    def process(self, error):
        pass

class RetryHandler(FailureHandler):
    """First try: retry the operation."""
    def can_handle(self, error):
        return error.get("retryable", False)

    def process(self, error):
        return {"resolved": True, "message": "Auto-retry succeeded", "handler": "RetryHandler"}

class RecalibrationHandler(FailureHandler):
    """Second try: recalibrate the hardware module."""
    def can_handle(self, error):
        return error.get("hardware_related", False)

    def process(self, error):
        # Simulate: recalibration succeeds 70% of the time
        import random
        success = random.random() < 0.7
        return {
            "resolved": success,
            "message": "Recalibration succeeded" if success else "Recalibration failed",
            "handler": "RecalibrationHandler"
        }

class TechnicianAlertHandler(FailureHandler):
    """Last resort: alert a technician."""
    def can_handle(self, error):
        return True

    def process(self, error):
        return {"resolved": False, "message": "Technician alert issued", "handler": "TechnicianAlertHandler"}


# Build the default failure chain: Retry -> Recalibration -> Technician Alert
def build_failure_chain():
    """Builds the default chain: RetryHandler -> RecalibrationHandler -> TechnicianAlertHandler"""
    technician = TechnicianAlertHandler()
    recalibration = RecalibrationHandler(technician)
    retry = RetryHandler(recalibration)
    return retry
