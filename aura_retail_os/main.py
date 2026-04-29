"""
Aura Retail OS - Main Simulation
Demonstrates all 8 design patterns in action.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services import KioskInterface


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def run_simulation():
    """Run simulation scenarios demonstrating all patterns."""

    # ── Factory Pattern — create a pharmacy kiosk ─────────
    print_header("AURA RETAIL OS — FULL SIMULATION")
    kiosk = KioskInterface("pharmacy")
    print(f"Kiosk created: {kiosk.kiosk_id} at {kiosk.location}")
    print(f"Diagnostics: {kiosk.diagnostics()}")

    # ── Scenario 1: Normal Purchase (Command Pattern) ─────
    print_header("SCENARIO 1: Normal Purchase (Command Pattern)")
    result = kiosk.purchase_item("p1", 2, "USER001")
    print(f"Purchase result: {result}")
    print(f"Available stock after: {kiosk.inventory['p1'].available_stock}")

    # ── Scenario 2: Emergency Mode (State Pattern) ────────
    print_header("SCENARIO 2: Emergency Mode (State Pattern)")
    kiosk.change_mode("emergency")
    print(f"Mode: {kiosk.mode.name}")
    print(f"Pricing auto-switched to: {kiosk.pricing.__class__.__name__}")

    # Purchase within emergency limit
    result = kiosk.purchase_item("p1", 1, "USER002")
    print(f"Emergency purchase (1 item): {result}")

    # Exceed emergency limit
    result = kiosk.purchase_item("p1", 5, "USER002")
    print(f"Emergency purchase (5 items — exceeds limit): {result}")

    # ── Scenario 3: Power Saving Mode (State Pattern) ─────
    print_header("SCENARIO 3: Power Saving Mode (State Pattern)")
    kiosk.change_mode("power_saving")
    result = kiosk.purchase_item("p1", 1, "USER003")
    print(f"Power saving purchase attempt: {result}")

    # ── Scenario 4: Maintenance Mode (State Pattern) ──────
    print_header("SCENARIO 4: Maintenance Mode (State Pattern)")
    kiosk.change_mode("maintenance")
    result = kiosk.purchase_item("p1", 1, "USER003")
    print(f"Maintenance purchase attempt: {result}")

    # Back to active
    kiosk.change_mode("active")

    # ── Scenario 5: Dynamic Pricing (Strategy Pattern) ────
    print_header("SCENARIO 5: Dynamic Pricing (Strategy Pattern)")
    kiosk.change_pricing("discount")
    result = kiosk.purchase_item("p1", 1, "USER004")
    print(f"Discount purchase: {result}")
    kiosk.change_pricing("standard")

    # ── Scenario 6: Price Calculator (Strategy Pattern) ───
    print_header("SCENARIO 6: Price Calculator")
    for strat in ["standard", "discount", "emergency"]:
        kiosk.change_pricing(strat)
        calc = kiosk.calculate_price(100, 2)
        print(f"  {strat}: ₹100 × 2 = ₹{calc['final']}")
    kiosk.change_pricing("standard")

    # ── Scenario 7: Refund (Command Pattern) ──────────────
    print_header("SCENARIO 7: Refund Transaction (Command Pattern)")
    if kiosk.transactions:
        tx_id = kiosk.transactions[0].id
        result = kiosk.refund(tx_id)
        print(f"Refund result: {result}")

    # ── Scenario 8: Restock (Command Pattern) ─────────────
    print_header("SCENARIO 8: Restock Inventory (Command Pattern)")
    result = kiosk.restock("p1", 10)
    print(f"Restock result: {result}")

    # ── Scenario 9: Undo / Rollback (Memento Pattern) ─────
    print_header("SCENARIO 9: Undo Last Operation (Memento Pattern)")
    print(f"Stock before undo: {kiosk.inventory['p1'].stock}")
    result = kiosk._undo_last()
    print(f"Undo result: {result}")
    print(f"Stock after undo: {kiosk.inventory['p1'].stock}")

    # ── Scenario 10: Hardware Failure (Chain of Resp.) ────
    print_header("SCENARIO 10: Hardware Failure (Chain of Responsibility)")
    result = kiosk.simulate_hardware_fault("refrigeration")
    print(f"Hardware fault result: {result}")
    print(f"Insulin available? {kiosk.inventory['p2'].available_stock}")
    print(f"Operational status: {kiosk.diagnostics()['operational_status']}")

    # Repair
    result = kiosk.repair_hardware("refrigeration")
    print(f"Hardware repair result: {result}")
    print(f"Insulin available now? {kiosk.inventory['p2'].available_stock}")

    # ── Scenario 11: CSV Export (System Persistence) ──────
    print_header("SCENARIO 11: CSV Export (System Persistence)")
    csv_result = kiosk.export_csv()
    print(f"CSV exported: {csv_result['message']}")

    # ── Final Summary ─────────────────────────────────────
    print_header("FINAL SUMMARY")
    diag = kiosk.diagnostics()
    for key, val in diag.items():
        print(f"  {key}: {val}")

    print(f"\nEvent Log ({len(kiosk.get_events())} events):")
    for event in kiosk.get_events()[-10:]:
        print(f"  [{event['type']}] {event.get('data', {})}")

    print(f"\nTransactions ({len(kiosk.transactions)}):")
    for tx in kiosk.get_transactions():
        print(f"  TX-{tx['id']}: {tx['product_name']} ×{tx['quantity']} "
              f"= ₹{tx['amount']} [{tx['status']}] ({tx['pricing_used']})")


if __name__ == "__main__":
    run_simulation()
