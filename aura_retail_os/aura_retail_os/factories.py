from __future__ import annotations

from abc import ABC, abstractmethod

from .events import EventBus
from .hardware import HardwareMonitor, MockDispenser, RetryHandler, RecalibrationHandler, TechnicianAlertHandler, SensorManager
from .inventory import InventoryManager, Product, ProductBundle
from .kiosk import AuraKiosk
from .payment import PaymentProcessor, MockUPIPaymentProvider, MockCardPaymentProvider


class KioskFactory(ABC):
    @abstractmethod
    def create_kiosk(self) -> AuraKiosk:
        raise NotImplementedError

    def _build_failure_chain(self):
        technician = TechnicianAlertHandler()
        recalibration = RecalibrationHandler(technician)
        retry = RetryHandler(recalibration)
        return retry


class PharmacyKioskFactory(KioskFactory):
    def create_kiosk(self) -> AuraKiosk:
        inventory = InventoryManager()
        inventory.add_product(Product("p1", "Paracetamol", 20.0, 10, essential=True))
        inventory.add_product(Product("p2", "Insulin", 150.0, 4, essential=True, required_module="refrigeration"))

        # nested bundle example
        inventory.add_bundle(ProductBundle("b1", "FirstAidKit", {"p1": 2, "p2": 1}))

        bus = EventBus()
        dispenser = MockDispenser(fail_rate=0.2, name="PharmacyDispenser")
        monitor = HardwareMonitor(SensorManager(), self._build_failure_chain())
        payment = PaymentProcessor(MockCardPaymentProvider())
        return AuraKiosk("pharmacy-01", "PharmacyKiosk", inventory, payment, dispenser, monitor, bus)


class FoodKioskFactory(KioskFactory):
    def create_kiosk(self) -> AuraKiosk:
        inventory = InventoryManager()
        inventory.add_product(Product("f1", "Sandwich", 50.0, 12))
        inventory.add_product(Product("f2", "Juice", 30.0, 8))
        bus = EventBus()
        dispenser = MockDispenser(fail_rate=0.05, name="FoodDispenser")
        monitor = HardwareMonitor(SensorManager(), self._build_failure_chain())
        payment = PaymentProcessor(MockUPIPaymentProvider())
        return AuraKiosk("food-01", "FoodKiosk", inventory, payment, dispenser, monitor, bus)


class EmergencyReliefKioskFactory(KioskFactory):
    def create_kiosk(self) -> AuraKiosk:
        inventory = InventoryManager()
        inventory.add_product(Product("e1", "Water Bottle", 10.0, 20, essential=True))
        inventory.add_product(Product("e2", "Energy Bar", 15.0, 30, essential=True))
        inventory.add_bundle(ProductBundle("b2", "ReliefPack", {"e1": 2, "e2": 2}))
        bus = EventBus()
        dispenser = MockDispenser(fail_rate=0.1, name="ReliefDispenser")
        monitor = HardwareMonitor(SensorManager(), self._build_failure_chain())
        payment = PaymentProcessor(MockUPIPaymentProvider())
        kiosk = AuraKiosk("relief-01", "EmergencyReliefKiosk", inventory, payment, dispenser, monitor, bus)
        return kiosk
