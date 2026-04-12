from __future__ import annotations

from abc import ABC, abstractmethod


class PricingStrategy(ABC):
    @abstractmethod
    def compute_price(self, base_price: float, quantity: int = 1) -> float:
        raise NotImplementedError


class StandardPricing(PricingStrategy):
    def compute_price(self, base_price: float, quantity: int = 1) -> float:
        return round(base_price * quantity, 2)


class DiscountedPricing(PricingStrategy):
    def __init__(self, discount_rate: float = 0.15) -> None:
        self.discount_rate = discount_rate

    def compute_price(self, base_price: float, quantity: int = 1) -> float:
        return round(base_price * quantity * (1 - self.discount_rate), 2)


class EmergencyPricing(PricingStrategy):
    def __init__(self, markup_rate: float = 0.10) -> None:
        self.markup_rate = markup_rate

    def compute_price(self, base_price: float, quantity: int = 1) -> float:
        return round(base_price * quantity * (1 + self.markup_rate), 2)
