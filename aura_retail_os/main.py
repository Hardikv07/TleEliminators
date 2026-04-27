"""
Aura Retail OS - Main Simulation
Demonstrates all design patterns in action.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services import KioskInterface


def print_header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def run_simulation():
    """Run 3 simulation scenarios demonstrating all patterns."""

    # Factory Pattern - create a pharmacy kiosk
    print_header("AURA RETAIL OS - SIMULATION")
    kiosk = KioskInterface("pharmacy")
    print(f"Kiosk created: {kiosk.kiosk_id} at {kiosk.location}")
    print(f"Diagnostics: {kiosk.diagnostics()}")

    # ── Scenario 1: Normal Purchase ──────────────────────
    print_header("SCENARIO 1: Normal Purchase")
    result = kiosk.purchase_item("p1", 2)
    print(f"Purchase result: {result}")
    print(f"Stock after: {kiosk.inventory['p1'].stock}")

    # ── Scenario 2: Emergency Mode ───────────────────────
    print_header("SCENARIO 2: Emergency Mode Activation")
    kiosk.change_mode("emergency")
    print(f"Mode: {kiosk.mode.name}")
    print(f"Pricing: {kiosk.pricing.__class__.__name__}")

    # Try purchase in emergency (limited to 2 items)
    result = kiosk.purchase_item("p1", 1)
    print(f"Emergency purchase: {result}")

    # Try exceeding limit
    result = kiosk.purchase_item("p1", 5)
    print(f"Excess purchase attempt: {result}")

    # ── Scenario 3: Maintenance Mode (blocked) ──────────
    print_header("SCENARIO 3: Maintenance Mode")
    kiosk.change_mode("maintenance")
    result = kiosk.purchase_item("p1", 1)
    print(f"Maintenance purchase attempt: {result}")

    # Back to active
    kiosk.change_mode("active")

    # ── Scenario 4: Pricing Strategy Change ──────────────
    print_header("SCENARIO 4: Dynamic Pricing")
    kiosk.change_pricing("discount")
    result = kiosk.purchase_item("p1", 1)
    print(f"Discount purchase: {result}")
    kiosk.change_pricing("standard")

    # ── Scenario 5: Refund ───────────────────────────────
    print_header("SCENARIO 5: Refund Transaction")
    if kiosk.transactions:
        tx_id = kiosk.transactions[0].id
        result = kiosk.refund(tx_id)
        print(f"Refund result: {result}")

    # ── Scenario 6: Restock ──────────────────────────────
    print_header("SCENARIO 6: Restock Inventory")
    result = kiosk.restock("p1", 10)
    print(f"Restock result: {result}")

    # ── Scenario 7: Undo (Memento) ───────────────────────
    print_header("SCENARIO 7: Undo Last Operation")
    print(f"Stock before undo: {kiosk.inventory['p1'].stock}")
    result = kiosk._undo_last()
    print(f"Undo result: {result}")
    print(f"Stock after undo: {kiosk.inventory['p1'].stock}")

    # ── Final Summary ────────────────────────────────────
    print_header("FINAL SUMMARY")
    print(f"Diagnostics: {kiosk.diagnostics()}")
    print(f"\nEvent Log:")
    for event in kiosk.get_events():
        print(f"  [{event['type']}] {event.get('data', {})}")

    print(f"\nTransactions:")
    for tx in kiosk.get_transactions():
        print(f"  TX-{tx['id']}: {tx['product_name']} x{tx['quantity']} "
              f"= Rs.{tx['amount']} [{tx['status']}]")


if __name__ == "__main__":
    run_simulation()
