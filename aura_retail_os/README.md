# 🛒 Aura Retail OS — Adaptive Autonomous Kiosk System

> **Path A: Adaptive Autonomous System**
> A smart, pattern-driven kiosk management platform that demonstrates **8 Gang-of-Four design patterns** working together in a real-world retail simulation. Built with Python (Flask) backend and a responsive web dashboard.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Design Patterns Used](#-design-patterns-implemented-8)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Installation & Setup](#-installation--setup)
- [Running the Project](#-running-the-project)
- [API Endpoints](#-api-endpoints)
- [Class Diagram Reference](#-class-diagram-reference)
- [Simulation Demonstrations](#-simulation-demonstrations)
- [Dashboard Features](#-dashboard-features)
- [Data Persistence](#-data-persistence)
- [Team](#-team)

---

## 🔭 Overview

**Aura Retail OS** is an autonomous retail kiosk operating system designed for deployment in hospitals, metro stations, and disaster relief camps. The system manages inventory, processes transactions, handles hardware failures, and adapts its behavior dynamically based on operating conditions — all powered by clean, modular design patterns.

The system supports **3 kiosk types** (Pharmacy, Food, Emergency Relief), each with preset inventory, and provides a unified dashboard for monitoring, control, and simulation.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Dynamic Pricing** | Switch between Standard, Discount (-15%), and Emergency (+10%) pricing at runtime |
| **Adaptive Mode Switching** | Active, Power Saving, Maintenance, and Emergency modes with automatic behavior changes |
| **Atomic Transactions** | Thread-safe purchases with automatic rollback on payment/dispenser failure |
| **Event-Driven Architecture** | Priority-aware publish/subscribe system for real-time event propagation |
| **Inventory Rollback** | Snapshot-based undo system — restore inventory to any previous state |
| **Hardware Simulation** | Simulate and repair hardware module failures (refrigeration, dispenser, solar) |
| **Failure Recovery Chain** | Auto-retry → Recalibration → Technician Alert escalation pipeline |
| **Multi-Kiosk Support** | Factory-created kiosks with preset inventory per deployment type |
| **CSV Export** | Export inventory and transaction data as downloadable CSV files |
| **Real-time Dashboard** | Live web UI with auto-refresh, toast notifications, and interactive controls |

---

## 🧩 Design Patterns Implemented (8)

| # | Pattern | Module | Purpose | Key Classes |
|---|---------|--------|---------|-------------|
| 1 | **Strategy** | `patterns/` | Dynamic pricing — swap algorithms at runtime | `PricingStrategy`, `StandardPricing`, `DiscountPricing`, `EmergencyPricing` |
| 2 | **State** | `patterns/` | Kiosk operating modes — controls purchase eligibility | `KioskMode`, `ActiveMode`, `PowerSavingMode`, `MaintenanceMode`, `EmergencyMode` |
| 3 | **Command** | `patterns/` | Encapsulate operations for execute/undo | `Command`, `PurchaseCommand`, `RefundCommand`, `RestockCommand` |
| 4 | **Observer** | `patterns/` | Priority-aware event pub/sub system | `EventManager` |
| 5 | **Memento** | `patterns/` | Save/restore inventory snapshots for rollback | `InventoryMemento`, `MementoManager` |
| 6 | **Factory** | `patterns/` | Create kiosks from predefined presets | `KioskFactory` |
| 7 | **Singleton** | `patterns/` | Single global configuration registry | `CentralRegistry` |
| 8 | **Chain of Responsibility** | `patterns/` | Escalating failure recovery pipeline | `FailureHandler`, `RetryHandler`, `RecalibrationHandler`, `TechnicianAlertHandler` |

### How Patterns Connect

```
┌─────────────────────────────────────────────────────────────┐
│                    KioskInterface (Facade)                   │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────┐  │
│  │ Strategy │  │  State   │  │  Command  │  │ Observer  │  │
│  │ (Pricing)│  │  (Mode)  │  │(Purchase) │  │ (Events)  │  │
│  └──────────┘  └──────────┘  └───────────┘  └───────────┘  │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────┐  │
│  │ Memento  │  │ Factory  │  │ Singleton │  │  Chain of │  │
│  │(Rollback)│  │ (Kiosks) │  │(Registry) │  │   Resp.   │  │
│  └──────────┘  └──────────┘  └───────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗 System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Web Dashboard (UI)                        │
│                     ui/index.html                             │
│              HTML + CSS + Vanilla JavaScript                  │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP REST (JSON)
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   Flask REST API (api.py)                     │
│            Routes → /api/state, /api/purchase, etc.          │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              KioskInterface — Facade (services/)             │
│     Connects all 8 design patterns into a unified API        │
├──────────────────────────────────────────────────────────────┤
│  patterns/          │  models/           │  data/             │
│  • 8 Design Pattern │  • Product         │  • inventory.json  │
│    Implementations  │  • ProductBundle   │  • transactions.json│
│                     │  • Transaction     │  • csv_export/     │
└─────────────────────┴────────────────────┴───────────────────┘
```

---

## 📁 Project Structure

```
aura_retail_os/
├── main.py                  # CLI simulation — demonstrates all 11 scenarios
├── api.py                   # Flask REST API server + serves dashboard
├── requirements.txt         # Python dependencies (flask, flask-cors)
│
├── patterns/
│   └── __init__.py          # All 8 design pattern implementations (26 classes)
│
├── models/
│   └── __init__.py          # Data models: Product, ProductBundle, Transaction
│
├── services/
│   └── __init__.py          # KioskInterface — main Facade connecting all patterns
│
├── data/
│   ├── inventory.json       # Product catalog + bundles (JSON persistence)
│   ├── transactions.json    # Transaction history
│   └── csv_export/          # Exported CSV files
│       ├── inventory.csv
│       └── transactions.csv
│
└── ui/
    └── index.html           # Web dashboard (single-page app)
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, Flask, Flask-CORS |
| **Frontend** | HTML5, CSS3 (custom design system), Vanilla JavaScript |
| **Data Storage** | JSON files (inventory.json, transactions.json) |
| **Export** | CSV (inventory + transactions) |
| **Concurrency** | `threading.Lock` for atomic transactions |
| **Architecture** | Facade Pattern — all subsystems accessed via `KioskInterface` |

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- A modern web browser (Chrome, Firefox, Edge)

### Step 1: Clone the Repository

```bash
git clone https://github.com/TleEliminators/aura-retail-os.git
cd aura-retail-os/aura_retail_os
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `flask>=3.0` — Web framework for the REST API
- `flask-cors>=4.0` — Cross-Origin Resource Sharing support

### Step 3: Verify Data Files

Ensure these files exist in the `data/` directory:
- `inventory.json` — Contains 6 products and 2 bundles
- `transactions.json` — Transaction history (can be empty `[]`)

---

## ▶ Running the Project

### Option 1: Web Dashboard (Recommended)

```bash
python api.py
```

Output:
```
  === AURA RETAIL OS -- API Server ===
  http://localhost:5000
  =====================================
```

Open **http://localhost:5000** in your browser to access the interactive dashboard.

### Option 2: CLI Simulation

```bash
python main.py
```

Runs all 11 demonstration scenarios in sequence, printing results to the terminal. This is ideal for verifying all patterns work without a browser.

---

## 🌐 API Endpoints

### Kiosk Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/kiosks` | List all available kiosks |
| `POST` | `/api/kiosk/select` | Switch active kiosk `{id: "pharmacy-01"}` |

### State & Diagnostics
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/state` | Full system state (diagnostics, inventory, transactions, events) |
| `GET` | `/api/inventory` | Current inventory list |
| `GET` | `/api/bundles` | Product bundles with fulfillment status |
| `GET` | `/api/events` | Event log (Observer Pattern) |
| `GET` | `/api/registry` | Singleton registry snapshot |

### Transactions (Command Pattern)
| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `POST` | `/api/purchase` | `{pid, qty, uid}` | Purchase a product |
| `POST` | `/api/refund` | `{tid}` | Refund a transaction |
| `POST` | `/api/restock` | `{pid, qty}` | Restock a product |

### Mode & Pricing (State + Strategy)
| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `POST` | `/api/mode` | `{mode}` | Set mode: `active`, `power_saving`, `maintenance`, `emergency` |
| `POST` | `/api/pricing` | `{strategy}` | Set pricing: `standard`, `discount`, `emergency` |
| `POST` | `/api/price/calculate` | `{base, qty}` | Calculate price using active strategy |

### Hardware (Chain of Responsibility)
| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `POST` | `/api/hardware/fault` | `{module}` | Simulate hardware failure |
| `POST` | `/api/hardware/repair` | `{module}` | Repair a hardware module |

### System Operations
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/undo` | Rollback last operation (Memento Pattern) |
| `GET` | `/api/export/csv` | Export all data as CSV |
| `GET` | `/api/export/csv/inventory` | Download inventory CSV file |
| `GET` | `/api/export/csv/transactions` | Download transactions CSV file |
| `POST` | `/api/simulate` | Run simulation scenario `{scenario}` |

---

## 📐 Class Diagram Reference

### All 26 Classes (Grouped by Pattern)

**Strategy Pattern:**
- `PricingStrategy` (ABC) → `StandardPricing`, `DiscountPricing`, `EmergencyPricing`

**State Pattern:**
- `KioskMode` (ABC) → `ActiveMode`, `PowerSavingMode`, `MaintenanceMode`, `EmergencyMode`

**Command Pattern:**
- `Command` (ABC) → `PurchaseCommand`, `RefundCommand`, `RestockCommand`

**Observer Pattern:**
- `EventManager`

**Memento Pattern:**
- `InventoryMemento`, `MementoManager`

**Factory Pattern:**
- `KioskFactory`

**Singleton Pattern:**
- `CentralRegistry`

**Chain of Responsibility:**
- `FailureHandler` (ABC) → `RetryHandler`, `RecalibrationHandler`, `TechnicianAlertHandler`

**Data Models:**
- `Product`, `ProductBundle`, `Transaction`

**Facade:**
- `KioskInterface`

### Key Relationships

```
KioskInterface ──uses──▶ PricingStrategy (Strategy)
KioskInterface ──uses──▶ KioskMode (State)
KioskInterface ──uses──▶ EventManager (Observer)
KioskInterface ──uses──▶ MementoManager (Memento)
KioskInterface ──uses──▶ CentralRegistry (Singleton)
KioskInterface ──uses──▶ FailureHandler (Chain)
KioskInterface ──has───▶ Product, ProductBundle, Transaction
PurchaseCommand ─refs──▶ KioskInterface
FailureHandler ──next──▶ FailureHandler (self-referencing chain)
MementoManager ──has───▶ InventoryMemento
```

---

## 🎮 Simulation Demonstrations

### Running All Simulations (CLI)

```bash
python main.py
```

This runs **11 scenarios** end-to-end. Below is each scenario with expected output and which pattern it demonstrates.

---

### Scenario 1: Normal Purchase — `Command Pattern`

**What happens:** Creates a pharmacy kiosk and purchases 2 units of Paracetamol.

**Steps:**
1. `KioskFactory.create("pharmacy")` creates the kiosk (Factory)
2. `PurchaseCommand` wraps the operation (Command)
3. `StandardPricing.calculate(20, 2)` computes price (Strategy)
4. `MementoManager.save()` snapshots inventory before deduction (Memento)
5. Stock is deducted, transaction recorded, event published (Observer)

**Expected Output:**
```
Purchase result: {'success': True, 'product': 'Paracetamol', 'amount': 40.0, 'pricing': 'StandardPricing'}
```

---

### Scenario 2: Emergency Mode — `State Pattern`

**What happens:** Activates emergency mode, which auto-switches pricing to +10% and limits purchases to 2 items.

**Steps:**
1. `change_mode("emergency")` switches state to `EmergencyMode`
2. Pricing auto-changes to `EmergencyPricing` (adaptive behavior)
3. Purchase of 1 item succeeds (within limit)
4. Purchase of 5 items is rejected (exceeds limit of 2)

**Expected Output:**
```
Emergency purchase (1 item): {'success': True, 'amount': 22.0, 'pricing': 'EmergencyPricing'}
Emergency purchase (5 items): {'success': False, 'message': 'Emergency limit: max 2 items'}
```

---

### Scenario 3: Power Saving Mode — `State Pattern`

**What happens:** Switches to power saving mode — all purchases are blocked.

**Steps:**
1. `change_mode("power_saving")` sets state to `PowerSavingMode`
2. `PowerSavingMode.can_purchase()` returns `(False, "suspended")`
3. Purchase attempt is rejected

**Expected Output:**
```
Power saving purchase attempt: {'success': False, 'message': 'Kiosk is in power-saving mode...'}
```

---

### Scenario 4: Maintenance Mode — `State Pattern`

**What happens:** Switches to maintenance mode — all purchases blocked.

**Expected Output:**
```
Maintenance purchase attempt: {'success': False, 'message': 'Kiosk is under maintenance'}
```

---

### Scenario 5: Dynamic Pricing — `Strategy Pattern`

**What happens:** Switches pricing to Discount (-15%) and makes a purchase.

**Steps:**
1. `change_pricing("discount")` swaps strategy to `DiscountPricing`
2. `DiscountPricing.calculate(20, 1)` → `20 × 1 × 0.85 = ₹17.0`
3. Purchase records which strategy was used

**Expected Output:**
```
Discount purchase: {'success': True, 'amount': 17.0, 'pricing': 'DiscountPricing'}
```

---

### Scenario 6: Price Calculator — `Strategy Pattern`

**What happens:** Compares all 3 pricing strategies on the same product.

**Expected Output:**
```
  standard:  ₹100 × 2 = ₹200.0
  discount:  ₹100 × 2 = ₹170.0
  emergency: ₹100 × 2 = ₹220.0
```

---

### Scenario 7: Refund — `Command Pattern`

**What happens:** Refunds the first transaction, restoring stock.

**Steps:**
1. `RefundCommand` wraps the refund operation
2. Transaction status changes from `"completed"` → `"refunded"`
3. Product stock is restored
4. `REFUND` event is published (Observer)

**Expected Output:**
```
Refund result: {'success': True, 'transaction_id': 'abc12345'}
```

---

### Scenario 8: Restock — `Command Pattern`

**What happens:** Restocks a product by adding 10 units.

**Steps:**
1. `RestockCommand` wraps the operation
2. Inventory snapshot saved (Memento) before modification
3. Stock is increased, `RESTOCK` event published

**Expected Output:**
```
Restock result: {'success': True, 'new_stock': 28}
```

---

### Scenario 9: Undo / Rollback — `Memento Pattern`

**What happens:** Undoes the last operation by restoring the previous inventory snapshot.

**Steps:**
1. `MementoManager.restore()` pops the last `InventoryMemento`
2. Inventory state is replaced with the snapshot
3. `UNDO` event is published

**Expected Output:**
```
Stock before undo: 28
Undo result: {'success': True, 'message': 'Rolled back to previous state'}
Stock after undo: 18
```

---

### Scenario 10: Hardware Failure — `Chain of Responsibility`

**What happens:** Simulates a refrigeration module failure. Products requiring refrigeration (Insulin) become unavailable. The failure chain attempts recovery.

**Steps:**
1. `simulate_hardware_fault("refrigeration")` marks module OFFLINE
2. Products with `required_module: "refrigeration"` become unavailable
3. `HARDWARE_FAILURE` event published (Observer)
4. Chain processes: `RetryHandler` → `RecalibrationHandler` → `TechnicianAlertHandler`
5. `repair_hardware("refrigeration")` restores the module

**Expected Output:**
```
Hardware fault result: {'success': True, 'module': 'refrigeration', 'status': 'OFFLINE',
  'recovery': {'resolved': True, 'handler': 'RetryHandler'},
  'affected_products': ['Insulin']}
Insulin available? 0
Operational status: DEGRADED

Hardware repair result: {'success': True, 'module': 'refrigeration', 'status': 'ONLINE'}
Insulin available now? 15
```

---

### Scenario 11: CSV Export — `System Persistence`

**What happens:** Exports all inventory and transaction data as CSV files.

**Expected Output:**
```
CSV exported: CSV files exported to data/csv_export/
```

Generated files:
- `data/csv_export/inventory.csv`
- `data/csv_export/transactions.csv`

---

## 🖥 Dashboard Features

The web dashboard at `http://localhost:5000` provides interactive access to all features:

### Top Navigation Bar
- **Kiosk Tabs** — Switch between Pharmacy, Food, and Emergency kiosks (Factory Pattern)
- **Mode Badge** — Shows current operating mode with color coding
- **Undo Button** — Rollback last operation (Memento Pattern)
- **CSV Export** — Download inventory data

### Stats Bar (4 Metrics)
- **Mode** — Current kiosk mode (active/maintenance/emergency/power_saving)
- **Pricing** — Active pricing strategy
- **Transactions** — Total transaction count
- **Status** — Operational status (OPERATIONAL / DEGRADED / OFFLINE / RESTRICTED)

### System Diagnostics Panel (Facade Pattern)
- Hardware status, mode, pricing, purchase eligibility
- Total stock vs available stock
- Memento snapshot count
- Alert banners for blocked/emergency modes

### Mode Control (State Pattern)
- 4 clickable mode buttons: Active ⚡, Power Save 💤, Maintenance 🔧, Emergency 🚨
- Selecting emergency auto-switches pricing to Emergency (+10%)

### Pricing Control (Strategy Pattern)
- 3 clickable pricing buttons: Standard 📊, Discount 🏷, Emergency 🚨
- Active strategy highlighted

### Hardware Modules (Chain of Responsibility)
- Shows 3 modules: Refrigeration, Standard Dispenser, Solar
- **Break** button — simulates hardware failure
- **Repair** button — restores the module
- Affected products become unavailable in real time

### Purchase Form (Command Pattern)
- Product dropdown (shows price + available stock)
- Quantity input, User ID input
- **Buy Now** button (disabled in blocked modes)
- Toast notification on success/failure

### Inventory Grid (Factory Pattern)
- Visual product cards with emoji icons
- Stock bar (green/amber/red based on level)
- Available vs total stock display
- **Restock** button per product
- `⚠ HW UNAVAILABLE` badge for hardware-blocked products

### Transactions Panel (Command Pattern)
- Reverse-chronological list of all transactions
- Shows: TX ID, product, quantity, amount, status, pricing used, mode used
- **Refund** button on each completed transaction

### Rollback Panel (Memento Pattern)
- Shows current snapshot count
- **Undo Last Operation** button

### Events Log (Observer Pattern)
- Real-time event feed with color-coded dots
- Event types: PURCHASE, REFUND, RESTOCK, MODE_CHANGE, PRICING_CHANGE, HARDWARE_FAILURE, LOW_STOCK, EMERGENCY, TX_FAILED, UNDO

### Central Registry (Singleton Pattern)
- Displays global config: Currency (INR), Emergency Limit (2 items), Low Stock Alert (≤ 3)

---

## 💾 Data Persistence

### Inventory (`data/inventory.json`)

Contains **6 products** across 3 kiosk types and **2 bundles**:

| ID | Product | Price (₹) | Category | Kiosk | Hardware Dependency |
|----|---------|-----------|----------|-------|-------------------|
| p1 | Paracetamol | 20 | Essential | Pharmacy | None |
| p2 | Insulin | 150 | Premium | Pharmacy | Refrigeration |
| f1 | Sandwich | 50 | General | Food | None |
| f2 | Juice | 30 | General | Food | Refrigeration |
| e1 | Water Bottle | 10 | Essential | Emergency | None |
| e2 | Energy Bar | 15 | Essential | Emergency | None |

**Bundles:**
| ID | Bundle Name | Components |
|----|-------------|------------|
| b1 | First Aid Kit | 2× Paracetamol + 1× Insulin |
| b2 | Relief Pack | 2× Water Bottle + 2× Energy Bar |

### Transactions (`data/transactions.json`)

Each transaction records:
- Transaction ID (auto-generated UUID)
- Product ID and name
- Quantity and total amount
- Status: `completed` / `refunded` / `failed`
- User ID, pricing strategy used, kiosk mode at time of purchase

---

## 🏭 Kiosk Types

| Type | Kiosk ID | Location | Products |
|------|----------|----------|----------|
| **Pharmacy** | pharmacy-01 | City Hospital | Paracetamol, Insulin |
| **Food** | food-01 | Metro Station | Sandwich, Juice |
| **Emergency** | relief-01 | Relief Camp Sector 7 | Water Bottle, Energy Bar |

Each kiosk type is created using the **Factory Pattern** with predefined presets. Switch between kiosks using the navigation tabs in the dashboard.

---

## 🔒 Concurrency & Safety

- All purchase operations are protected by `threading.Lock` for thread safety
- **Atomic Transaction Flow:**
  1. Check mode allows purchase (State)
  2. Check emergency limits (Singleton config)
  3. Verify product exists and is available
  4. Check hardware dependency constraints
  5. Save inventory snapshot (Memento)
  6. Reserve inventory (prevents overselling)
  7. Calculate dynamic price (Strategy)
  8. Simulate payment (8% failure rate)
  9. Simulate dispensing (8% failure rate)
  10. On failure → Chain of Responsibility → Rollback reservation + Memento restore
  11. On success → Commit stock deduction, create Transaction, publish events

---

## 👥 Team

**Team Name:** TLE Eliminators

---

## 📄 License

This project is developed as an academic submission for demonstrating design pattern implementation in an adaptive autonomous system.
