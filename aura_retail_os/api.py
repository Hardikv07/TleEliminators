"""
Aura Retail OS - Flask REST API
Serves the frontend and provides API endpoints for all subsystems.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from services import KioskInterface

app = Flask(__name__)
CORS(app)

# ── Create kiosks using Factory Pattern ───────────────────
kiosks = {
    "pharmacy-01": KioskInterface("pharmacy"),
    "food-01": KioskInterface("food"),
    "relief-01": KioskInterface("emergency"),
}
active_id = "pharmacy-01"

def get_kiosk():
    return kiosks[active_id]

# ══════════════════════════════════════════════════════════
# FRONTEND SERVING
# ══════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory("ui", "index.html")

# ══════════════════════════════════════════════════════════
# KIOSK MANAGEMENT
# ══════════════════════════════════════════════════════════

@app.route("/api/kiosks")
def list_kiosks():
    return jsonify([{"id": k.kiosk_id, "type": k.kiosk_type,
                     "location": k.location} for k in kiosks.values()])

@app.route("/api/kiosk/select", methods=["POST"])
def select_kiosk():
    global active_id
    kid = (request.json or {}).get("id")
    if kid in kiosks:
        active_id = kid
        return jsonify({"status": "ok", "active": active_id})
    return jsonify({"error": "Not found"}), 404

# ══════════════════════════════════════════════════════════
# STATE & DIAGNOSTICS
# ══════════════════════════════════════════════════════════

@app.route("/api/state")
def get_state():
    k = get_kiosk()
    diag = k.diagnostics()
    return jsonify({
        "diagnostics": diag,
        "inventory": k.get_inventory(),
        "bundles": k.get_bundles(),
        "transactions": k.get_transactions(),
        "events": k.get_events(),
        "mode": k.mode.name,
        "pricing": k.pricing.__class__.__name__,
        "hardware_modules": k.hardware_modules,
    })

@app.route("/api/inventory")
def get_inventory():
    return jsonify(get_kiosk().get_inventory())

@app.route("/api/bundles")
def get_bundles():
    return jsonify(get_kiosk().get_bundles())

# ══════════════════════════════════════════════════════════
# CORE TRANSACTIONS (Command Pattern)
# ══════════════════════════════════════════════════════════

@app.route("/api/purchase", methods=["POST"])
def purchase():
    d = request.json or {}
    result = get_kiosk().purchase_item(
        d.get("pid"), int(d.get("qty", 1)), d.get("uid", "USER001"))
    return jsonify(result), 200 if result.get("success") else 400

@app.route("/api/refund", methods=["POST"])
def refund():
    tid = (request.json or {}).get("tid")
    result = get_kiosk().refund(tid)
    return jsonify(result), 200 if result.get("success") else 400

@app.route("/api/restock", methods=["POST"])
def restock():
    d = request.json or {}
    result = get_kiosk().restock(d.get("pid"), int(d.get("qty", 5)))
    return jsonify(result), 200 if result.get("success") else 400

# ══════════════════════════════════════════════════════════
# MODE & PRICING (State + Strategy Patterns)
# ══════════════════════════════════════════════════════════

@app.route("/api/mode", methods=["POST"])
def set_mode():
    mode = (request.json or {}).get("mode")
    result = get_kiosk().change_mode(mode)
    return jsonify(result)

@app.route("/api/pricing", methods=["POST"])
def set_pricing():
    strat = (request.json or {}).get("strategy")
    result = get_kiosk().change_pricing(strat)
    return jsonify(result)

# ══════════════════════════════════════════════════════════
# PRICE CALCULATOR (Strategy Pattern)
# ══════════════════════════════════════════════════════════

@app.route("/api/price/calculate", methods=["POST"])
def calc_price():
    d = request.json or {}
    base = float(d.get("base", 100))
    qty = int(d.get("qty", 1))
    result = get_kiosk().calculate_price(base, qty)
    return jsonify(result)

# ══════════════════════════════════════════════════════════
# UNDO / ROLLBACK (Memento Pattern)
# ══════════════════════════════════════════════════════════

@app.route("/api/undo", methods=["POST"])
def undo():
    result = get_kiosk()._undo_last()
    return jsonify(result)

# ══════════════════════════════════════════════════════════
# EVENT LOG (Observer Pattern)
# ══════════════════════════════════════════════════════════

@app.route("/api/events")
def events():
    return jsonify(get_kiosk().get_events())

# ══════════════════════════════════════════════════════════
# HARDWARE SIMULATION (Chain of Responsibility)
# ══════════════════════════════════════════════════════════

@app.route("/api/hardware/fault", methods=["POST"])
def hardware_fault():
    module = (request.json or {}).get("module", "refrigeration")
    result = get_kiosk().simulate_hardware_fault(module)
    return jsonify(result)

@app.route("/api/hardware/repair", methods=["POST"])
def hardware_repair():
    module = (request.json or {}).get("module", "refrigeration")
    result = get_kiosk().repair_hardware(module)
    return jsonify(result)

# ══════════════════════════════════════════════════════════
# CSV EXPORT (System Persistence)
# ══════════════════════════════════════════════════════════

@app.route("/api/export/csv")
def export_csv():
    result = get_kiosk().export_csv()
    return jsonify(result)

@app.route("/api/export/csv/inventory")
def export_csv_inventory():
    result = get_kiosk().export_csv()
    return Response(result["inventory_csv"], mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=inventory.csv"})

@app.route("/api/export/csv/transactions")
def export_csv_transactions():
    result = get_kiosk().export_csv()
    return Response(result["transactions_csv"], mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=transactions.csv"})

# ══════════════════════════════════════════════════════════
# SIMULATION SCENARIOS
# ══════════════════════════════════════════════════════════

@app.route("/api/simulate", methods=["POST"])
def simulate():
    scenario = (request.json or {}).get("scenario", "emergency")
    result = get_kiosk().run_simulation(scenario)
    return jsonify(result)

# ══════════════════════════════════════════════════════════
# REGISTRY (Singleton)
# ══════════════════════════════════════════════════════════

@app.route("/api/registry")
def registry():
    from patterns import CentralRegistry
    return jsonify(CentralRegistry().snapshot())


if __name__ == "__main__":
    print("\n  === AURA RETAIL OS -- API Server ===")
    print("  http://localhost:5000")
    print("  =====================================\n")
    app.run(port=5000, debug=True)
