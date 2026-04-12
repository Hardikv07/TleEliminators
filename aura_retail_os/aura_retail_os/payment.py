from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict
import uuid


@dataclass
class PaymentReceipt:
    transaction_id: str
    amount: float
    provider: str
    success: bool
    message: str


class PaymentProvider(ABC):
    name: str = "PaymentProvider"

    @abstractmethod
    def authorize(self, amount: float) -> bool:
        raise NotImplementedError

    @abstractmethod
    def capture(self, amount: float) -> str:
        raise NotImplementedError

    @abstractmethod
    def refund(self, transaction_id: str, amount: float) -> bool:
        raise NotImplementedError


class MockUPIPaymentProvider(PaymentProvider):
    name = "UPI"

    def authorize(self, amount: float) -> bool:
        return True

    def capture(self, amount: float) -> str:
        return f"upi-{uuid.uuid4().hex[:8]}"

    def refund(self, transaction_id: str, amount: float) -> bool:
        return True


class MockCardPaymentProvider(PaymentProvider):
    name = "Card"

    def authorize(self, amount: float) -> bool:
        return amount > 0

    def capture(self, amount: float) -> str:
        return f"card-{uuid.uuid4().hex[:8]}"

    def refund(self, transaction_id: str, amount: float) -> bool:
        return True


class PaymentProcessor:
    def __init__(self, provider: PaymentProvider | None = None) -> None:
        self.provider = provider or MockUPIPaymentProvider()
        self.ledger: Dict[str, PaymentReceipt] = {}

    def set_provider(self, provider: PaymentProvider) -> None:
        self.provider = provider

    def charge(self, amount: float) -> PaymentReceipt:
        if not self.provider.authorize(amount):
            receipt = PaymentReceipt("", amount, self.provider.name, False, "Authorization failed")
            return receipt
        tx_id = self.provider.capture(amount)
        receipt = PaymentReceipt(tx_id, amount, self.provider.name, True, "Captured")
        self.ledger[tx_id] = receipt
        return receipt

    def refund(self, transaction_id: str) -> bool:
        receipt = self.ledger.get(transaction_id)
        if not receipt:
            return False
        ok = self.provider.refund(transaction_id, receipt.amount)
        if ok:
            receipt.success = False
            receipt.message = "Refunded"
        return ok
