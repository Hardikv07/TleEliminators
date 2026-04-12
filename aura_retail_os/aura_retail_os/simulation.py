from __future__ import annotations

from pprint import pprint

from .events import EmergencyModeActivated, LowStockEvent
from .factories import PharmacyKioskFactory
from .state import ActiveMode, MaintenanceMode, PowerSavingMode


def run_all_scenarios() -> None:
    kiosk = PharmacyKioskFactory().create_kiosk()
    interface = kiosk  # internal use in simulation

    print("\nSCENARIO 1: Emergency Mode Activation")
    kiosk.event_bus.publish(EmergencyModeActivated("Disaster alert in city zone"))
    result1 = interface.purchase_item("p1", 1, "user-101")
    pprint(result1)
    print("Mode:", kiosk.mode.name, "| Pricing:", kiosk.pricing_strategy.__class__.__name__)

    print("\nSCENARIO 2: Hardware Failure Recovery")
    kiosk.dispenser.fail_rate = 1.0
    kiosk.set_mode(ActiveMode())
    result2 = interface.purchase_item("p1", 1, "user-102")
    pprint(result2)

    print("\nSCENARIO 3: Dynamic Pricing Change")
    kiosk.set_mode(ActiveMode())
    kiosk.event_bus.publish(LowStockEvent("p1", kiosk.inventory.available_stock("p1")))
    result3 = interface.purchase_item("p1", 1, "user-103")
    pprint(result3)
    print("Mode:", kiosk.mode.name, "| Pricing:", kiosk.pricing_strategy.__class__.__name__)

    print("\nSCENARIO 4: Atomic Transaction Rollback")
    kiosk.dispenser.fail_rate = 1.0
    kiosk.set_mode(ActiveMode())
    result4 = interface.purchase_item("p2", 1, "user-104")
    pprint(result4)

    print("\nFINAL SUMMARY")
    pprint(kiosk.summary())
