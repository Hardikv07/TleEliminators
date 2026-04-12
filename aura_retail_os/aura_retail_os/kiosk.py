from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import csv
import json
import uuid

from .commands import PurchaseItemCommand, RefundCommand, RestockCommand
from .events import (
    EventBus,
    EmergencyModeActivated,
    HardwareFailureEvent,
    LowStockEvent,
    TransactionCompleted,
    TransactionFailed,
)
from .hardware import HardwareMonitor, DispenserInterface
from .inventory import InventoryManager
from .memento import TransactionMemento, TransactionSnapshot
from .payment import PaymentProcessor
from .pricing import PricingStrategy, StandardPricing, DiscountedPricing, EmergencyPricing
from .registry import CentralRegistry
from .state import ActiveMode, EmergencyLockdownMode, KioskMode


@dataclass
class TransactionRecord:
    transaction_id: str
    product_id: str
    quantity: int
    amount: float
    user_id: str
    status: str


class AuraKiosk:
    def __init__(
        self,
        kiosk_id: str,
        kiosk_type: str,
        inventory: InventoryManager,
        payment_processor: PaymentProcessor,
        dispenser: DispenserInterface,
        hardware_monitor: HardwareMonitor,
        event_bus: EventBus,
    ) -> None:
        self.kiosk_id = kiosk_id
        self.kiosk_type = kiosk_type
        self.inventory = inventory
        self.payment_processor = payment_processor
        self.dispenser = dispenser
        self.hardware_monitor = hardware_monitor
        self.event_bus = event_bus
        self.registry = CentralRegistry()
        self.registry.register_kiosk(kiosk_id, {"type": kiosk_type})

        self.mode: KioskMode = ActiveMode()
        self.pricing_strategy: PricingStrategy = StandardPricing()
        self.transaction_log: list[TransactionRecord] = []
        self._active_transactions: Dict[str, Dict[str, Any]] = {}
        self._last_snapshot: TransactionMemento | None = None
        self.last_purchase_quantity: int = 0

        self._wire_events()

    def _wire_events(self) -> None:
        self.event_bus.subscribe(EmergencyModeActivated, self._on_emergency_mode, priority=100)
        self.event_bus.subscribe(LowStockEvent, self._on_low_stock, priority=50)
        self.event_bus.subscribe(HardwareFailureEvent, self._on_hardware_failure, priority=75)
        self.event_bus.subscribe(TransactionCompleted, self._on_transaction_completed, priority=10)
        self.event_bus.subscribe(TransactionFailed, self._on_transaction_failed, priority=10)

    def _on_emergency_mode(self, event: EmergencyModeActivated) -> None:
        self.mode = EmergencyLockdownMode()
        self.pricing_strategy = EmergencyPricing()
        self.registry.update_status(mode=self.mode.name, last_event=event.name)

    def _on_low_stock(self, event: LowStockEvent) -> None:
        self.pricing_strategy = DiscountedPricing()
        self.registry.update_status(last_event=event.name)

    def _on_hardware_failure(self, event: HardwareFailureEvent) -> None:
        self.registry.update_status(hardware_ok=False, last_event=event.name)

    def _on_transaction_completed(self, event: TransactionCompleted) -> None:
        self.registry.update_status(last_event=event.name)

    def _on_transaction_failed(self, event: TransactionFailed) -> None:
        self.registry.update_status(last_event=event.name)

    def set_mode(self, mode: KioskMode) -> None:
        self.mode = mode
        self.registry.update_status(mode=mode.name)

    def set_pricing_strategy(self, strategy: PricingStrategy) -> None:
        self.pricing_strategy = strategy

    def diagnostics(self) -> dict[str, Any]:
        result = self.hardware_monitor.diagnostics()
        result["mode"] = self.mode.name
        result["pricing"] = self.pricing_strategy.__class__.__name__
        return result

    def purchase_item(self, product_id: str, quantity: int, user_id: str) -> dict[str, Any]:
        cmd = PurchaseItemCommand(self, product_id, quantity, user_id)
        return cmd.execute()

    def refund_transaction(self, transaction_id: str) -> dict[str, Any]:
        cmd = RefundCommand(self, transaction_id)
        return cmd.execute()

    def restock_inventory(self, product_id: str, quantity: int) -> dict[str, Any]:
        cmd = RestockCommand(self, product_id, quantity)
        return cmd.execute()

    def _snapshot_state(self) -> TransactionMemento:
        snapshot = TransactionSnapshot(
            inventory_state=self.inventory.snapshot(),
            transaction_log=[record.__dict__.copy() for record in self.transaction_log],
            active_transactions=json.loads(json.dumps(self._active_transactions)),
        )
        memento = TransactionMemento(snapshot)
        self._last_snapshot = memento
        return memento

    def _restore_state(self, memento: TransactionMemento) -> None:
        snapshot = memento.get_snapshot()
        self.inventory.restore(snapshot.inventory_state)
        self.transaction_log = [TransactionRecord(**item) for item in snapshot.transaction_log]
        self._active_transactions = snapshot.active_transactions

    def _undo_last_purchase(self) -> dict[str, Any]:
        if self._last_snapshot:
            self._restore_state(self._last_snapshot)
        return {"status": "rolled_back"}

    def _execute_purchase(self, product_id: str, quantity: int, user_id: str) -> dict[str, Any]:
        self.last_purchase_quantity = quantity
        allowed, reason = self.mode.can_purchase(self)
        if not allowed:
            return {"success": False, "message": reason}

        product = self.inventory.products[product_id]
        if product.temporarily_unavailable:
            return {"success": False, "message": "Product temporarily unavailable"}

        available = self.inventory.available_stock(product_id)
        if available < quantity:
            return {"success": False, "message": "Insufficient stock"}

        self._snapshot_state()
        self.inventory.reserve(product_id, quantity)

        transaction_id = str(uuid.uuid4())
        amount = self.pricing_strategy.compute_price(product.base_price, quantity)
        self._active_transactions[transaction_id] = {
            "product_id": product_id,
            "quantity": quantity,
            "amount": amount,
            "user_id": user_id,
        }

        payment = self.payment_processor.charge(amount)
        if not payment.success:
            self.inventory.release_reservation(product_id, quantity)
            self.event_bus.publish(TransactionFailed(transaction_id, payment.message))
            return {"success": False, "message": payment.message, "transaction_id": transaction_id}

        dispensed = self.dispenser.dispense(product_id, quantity)
        if not dispensed:
            failure_context = self.hardware_monitor.resolve_failure(product_id, quantity)
            self.event_bus.publish(HardwareFailureEvent(self.dispenser.__class__.__name__, failure_context.message))

            if failure_context.resolved:
                # Simulate that the repair/recalibration fixed the issue.
                if hasattr(self.dispenser, "fail_rate"):
                    self.dispenser.fail_rate = 0.0
                dispensed = self.dispenser.dispense(product_id, quantity)

            if not dispensed:
                self.payment_processor.refund(payment.transaction_id)
                self.inventory.release_reservation(product_id, quantity)
                self._restore_state(self._last_snapshot)  # rollback
                self.event_bus.publish(TransactionFailed(transaction_id, "Hardware failure; rolled back"))
                return {"success": False, "message": "Hardware failure; transaction rolled back", "transaction_id": transaction_id}

        self.inventory.commit_sale(product_id, quantity)
        self.transaction_log.append(
            TransactionRecord(
                transaction_id=transaction_id,
                product_id=product_id,
                quantity=quantity,
                amount=amount,
                user_id=user_id,
                status="COMPLETED",
            )
        )
        self._active_transactions.pop(transaction_id, None)

        threshold = self.registry.config.get("low_stock_threshold", 3)
        if self.inventory.available_stock(product_id) <= threshold:
            self.event_bus.publish(LowStockEvent(product_id, self.inventory.available_stock(product_id)))

        self.event_bus.publish(TransactionCompleted(transaction_id))
        return {
            "success": True,
            "transaction_id": transaction_id,
            "amount": amount,
            "product": product.name,
            "mode": self.mode.name,
            "pricing": self.pricing_strategy.__class__.__name__,
        }

    def _execute_refund(self, transaction_id: str) -> dict[str, Any]:
        record = next((r for r in self.transaction_log if r.transaction_id == transaction_id), None)
        if not record:
            return {"success": False, "message": "Transaction not found"}
        success = self.payment_processor.refund(transaction_id)
        if success:
            record.status = "REFUNDED"
        return {"success": success, "transaction_id": transaction_id}

    def _execute_restock(self, product_id: str, quantity: int) -> dict[str, Any]:
        self.inventory.restock(product_id, quantity)
        return {"success": True, "product_id": product_id, "new_stock": self.inventory.products[product_id].stock}

    def persist_state(self, directory: str | Path) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "config.json").write_text(json.dumps(self.registry.snapshot(), indent=2), encoding="utf-8")

        inventory_rows = []
        for product in self.inventory.products.values():
            inventory_rows.append({
                "product_id": product.product_id,
                "name": product.name,
                "base_price": product.base_price,
                "stock": product.stock,
                "essential": product.essential,
                "required_module": product.required_module or "",
                "temporarily_unavailable": product.temporarily_unavailable,
            })

        with (directory / "inventory.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(inventory_rows[0].keys()) if inventory_rows else [])
            if inventory_rows:
                writer.writeheader()
                writer.writerows(inventory_rows)

        tx_rows = [record.__dict__ for record in self.transaction_log]
        with (directory / "transactions.csv").open("w", newline="", encoding="utf-8") as f:
            if tx_rows:
                writer = csv.DictWriter(f, fieldnames=list(tx_rows[0].keys()))
                writer.writeheader()
                writer.writerows(tx_rows)

    def summary(self) -> dict[str, Any]:
        return {
            "kiosk_id": self.kiosk_id,
            "kiosk_type": self.kiosk_type,
            "mode": self.mode.name,
            "pricing_strategy": self.pricing_strategy.__class__.__name__,
            "inventory": {pid: self.inventory.available_stock(pid) for pid in self.inventory.products},
            "transactions": [r.__dict__ for r in self.transaction_log],
        }


class KioskInterface:
    """Facade pattern: a simplified entry point for external systems."""

    def __init__(self, kiosk: AuraKiosk) -> None:
        self._kiosk = kiosk

    def purchaseItem(self, product_id: str, quantity: int, user_id: str) -> dict[str, Any]:
        return self._kiosk.purchase_item(product_id, quantity, user_id)

    def refundTransaction(self, transaction_id: str) -> dict[str, Any]:
        return self._kiosk.refund_transaction(transaction_id)

    def runDiagnostics(self) -> dict[str, Any]:
        return self._kiosk.diagnostics()

    def restockInventory(self, product_id: str, quantity: int) -> dict[str, Any]:
        return self._kiosk.restock_inventory(product_id, quantity)
