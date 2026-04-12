from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class Command(ABC):
    @abstractmethod
    def execute(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def undo(self) -> Any:
        raise NotImplementedError


@dataclass
class PurchaseItemCommand(Command):
    kiosk: Any
    product_id: str
    quantity: int
    user_id: str

    def execute(self) -> Any:
        return self.kiosk._execute_purchase(self.product_id, self.quantity, self.user_id)

    def undo(self) -> Any:
        return self.kiosk._undo_last_purchase()


@dataclass
class RefundCommand(Command):
    kiosk: Any
    transaction_id: str

    def execute(self) -> Any:
        return self.kiosk._execute_refund(self.transaction_id)

    def undo(self) -> Any:
        return None


@dataclass
class RestockCommand(Command):
    kiosk: Any
    product_id: str
    quantity: int

    def execute(self) -> Any:
        return self.kiosk._execute_restock(self.product_id, self.quantity)

    def undo(self) -> Any:
        return self.kiosk._undo_restock(self.product_id, self.quantity)
