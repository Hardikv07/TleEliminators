from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict
import copy


@dataclass
class Product:
    product_id: str
    name: str
    base_price: float
    stock: int
    essential: bool = False
    required_module: str | None = None
    temporarily_unavailable: bool = False


@dataclass
class ProductBundle:
    bundle_id: str
    name: str
    components: Dict[str, int] = field(default_factory=dict)  # id -> qty


class InventoryManager:
    def __init__(self) -> None:
        self.products: Dict[str, Product] = {}
        self.bundles: Dict[str, ProductBundle] = {}
        self.reserved: Dict[str, int] = {}

    def add_product(self, product: Product) -> None:
        self.products[product.product_id] = product

    def add_bundle(self, bundle: ProductBundle) -> None:
        self.bundles[bundle.bundle_id] = bundle

    def available_stock(self, product_id: str) -> int:
        product = self.products[product_id]
        reserved = self.reserved.get(product_id, 0)
        return max(0, product.stock - reserved)

    def can_fulfill_bundle(self, bundle_id: str) -> bool:
        bundle = self.bundles[bundle_id]
        for component_id, qty in bundle.components.items():
            if component_id in self.products:
                if self.available_stock(component_id) < qty:
                    return False
            elif component_id in self.bundles:
                if not self.can_fulfill_bundle(component_id):
                    return False
            else:
                return False
        return True

    def reserve(self, product_id: str, quantity: int) -> None:
        if self.available_stock(product_id) < quantity:
            raise ValueError(f"Insufficient stock for {product_id}")
        self.reserved[product_id] = self.reserved.get(product_id, 0) + quantity

    def commit_sale(self, product_id: str, quantity: int) -> None:
        product = self.products[product_id]
        reserved = self.reserved.get(product_id, 0)
        if reserved < quantity:
            raise ValueError("Nothing reserved to commit.")
        product.stock -= quantity
        self.reserved[product_id] = reserved - quantity
        if self.reserved[product_id] <= 0:
            self.reserved.pop(product_id, None)

    def release_reservation(self, product_id: str, quantity: int) -> None:
        reserved = self.reserved.get(product_id, 0)
        reserved -= quantity
        if reserved <= 0:
            self.reserved.pop(product_id, None)
        else:
            self.reserved[product_id] = reserved

    def restock(self, product_id: str, quantity: int) -> None:
        self.products[product_id].stock += quantity

    def mark_temporarily_unavailable(self, product_id: str, unavailable: bool = True) -> None:
        self.products[product_id].temporarily_unavailable = unavailable

    def snapshot(self) -> Dict[str, Any]:
        return {
            "products": copy.deepcopy(self.products),
            "bundles": copy.deepcopy(self.bundles),
            "reserved": copy.deepcopy(self.reserved),
        }

    def restore(self, snapshot: Dict[str, Any]) -> None:
        self.products = copy.deepcopy(snapshot["products"])
        self.bundles = copy.deepcopy(snapshot["bundles"])
        self.reserved = copy.deepcopy(snapshot["reserved"])

    def low_stock_products(self, threshold: int) -> list[Product]:
        return [p for p in self.products.values() if self.available_stock(p.product_id) <= threshold]
