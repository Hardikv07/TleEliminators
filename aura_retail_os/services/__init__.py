"""
KioskInterface - Main service layer for Aura Retail OS.
This is the Facade that connects all 8 design patterns together.

Patterns used:
  1. Strategy  — Dynamic pricing (Standard / Discount / Emergency)
  2. State     — Operating modes (Active / PowerSaving / Maintenance / Emergency)
  3. Command   — Purchase, Refund, Restock commands with undo
  4. Observer  — Priority-aware event system
  5. Memento   — Inventory snapshot & rollback
  6. Factory   — Kiosk creation from presets
  7. Singleton — CentralRegistry for global config
  8. Chain of Responsibility — Failure handling (Retry -> Recalibration -> Technician)
"""
import csv
import io
import json
import os
import random
import threading
import time
from models import Product, ProductBundle, Transaction
from patterns import (
    StandardPricing, DiscountPricing, EmergencyPricing,
    ActiveMode, PowerSavingMode, MaintenanceMode, EmergencyMode,
    PurchaseCommand, RefundCommand, RestockCommand,
    EventManager, MementoManager, KioskFactory,
    CentralRegistry, build_failure_chain,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


class KioskInterface:
    """Main interface for a kiosk. Connects all design patterns.
    External systems interact ONLY through this Facade."""

    def __init__(self, kiosk_type="pharmacy"):
        # ── Factory Pattern ───────────────────────────────────
        preset = KioskFactory.create(kiosk_type)
        self.kiosk_id = preset["id"]
        self.kiosk_type = kiosk_type
        self.location = preset["location"]
        self.allowed_products = preset["products"]

        # ── State Pattern ─────────────────────────────────────
        self.mode = ActiveMode()

        # ── Strategy Pattern ──────────────────────────────────
        self.pricing = StandardPricing()

        # ── Observer Pattern ──────────────────────────────────
        self.events = EventManager()
        self._wire_event_subscribers()

        # ── Memento Pattern ───────────────────────────────────
        self.memento = MementoManager()

        # ── Singleton Pattern ─────────────────────────────────
        self.registry = CentralRegistry()
        self.registry.register_kiosk(self.kiosk_id, {
            "type": kiosk_type, "location": self.location
        })

        # ── Chain of Responsibility Pattern ───────────────────
        self.failure_chain = build_failure_chain()

        # ── Data ──────────────────────────────────────────────
        self.inventory = {}          # product_id -> Product
        self.bundles = {}            # bundle_id -> ProductBundle
        self.transactions = []       # list[Transaction]
        self.hardware_modules = {    # tracks which hardware modules are available
            "refrigeration": True,
            "standard_dispenser": True,
            "solar": True,
        }
        self.dispenser_fail_rate = 0.08   # 8% chance of dispense failure

        # ── Concurrency Lock ──────────────────────────────────
        self._lock = threading.Lock()

        self._load_inventory()
        self._load_transactions()

    # ══════════════════════════════════════════════════════════
    # EVENT WIRING (Observer Pattern)
    # ══════════════════════════════════════════════════════════

    def _wire_event_subscribers(self):
        """Subscribe internal handlers to events with priorities."""
        # Emergency events have highest priority (100)
        self.events.subscribe("EMERGENCY", self._on_emergency, priority=100)
        # Hardware failures have high priority (75)
        self.events.subscribe("HARDWARE_FAILURE", self._on_hardware_failure, priority=75)
        # Low stock has medium priority (50)
        self.events.subscribe("LOW_STOCK", self._on_low_stock, priority=50)
        # Transaction events have normal priority (10)
        self.events.subscribe("PURCHASE", self._on_purchase_complete, priority=10)
        self.events.subscribe("TX_FAILED", self._on_tx_failed, priority=10)

    def _on_emergency(self, data):
        """High-priority handler: emergency overrides normal operation."""
        self.registry.update_status(mode="emergency", last_event="EMERGENCY")

    def _on_hardware_failure(self, data):
        """Mark affected products temporarily unavailable."""
        module = (data or {}).get("module", "")
        self.registry.update_status(hardware_ok=False, last_event="HARDWARE_FAILURE")
        # Mark products that require the failed module as unavailable
        for p in self.inventory.values():
            if p.required_module == module:
                p.temporarily_unavailable = True

    def _on_low_stock(self, data):
        self.registry.update_status(last_event="LOW_STOCK")

    def _on_purchase_complete(self, data):
        self.registry.update_status(last_event="PURCHASE")

    def _on_tx_failed(self, data):
        self.registry.update_status(last_event="TX_FAILED")

    # ══════════════════════════════════════════════════════════
    # DATA PERSISTENCE (JSON + CSV)
    # ══════════════════════════════════════════════════════════

    def _load_inventory(self):
        """Load products from JSON file."""
        path = os.path.join(DATA_DIR, "inventory.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            # Load products
            for item in data.get("products", data if isinstance(data, list) else []):
                if item["id"] in self.allowed_products:
                    self.inventory[item["id"]] = Product(
                        id=item["id"],
                        name=item["name"],
                        price=item["price"],
                        stock=item.get("stock", 0),
                        category=item.get("category", "general"),
                        required_module=item.get("required_module") or None,
                        temporarily_unavailable=item.get("temporarily_unavailable", False),
                        max_stock=item.get("max_stock", 30),
                    )
            # Load bundles
            for bundle in data.get("bundles", []) if isinstance(data, dict) else []:
                self.bundles[bundle["id"]] = ProductBundle(
                    id=bundle["id"], name=bundle["name"],
                    components=bundle.get("components", {})
                )
        # Check hardware dependency constraints
        self._check_hardware_dependencies()

    def _load_transactions(self):
        """Load transaction history from JSON."""
        path = os.path.join(DATA_DIR, "transactions.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                items = json.load(f)
            for item in items:
                # Only load transactions for our kiosk's products
                if item.get("product_id", "") in self.allowed_products:
                    self.transactions.append(Transaction(
                        id=item["id"],
                        product_id=item["product_id"],
                        product_name=item["product_name"],
                        quantity=item["quantity"],
                        amount=item["amount"],
                        status=item["status"],
                        user_id=item.get("user_id", "USER001"),
                        pricing_used=item.get("pricing_used", "StandardPricing"),
                        mode_used=item.get("mode_used", "active"),
                    ))

    def _save_data(self):
        """Save current inventory and transactions to JSON."""
        # ── Save inventory ────────────────────────────────────
        inv_path = os.path.join(DATA_DIR, "inventory.json")
        all_items = []
        if os.path.exists(inv_path):
            with open(inv_path, "r") as f:
                raw = json.load(f)
            # Handle both old (list) and new (dict) formats
            if isinstance(raw, list):
                all_items = raw
            else:
                all_items = raw.get("products", [])

        # Update our products in the master list
        for i, item in enumerate(all_items):
            if item["id"] in self.inventory:
                p = self.inventory[item["id"]]
                all_items[i] = {
                    "id": p.id, "name": p.name, "price": p.price,
                    "stock": p.stock, "category": p.category,
                    "required_module": p.required_module or "",
                    "temporarily_unavailable": p.temporarily_unavailable,
                    "max_stock": p.max_stock,
                }

        # Write as new format with bundles
        bundle_list = [b.to_dict() for b in self.bundles.values()]
        with open(inv_path, "w") as f:
            json.dump({"products": all_items, "bundles": bundle_list}, f, indent=2)

        # ── Save transactions ─────────────────────────────────
        tx_path = os.path.join(DATA_DIR, "transactions.json")
        existing = []
        if os.path.exists(tx_path):
            with open(tx_path, "r") as f:
                existing = json.load(f)
        tx_ids = {t["id"] for t in existing}
        for tx in self.transactions:
            d = tx.to_dict()
            if d["id"] not in tx_ids:
                existing.append(d)
            else:
                for i, e in enumerate(existing):
                    if e["id"] == d["id"]:
                        existing[i] = d
        with open(tx_path, "w") as f:
            json.dump(existing, f, indent=2)

    def export_csv(self) -> dict:
        """Export inventory and transactions as CSV strings (System Persistence)."""
        # Inventory CSV
        inv_buf = io.StringIO()
        if self.inventory:
            fields = ["id", "name", "price", "stock", "category",
                       "required_module", "temporarily_unavailable", "available_stock"]
            writer = csv.DictWriter(inv_buf, fieldnames=fields)
            writer.writeheader()
            for p in self.inventory.values():
                writer.writerow({
                    "id": p.id, "name": p.name, "price": p.price,
                    "stock": p.stock, "category": p.category,
                    "required_module": p.required_module or "",
                    "temporarily_unavailable": p.temporarily_unavailable,
                    "available_stock": p.available_stock,
                })

        # Transactions CSV
        tx_buf = io.StringIO()
        if self.transactions:
            fields = ["id", "product_id", "product_name", "quantity",
                       "amount", "status", "user_id", "pricing_used", "mode_used"]
            writer = csv.DictWriter(tx_buf, fieldnames=fields)
            writer.writeheader()
            for tx in self.transactions:
                writer.writerow(tx.to_dict())

        # Also write to disk
        csv_dir = os.path.join(DATA_DIR, "csv_export")
        os.makedirs(csv_dir, exist_ok=True)
        with open(os.path.join(csv_dir, "inventory.csv"), "w", newline="") as f:
            f.write(inv_buf.getvalue())
        with open(os.path.join(csv_dir, "transactions.csv"), "w", newline="") as f:
            f.write(tx_buf.getvalue())

        return {
            "inventory_csv": inv_buf.getvalue(),
            "transactions_csv": tx_buf.getvalue(),
            "message": "CSV files exported to data/csv_export/"
        }

    # ══════════════════════════════════════════════════════════
    # HARDWARE DEPENDENCY CONSTRAINT
    # ══════════════════════════════════════════════════════════

    def _check_hardware_dependencies(self):
        """If a required hardware module is offline, mark products unavailable."""
        for p in self.inventory.values():
            if p.required_module and not self.hardware_modules.get(p.required_module, True):
                p.temporarily_unavailable = True
            elif p.required_module and self.hardware_modules.get(p.required_module, True):
                # Only restore if it was marked unavailable due to hardware
                if p.temporarily_unavailable:
                    p.temporarily_unavailable = False

    def simulate_hardware_fault(self, module_name: str) -> dict:
        """Simulate a hardware module failure."""
        if module_name in self.hardware_modules:
            self.hardware_modules[module_name] = False
            self._check_hardware_dependencies()
            self.events.publish("HARDWARE_FAILURE", {
                "module": module_name, "status": "OFFLINE"
            })
            # Try to resolve via chain of responsibility
            result = self.failure_chain.handle({
                "retryable": True, "hardware_related": True,
                "module": module_name
            })
            return {
                "success": True,
                "module": module_name,
                "status": "OFFLINE",
                "recovery": result,
                "affected_products": [
                    p.name for p in self.inventory.values()
                    if p.required_module == module_name
                ]
            }
        return {"success": False, "message": f"Unknown module: {module_name}"}

    def repair_hardware(self, module_name: str) -> dict:
        """Repair a hardware module."""
        if module_name in self.hardware_modules:
            self.hardware_modules[module_name] = True
            self._check_hardware_dependencies()
            self.events.publish("HARDWARE_REPAIR", {
                "module": module_name, "status": "ONLINE"
            })
            return {"success": True, "module": module_name, "status": "ONLINE"}
        return {"success": False, "message": f"Unknown module: {module_name}"}

    # ══════════════════════════════════════════════════════════
    # CORE OPERATIONS (Facade)
    # ══════════════════════════════════════════════════════════

    def purchase_item(self, product_id, quantity=1, user_id="USER001"):
        """Purchase an item using Command Pattern.
        Thread-safe via lock (concurrent transaction safety)."""
        cmd = PurchaseCommand(self, product_id, quantity, user_id)
        return cmd.execute()

    def refund(self, transaction_id):
        """Refund a transaction using Command Pattern."""
        cmd = RefundCommand(self, transaction_id)
        return cmd.execute()

    def restock(self, product_id, quantity):
        """Restock a product using Command Pattern."""
        cmd = RestockCommand(self, product_id, quantity)
        return cmd.execute()

    def _do_restock(self, product_id, quantity):
        """Internal restock logic."""
        if product_id not in self.inventory:
            return {"success": False, "message": "Product not found"}
        # Save snapshot for undo
        self.memento.save({pid: p.to_dict() for pid, p in self.inventory.items()})
        self.inventory[product_id].stock += quantity
        self._save_data()
        self.events.publish("RESTOCK", {
            "product": product_id, "quantity": quantity,
            "new_stock": self.inventory[product_id].stock
        })
        return {"success": True, "new_stock": self.inventory[product_id].stock}

    def change_mode(self, mode_name):
        """Change kiosk operating mode (State Pattern)."""
        modes = {
            "active": ActiveMode,
            "power_saving": PowerSavingMode,
            "maintenance": MaintenanceMode,
            "emergency": EmergencyMode,
        }
        if mode_name not in modes:
            return {"success": False, "message": f"Unknown mode: {mode_name}"}

        self.mode = modes[mode_name]()

        # Emergency mode also changes pricing (auto-adaptive behavior)
        if mode_name == "emergency":
            self.pricing = EmergencyPricing()
            self.events.publish("EMERGENCY", {"reason": "Emergency mode activated"})
        elif mode_name == "active":
            self.pricing = StandardPricing()

        self.events.publish("MODE_CHANGE", {"mode": mode_name})
        self.registry.update_status(mode=mode_name)
        return {"success": True, "mode": mode_name}

    def change_pricing(self, strategy_name):
        """Switch pricing strategy at runtime (Strategy Pattern)."""
        strategies = {
            "standard": StandardPricing,
            "discount": DiscountPricing,
            "emergency": EmergencyPricing,
        }
        if strategy_name not in strategies:
            return {"success": False, "message": "Unknown strategy"}
        self.pricing = strategies[strategy_name]()
        self.events.publish("PRICING_CHANGE", {"strategy": strategy_name})
        return {"success": True, "strategy": strategy_name}

    def calculate_price(self, base_price: float, quantity: int) -> dict:
        """Compute the final price dynamically using the active pricing strategy."""
        final = self.pricing.calculate(base_price, quantity)
        return {
            "base_price": base_price,
            "quantity": quantity,
            "strategy": self.pricing.__class__.__name__,
            "final": final,
        }

    def get_inventory(self):
        """Get all products as list of dicts."""
        return [p.to_dict() for p in self.inventory.values()]

    def get_bundles(self):
        """Get all product bundles."""
        result = []
        for b in self.bundles.values():
            d = b.to_dict()
            # Check if bundle can be fulfilled
            can_fulfill = True
            for pid, qty in b.components.items():
                p = self.inventory.get(pid)
                if not p or p.available_stock < qty:
                    can_fulfill = False
                    break
            d["can_fulfill"] = can_fulfill
            result.append(d)
        return result

    def get_transactions(self):
        """Get all transactions."""
        return [t.to_dict() for t in self.transactions]

    def get_events(self):
        """Get event log."""
        return self.events.get_log()

    def diagnostics(self):
        """Run system diagnostics (Facade Pattern).
        Kiosk operational status is DERIVED from hardware + mode + network."""
        hw_ok = all(self.hardware_modules.values())
        network_ok = self.registry.get_status().get("network_ok", True)
        mode_allows = self.mode.can_purchase()[0]

        # Derived operational status
        if not hw_ok:
            operational_status = "DEGRADED"
        elif not network_ok:
            operational_status = "OFFLINE"
        elif not mode_allows:
            operational_status = "RESTRICTED"
        else:
            operational_status = "OPERATIONAL"

        return {
            "kiosk_id": self.kiosk_id,
            "type": self.kiosk_type,
            "location": self.location,
            "mode": self.mode.name,
            "pricing": self.pricing.__class__.__name__,
            "products": len(self.inventory),
            "total_stock": sum(p.stock for p in self.inventory.values()),
            "total_available": sum(p.available_stock for p in self.inventory.values()),
            "transactions": len(self.transactions),
            "purchase_allowed": mode_allows,
            "hardware_ok": hw_ok,
            "hardware_modules": dict(self.hardware_modules),
            "network_ok": network_ok,
            "operational_status": operational_status,
            "snapshots": self.memento.count(),
            "bundles": len(self.bundles),
        }

    # ══════════════════════════════════════════════════════════
    # INTERNAL PURCHASE LOGIC (Atomic Transaction)
    # ══════════════════════════════════════════════════════════

    def _do_purchase(self, product_id, quantity, user_id):
        """Internal purchase logic with full atomic transaction support.
        Uses threading.Lock for concurrent transaction safety."""
        with self._lock:  # Concurrent Transaction Safety
            # 1. Check mode allows purchase (State Pattern)
            allowed, reason = self.mode.can_purchase()
            if not allowed:
                self.events.publish("TX_FAILED", {
                    "product": product_id, "reason": reason
                })
                return {"success": False, "message": reason}

            # 2. Check emergency purchase limit
            if self.mode.name == "emergency":
                limit = self.registry.get_config().get("emergency_purchase_limit", 2)
                if quantity > limit:
                    self.events.publish("TX_FAILED", {
                        "product": product_id,
                        "reason": f"Emergency limit: max {limit} items"
                    })
                    return {"success": False,
                            "message": f"Emergency limit: max {limit} items"}

            # 3. Check product exists
            if product_id not in self.inventory:
                return {"success": False, "message": "Product not found"}

            product = self.inventory[product_id]

            # 4. Hardware dependency constraint
            if product.temporarily_unavailable:
                return {"success": False,
                        "message": f"Product temporarily unavailable (requires: {product.required_module})"}

            # 5. Check available stock (derived: stock - reserved)
            if product.available_stock < quantity:
                return {"success": False, "message": "Insufficient stock"}

            # 6. Save state for rollback (Memento Pattern)
            self.memento.save({
                pid: p.to_dict() for pid, p in self.inventory.items()
            })

            # 7. Reserve inventory (prevents overselling in concurrent scenarios)
            product.reserved += quantity

            # 8. Calculate price (Strategy Pattern — computed dynamically)
            amount = self.pricing.calculate(product.price, quantity)

            # 9. Simulate payment
            payment_failed = random.random() < 0.08  # 8% failure rate
            if payment_failed:
                # Payment failed — Chain of Responsibility
                result = self.failure_chain.handle({"retryable": True, "hardware_related": False})
                if not result["resolved"]:
                    # Rollback reservation
                    product.reserved -= quantity
                    self._undo_last()
                    self.events.publish("TX_FAILED", {
                        "product": product_id, "reason": "Payment failed",
                        "recovery": result["handler"]
                    })
                    return {"success": False,
                            "message": f"Payment failed ({result['handler']}), rolled back"}

            # 10. Simulate dispensing (may fail — delayed hardware response)
            dispense_failed = random.random() < self.dispenser_fail_rate
            if dispense_failed:
                # Hardware failure — Chain of Responsibility
                result = self.failure_chain.handle({
                    "retryable": True, "hardware_related": True,
                    "module": "standard_dispenser"
                })
                self.events.publish("HARDWARE_FAILURE", {
                    "module": "standard_dispenser",
                    "product": product_id,
                    "recovery": result
                })

                if not result["resolved"]:
                    # ATOMIC ROLLBACK: payment would be refunded, reservation released
                    product.reserved -= quantity
                    self._undo_last()
                    self.events.publish("TX_FAILED", {
                        "product": product_id,
                        "reason": "Dispense failed",
                        "recovery": result["handler"]
                    })
                    return {"success": False,
                            "message": f"Dispense failed ({result['handler']}), transaction rolled back"}

            # 11. Commit: update inventory (only on successful transaction)
            product.stock -= quantity
            product.reserved -= quantity

            # 12. Create transaction record
            tx = Transaction(
                product_id=product_id,
                product_name=product.name,
                quantity=quantity,
                amount=amount,
                status="completed",
                user_id=user_id,
                pricing_used=self.pricing.__class__.__name__,
                mode_used=self.mode.name,
            )
            self.transactions.append(tx)

            # 13. Check low stock (Observer Pattern)
            threshold = self.registry.get_config().get("low_stock_threshold", 3)
            if product.available_stock <= threshold:
                self.events.publish("LOW_STOCK", {
                    "product": product_id,
                    "stock": product.stock,
                    "available": product.available_stock
                })

            # 14. Publish success event
            self.events.publish("PURCHASE", {
                "transaction_id": tx.id, "amount": amount,
                "product": product.name, "quantity": quantity
            })

            # 15. Persist to JSON
            self._save_data()

            return {
                "success": True,
                "transaction_id": tx.id,
                "product": product.name,
                "quantity": quantity,
                "amount": amount,
                "pricing": self.pricing.__class__.__name__,
                "mode": self.mode.name,
            }

    def _do_refund(self, transaction_id):
        """Internal refund logic."""
        with self._lock:
            tx = next((t for t in self.transactions if t.id == transaction_id), None)
            if not tx:
                return {"success": False, "message": "Transaction not found"}
            if tx.status == "refunded":
                return {"success": False, "message": "Already refunded"}

            # Save snapshot before refund
            self.memento.save({
                pid: p.to_dict() for pid, p in self.inventory.items()
            })

            # Restore stock
            if tx.product_id in self.inventory:
                self.inventory[tx.product_id].stock += tx.quantity

            tx.status = "refunded"
            self._save_data()
            self.events.publish("REFUND", {
                "transaction_id": transaction_id,
                "product": tx.product_name,
                "amount": tx.amount
            })
            return {"success": True, "transaction_id": transaction_id}

    def _undo_last(self):
        """Undo last operation using Memento Pattern (Transaction Rollback)."""
        with self._lock:
            state = self.memento.restore()
            if state:
                for pid, data in state.items():
                    if pid in self.inventory:
                        self.inventory[pid] = Product(**{
                            k: v for k, v in data.items()
                            if k in Product.__dataclass_fields__
                        })
                self._save_data()
                self.events.publish("UNDO", {"message": "Rolled back to previous state"})
                return {"success": True, "message": "Rolled back to previous state"}
            return {"success": False, "message": "No snapshot available"}

    # ══════════════════════════════════════════════════════════
    # SIMULATION SCENARIOS (for demo / testing)
    # ══════════════════════════════════════════════════════════

    def run_simulation(self, scenario: str) -> dict:
        """Run a pre-built simulation scenario for demonstration."""
        if scenario == "emergency":
            self.change_mode("emergency")
            r1 = self.purchase_item(list(self.inventory.keys())[0], 1, "SIM-USER")
            r2 = self.purchase_item(list(self.inventory.keys())[0], 5, "SIM-USER")
            return {
                "scenario": "Emergency Mode",
                "steps": [
                    {"action": "Activate emergency mode", "result": "Mode changed"},
                    {"action": "Purchase 1 item (within limit)", "result": r1},
                    {"action": "Purchase 5 items (exceeds limit)", "result": r2},
                ]
            }
        elif scenario == "hardware_failure":
            result = self.simulate_hardware_fault("refrigeration")
            return {
                "scenario": "Hardware Failure (Refrigeration)",
                "steps": [
                    {"action": "Simulate refrigeration failure", "result": result},
                ]
            }
        elif scenario == "pricing_switch":
            prices = {}
            pid = list(self.inventory.keys())[0]
            p = self.inventory[pid]
            for strat_name, strat_cls in [("standard", StandardPricing), ("discount", DiscountPricing), ("emergency", EmergencyPricing)]:
                prices[strat_name] = strat_cls().calculate(p.price, 1)
            return {
                "scenario": "Dynamic Pricing Comparison",
                "product": p.name,
                "base_price": p.price,
                "prices": prices,
            }
        elif scenario == "rollback":
            pid = list(self.inventory.keys())[0]
            stock_before = self.inventory[pid].stock
            self.purchase_item(pid, 1, "SIM-USER")
            stock_after_purchase = self.inventory[pid].stock
            self._undo_last()
            stock_after_undo = self.inventory[pid].stock
            return {
                "scenario": "Transaction Rollback (Memento)",
                "steps": [
                    {"stock_before": stock_before},
                    {"stock_after_purchase": stock_after_purchase},
                    {"stock_after_undo": stock_after_undo},
                ]
            }
        return {"error": f"Unknown scenario: {scenario}"}
