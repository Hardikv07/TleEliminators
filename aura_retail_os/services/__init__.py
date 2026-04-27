"""
KioskInterface - Main service layer for Aura Retail OS.
This is the Facade that connects all patterns together.
"""
import json
import os
from models import Product, Transaction
from patterns import (
    StandardPricing, DiscountPricing, EmergencyPricing,
    ActiveMode, MaintenanceMode, EmergencyMode,
    PurchaseCommand, RefundCommand,
    EventManager, MementoManager, KioskFactory,
    CentralRegistry, RetryHandler, AlertHandler,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


class KioskInterface:
    """Main interface for a kiosk. Connects all design patterns."""

    def __init__(self, kiosk_type="pharmacy"):
        # Factory Pattern - create kiosk
        preset = KioskFactory.create(kiosk_type)
        self.kiosk_id = preset["id"]
        self.kiosk_type = kiosk_type
        self.location = preset["location"]
        self.allowed_products = preset["products"]

        # State Pattern - operating mode
        self.mode = ActiveMode()

        # Strategy Pattern - pricing
        self.pricing = StandardPricing()

        # Observer Pattern - events
        self.events = EventManager()

        # Memento Pattern - rollback
        self.memento = MementoManager()

        # Singleton - registry
        self.registry = CentralRegistry()
        self.registry.register_kiosk(self.kiosk_id, {
            "type": kiosk_type, "location": self.location
        })

        # Chain of Responsibility - failure handling
        self.failure_chain = RetryHandler(AlertHandler())

        # Data
        self.inventory = {}   # product_id -> Product
        self.transactions = []
        self._load_inventory()

    # ── Data Persistence ──────────────────────────────────────

    def _load_inventory(self):
        """Load products from JSON file."""
        path = os.path.join(DATA_DIR, "inventory.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                items = json.load(f)
            for item in items:
                if item["id"] in self.allowed_products:
                    self.inventory[item["id"]] = Product(**item)

    def _save_data(self):
        """Save current inventory and transactions to JSON."""
        # Save inventory
        all_items = []
        inv_path = os.path.join(DATA_DIR, "inventory.json")
        if os.path.exists(inv_path):
            with open(inv_path, "r") as f:
                all_items = json.load(f)

        # Update only our products
        for i, item in enumerate(all_items):
            if item["id"] in self.inventory:
                all_items[i] = self.inventory[item["id"]].to_dict()

        with open(inv_path, "w") as f:
            json.dump(all_items, f, indent=2)

        # Save transactions
        tx_path = os.path.join(DATA_DIR, "transactions.json")
        existing = []
        if os.path.exists(tx_path):
            with open(tx_path, "r") as f:
                existing = json.load(f)
        # Append new transactions
        tx_ids = {t["id"] for t in existing}
        for tx in self.transactions:
            d = tx.to_dict()
            if d["id"] not in tx_ids:
                existing.append(d)
            else:
                # Update existing
                for i, e in enumerate(existing):
                    if e["id"] == d["id"]:
                        existing[i] = d
        with open(tx_path, "w") as f:
            json.dump(existing, f, indent=2)

    # ── Core Operations ───────────────────────────────────────

    def purchase_item(self, product_id, quantity=1, user_id="USER001"):
        """Purchase an item using Command Pattern."""
        cmd = PurchaseCommand(self, product_id, quantity, user_id)
        return cmd.execute()

    def refund(self, transaction_id):
        """Refund a transaction using Command Pattern."""
        cmd = RefundCommand(self, transaction_id)
        return cmd.execute()

    def restock(self, product_id, quantity):
        """Add stock to a product."""
        if product_id not in self.inventory:
            return {"success": False, "message": "Product not found"}
        self.inventory[product_id].stock += quantity
        self._save_data()
        self.events.publish("RESTOCK", {
            "product": product_id, "quantity": quantity
        })
        return {"success": True, "new_stock": self.inventory[product_id].stock}

    def change_mode(self, mode_name):
        """Change kiosk operating mode (State Pattern)."""
        modes = {
            "active": ActiveMode,
            "maintenance": MaintenanceMode,
            "emergency": EmergencyMode,
        }
        if mode_name not in modes:
            return {"success": False, "message": f"Unknown mode: {mode_name}"}

        self.mode = modes[mode_name]()

        # Emergency mode also changes pricing
        if mode_name == "emergency":
            self.pricing = EmergencyPricing()
            self.events.publish("EMERGENCY", {"reason": "Emergency mode activated"})
        elif mode_name == "active":
            self.pricing = StandardPricing()

        self.events.publish("MODE_CHANGE", {"mode": mode_name})
        return {"success": True, "mode": mode_name}

    def change_pricing(self, strategy_name):
        """Switch pricing strategy (Strategy Pattern)."""
        strategies = {
            "standard": StandardPricing,
            "discount": DiscountPricing,
            "emergency": EmergencyPricing,
        }
        if strategy_name not in strategies:
            return {"success": False, "message": "Unknown strategy"}
        self.pricing = strategies[strategy_name]()
        return {"success": True, "strategy": strategy_name}

    def get_inventory(self):
        """Get all products as list of dicts."""
        return [p.to_dict() for p in self.inventory.values()]

    def get_transactions(self):
        """Get all transactions."""
        return [t.to_dict() for t in self.transactions]

    def get_events(self):
        """Get event log."""
        return self.events.get_log()

    def diagnostics(self):
        """Run system diagnostics (Facade Pattern)."""
        return {
            "kiosk_id": self.kiosk_id,
            "type": self.kiosk_type,
            "location": self.location,
            "mode": self.mode.name,
            "pricing": self.pricing.__class__.__name__,
            "products": len(self.inventory),
            "total_stock": sum(p.stock for p in self.inventory.values()),
            "transactions": len(self.transactions),
            "purchase_allowed": self.mode.can_purchase()[0],
            "hardware": "OK",
        }

    # ── Internal Methods ──────────────────────────────────────

    def _do_purchase(self, product_id, quantity, user_id):
        """Internal purchase logic."""
        # 1. Check mode allows purchase (State Pattern)
        allowed, reason = self.mode.can_purchase()
        if not allowed:
            return {"success": False, "message": reason}

        # 2. Check emergency limits
        if self.mode.name == "emergency":
            limit = self.registry.get_config().get("emergency_purchase_limit", 2)
            if quantity > limit:
                return {"success": False,
                        "message": f"Emergency limit: max {limit} items"}

        # 3. Check product exists and stock
        if product_id not in self.inventory:
            return {"success": False, "message": "Product not found"}

        product = self.inventory[product_id]
        if product.stock < quantity:
            return {"success": False, "message": "Insufficient stock"}

        # 4. Save state for rollback (Memento Pattern)
        self.memento.save({
            pid: p.to_dict() for pid, p in self.inventory.items()
        })

        # 5. Calculate price (Strategy Pattern)
        amount = self.pricing.calculate(product.price, quantity)

        # 6. Simulate payment (mock - can fail)
        import random
        if random.random() < 0.1:  # 10% failure rate
            # Failure handling (Chain of Responsibility)
            result = self.failure_chain.handle({"retryable": True})
            if not result["resolved"]:
                # Rollback (Memento Pattern)
                self._undo_last()
                self.events.publish("TX_FAILED", {
                    "product": product_id, "reason": "Payment failed"
                })
                return {"success": False, "message": "Payment failed, rolled back"}

        # 7. Update inventory
        product.stock -= quantity

        # 8. Create transaction record
        tx = Transaction(
            product_id=product_id,
            product_name=product.name,
            quantity=quantity,
            amount=amount,
            status="completed"
        )
        self.transactions.append(tx)

        # 9. Check low stock (Observer Pattern)
        threshold = self.registry.get_config().get("low_stock_threshold", 3)
        if product.stock <= threshold:
            self.events.publish("LOW_STOCK", {
                "product": product_id, "stock": product.stock
            })

        # 10. Publish success event
        self.events.publish("PURCHASE", {
            "transaction_id": tx.id, "amount": amount
        })

        # 11. Save to JSON
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
        tx = next((t for t in self.transactions if t.id == transaction_id), None)
        if not tx:
            return {"success": False, "message": "Transaction not found"}
        if tx.status == "refunded":
            return {"success": False, "message": "Already refunded"}

        # Restore stock
        if tx.product_id in self.inventory:
            self.inventory[tx.product_id].stock += tx.quantity

        tx.status = "refunded"
        self._save_data()
        self.events.publish("REFUND", {"transaction_id": transaction_id})
        return {"success": True, "transaction_id": transaction_id}

    def _undo_last(self):
        """Undo last operation using Memento Pattern."""
        state = self.memento.restore()
        if state:
            for pid, data in state.items():
                if pid in self.inventory:
                    self.inventory[pid] = Product(**data)
            return {"success": True, "message": "Rolled back to previous state"}
        return {"success": False, "message": "No snapshot available"}
