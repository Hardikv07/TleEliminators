from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict


class CentralRegistry:
    """Singleton registry for global kiosk information."""

    _instance: "CentralRegistry | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "CentralRegistry":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_once()
        return cls._instance

    def _init_once(self) -> None:
        self.config: Dict[str, Any] = {
            "currency": "INR",
            "emergency_purchase_limit": 2,
            "low_stock_threshold": 3,
        }
        self.status: Dict[str, Any] = {
            "mode": "ActiveMode",
            "hardware_ok": True,
            "last_event": None,
        }
        self.kiosk_metadata: Dict[str, Any] = {}
        self._lock_instance = threading.RLock()

    def update_config(self, **kwargs: Any) -> None:
        with self._lock_instance:
            self.config.update(kwargs)

    def update_status(self, **kwargs: Any) -> None:
        with self._lock_instance:
            self.status.update(kwargs)

    def register_kiosk(self, kiosk_id: str, metadata: Dict[str, Any]) -> None:
        with self._lock_instance:
            self.kiosk_metadata[kiosk_id] = metadata

    def snapshot(self) -> Dict[str, Any]:
        with self._lock_instance:
            return {
                "config": dict(self.config),
                "status": dict(self.status),
                "kiosk_metadata": dict(self.kiosk_metadata),
            }

    def save(self, path: str | Path) -> None:
        with self._lock_instance:
            Path(path).write_text(json.dumps(self.snapshot(), indent=2), encoding="utf-8")

    def load(self, path: str | Path) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        with self._lock_instance:
            self.config = data.get("config", {})
            self.status = data.get("status", {})
            self.kiosk_metadata = data.get("kiosk_metadata", {})
