# Aura Retail OS — Path A: Adaptive Autonomous System

A kiosk management system demonstrating **8 design patterns** with a clean, modular Python backend and a cyberpunk-themed web dashboard.

## 🧩 Design Patterns Used

| # | Pattern | Where | What it does |
|---|---------|-------|--------------|
| 1 | **Strategy** | `patterns/` → Pricing | Switch between Standard, Discount (-15%), Emergency (+10%) pricing |
| 2 | **State** | `patterns/` → KioskMode | Active (open), Maintenance (blocked), Emergency (limited) |
| 3 | **Command** | `patterns/` → PurchaseCommand, RefundCommand | Encapsulates operations for execute/undo |
| 4 | **Observer** | `patterns/` → EventManager | Publish/subscribe for LOW_STOCK, EMERGENCY, PURCHASE events |
| 5 | **Memento** | `patterns/` → InventoryMemento | Save inventory state before purchase, restore on failure |
| 6 | **Factory** | `patterns/` → KioskFactory | Create Pharmacy, Food, Emergency kiosks with presets |
| 7 | **Singleton** | `patterns/` → CentralRegistry | Single global config (emergency limits, thresholds) |
| 8 | **Chain of Responsibility** | `patterns/` → RetryHandler → AlertHandler | Handle failures: retry first, then alert technician |

## 📁 Project Structure

```
aura_retail_os/
├── main.py              # Simulation entry point (7 scenarios)
├── api.py               # Flask REST API + serves frontend
├── requirements.txt     # Python dependencies
├── models/
│   └── __init__.py      # Product, Transaction dataclasses
├── patterns/
│   └── __init__.py      # All 8 design patterns
├── services/
│   └── __init__.py      # KioskInterface (main facade)
├── data/
│   ├── inventory.json   # Product data (JSON persistence)
│   └── transactions.json# Transaction history
└── ui/
    └── index.html       # Web dashboard (HTML + JS)
```

## 🚀 How to Run

### Option 1: CLI Simulation
```bash
python main.py
```

### Option 2: Web Dashboard
```bash
pip install flask flask-cors
python api.py
```
Then open **http://localhost:5000** in your browser.

## 🎛️ KioskInterface Methods

| Method | Description |
|--------|-------------|
| `purchase_item(pid, qty)` | Buy a product (checks mode, stock, pricing) |
| `refund(transaction_id)` | Refund a completed transaction |
| `restock(pid, qty)` | Add stock to a product |
| `change_mode(mode)` | Switch to active/maintenance/emergency |
| `change_pricing(strategy)` | Switch to standard/discount/emergency pricing |
| `diagnostics()` | Get full system status |
| `_undo_last()` | Rollback to previous inventory state (Memento) |

## 📊 Sample Output (from `main.py`)

```
SCENARIO 1: Normal Purchase
Purchase result: {'success': True, 'product': 'Paracetamol', 'amount': 40.0, 'pricing': 'StandardPricing'}

SCENARIO 2: Emergency Mode Activation
Emergency purchase: {'success': True, 'amount': 22.0, 'pricing': 'EmergencyPricing'}
Excess purchase attempt: {'success': False, 'message': 'Emergency limit: max 2 items'}

SCENARIO 3: Maintenance Mode
Maintenance purchase attempt: {'success': False, 'message': 'Kiosk is under maintenance'}

SCENARIO 4: Dynamic Pricing
Discount purchase: {'success': True, 'amount': 17.0, 'pricing': 'DiscountPricing'}

SCENARIO 5: Refund Transaction
Refund result: {'success': True}

SCENARIO 6: Restock Inventory
Restock result: {'success': True, 'new_stock': 18}

SCENARIO 7: Undo Last Operation
Undo result: {'success': True, 'message': 'Rolled back to previous state'}
```

## 🏭 Kiosk Types

| Type | ID | Location | Products |
|------|----|----------|----------|
| Pharmacy | pharmacy-01 | City Hospital | Paracetamol, Insulin |
| Food | food-01 | Metro Station | Sandwich, Juice |
| Emergency | relief-01 | Relief Camp Sector 7 | Water Bottle, Energy Bar |
