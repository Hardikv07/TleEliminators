from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
import copy


@dataclass
class TransactionSnapshot:
    inventory_state: Dict[str, Any]
    transaction_log: list[dict[str, Any]]
    active_transactions: Dict[str, Any]


class TransactionMemento:
    """Memento pattern: stores a snapshot for rollback."""

    def __init__(self, snapshot: TransactionSnapshot) -> None:
        self._snapshot = copy.deepcopy(snapshot)

    def get_snapshot(self) -> TransactionSnapshot:
        return copy.deepcopy(self._snapshot)
