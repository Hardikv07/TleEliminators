"""Models for Aura Retail OS."""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import uuid


@dataclass
class Product:
    """Represents a product in the kiosk inventory."""
    id: str
    name: str
    price: float
    stock: int
    category: str = "general"           # general, essential, premium
    required_module: Optional[str] = None   # e.g. "refrigeration", "solar"
    temporarily_unavailable: bool = False
    max_stock: int = 30                 # max capacity for stock-bar display
    reserved: int = 0                   # items reserved in active transactions

    @property
    def available_stock(self) -> int:
        """Derived attribute: stock minus reserved minus unavailable."""
        if self.temporarily_unavailable:
            return 0
        return max(0, self.stock - self.reserved)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "price": self.price,
            "stock": self.stock, "category": self.category,
            "required_module": self.required_module or "",
            "temporarily_unavailable": self.temporarily_unavailable,
            "max_stock": self.max_stock,
            "reserved": self.reserved,
            "available_stock": self.available_stock,
        }


@dataclass
class ProductBundle:
    """Represents a bundle of products sold together."""
    id: str
    name: str
    components: Dict[str, int] = field(default_factory=dict)  # product_id -> qty

    def to_dict(self):
        return {"id": self.id, "name": self.name, "components": self.components}


@dataclass
class Transaction:
    """Represents a completed transaction."""
    id: str = ""
    product_id: str = ""
    product_name: str = ""
    quantity: int = 0
    amount: float = 0.0
    status: str = "completed"  # completed, refunded, failed
    user_id: str = "USER001"
    pricing_used: str = "StandardPricing"
    mode_used: str = "active"

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def to_dict(self):
        return {
            "id": self.id, "product_id": self.product_id,
            "product_name": self.product_name, "quantity": self.quantity,
            "amount": self.amount, "status": self.status,
            "user_id": self.user_id,
            "pricing_used": self.pricing_used,
            "mode_used": self.mode_used,
        }
