"""Models for Aura Retail OS."""
from dataclasses import dataclass, field
from typing import Dict, List, Any
import uuid


@dataclass
class Product:
    """Represents a product in the kiosk inventory."""
    id: str
    name: str
    price: float
    stock: int
    category: str = "general"  # general, essential, premium

    def to_dict(self):
        return {"id": self.id, "name": self.name, "price": self.price,
                "stock": self.stock, "category": self.category}


@dataclass
class Transaction:
    """Represents a completed transaction."""
    id: str = ""
    product_id: str = ""
    product_name: str = ""
    quantity: int = 0
    amount: float = 0.0
    status: str = "completed"  # completed, refunded, failed

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def to_dict(self):
        return {"id": self.id, "product_id": self.product_id,
                "product_name": self.product_name, "quantity": self.quantity,
                "amount": self.amount, "status": self.status}
