from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .kiosk import AuraKiosk


class KioskMode(ABC):
    name: str = "Mode"

    @abstractmethod
    def can_purchase(self, kiosk: "AuraKiosk") -> tuple[bool, str]:
        raise NotImplementedError


class ActiveMode(KioskMode):
    name = "ActiveMode"

    def can_purchase(self, kiosk: "AuraKiosk") -> tuple[bool, str]:
        return True, "Active mode permits purchases."


class PowerSavingMode(KioskMode):
    name = "PowerSavingMode"

    def can_purchase(self, kiosk: "AuraKiosk") -> tuple[bool, str]:
        return False, "Power saving mode suspends customer-facing operations."


class MaintenanceMode(KioskMode):
    name = "MaintenanceMode"

    def can_purchase(self, kiosk: "AuraKiosk") -> tuple[bool, str]:
        return False, "Maintenance mode blocks purchases."


class EmergencyLockdownMode(KioskMode):
    name = "EmergencyLockdownMode"

    def can_purchase(self, kiosk: "AuraKiosk") -> tuple[bool, str]:
        limit = kiosk.registry.config.get("emergency_purchase_limit", 2)
        if kiosk.last_purchase_quantity > limit:
            return False, f"Emergency limit exceeded: max {limit} essential items."
        return True, "Emergency mode allows limited essential-item purchases."
