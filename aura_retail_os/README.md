# Aura Retail OS — Path A Prototype

This is a complete object-oriented prototype for **Aura Retail OS**, based on the **Path A: Adaptive Autonomous System** brief in your project documents.

## Implemented design patterns

- **Singleton** — `CentralRegistry`
- **Abstract Factory / Factory Method** — kiosk factories for Pharmacy, Food, and Emergency Relief kiosks
- **Facade** — `KioskInterface`
- **Command** — `PurchaseItemCommand`, `RefundCommand`, `RestockCommand`
- **Strategy** — `StandardPricing`, `DiscountedPricing`, `EmergencyPricing`
- **State** — `ActiveMode`, `PowerSavingMode`, `MaintenanceMode`, `EmergencyLockdownMode`
- **Observer / Event Bus** — `EventBus`
- **Chain of Responsibility** — `RetryHandler -> RecalibrationHandler -> TechnicianAlertHandler`
- **Memento** — transaction rollback snapshots

## What it demonstrates

The prototype covers the Path A requirements from your subtask document:

- dynamic pricing changes at runtime
- emergency mode activation
- hardware failure recovery
- transaction rollback
- event-driven communication between subsystems
- persistence to JSON/CSV files

The brief also calls for a central Event Bus and a kiosk interface facade, which are reflected here. fileciteturn0file0

The main project brief also requires modular subsystems, persistence, and simplified external access through `KioskInterface`. fileciteturn0file1

## How to run

```bash
python main.py
```

## Project structure

- `aura_retail_os/registry.py` — central registry singleton
- `aura_retail_os/events.py` — event bus and system events
- `aura_retail_os/pricing.py` — pricing strategies
- `aura_retail_os/state.py` — kiosk modes
- `aura_retail_os/inventory.py` — inventory and bundles
- `aura_retail_os/payment.py` — payment abstraction
- `aura_retail_os/hardware.py` — dispenser and failure chain
- `aura_retail_os/commands.py` — command objects
- `aura_retail_os/kiosk.py` — kiosk core and facade
- `aura_retail_os/factories.py` — kiosk factories
- `aura_retail_os/simulation.py` — demo scenarios

## Notes

The code is written so you can extend it further for your final submission with extra screens, more detailed payment adapters, or additional hardware modules.
