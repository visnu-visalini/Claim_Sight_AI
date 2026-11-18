from flask import Blueprint, request, jsonify
from app import db
from app.models.vehicle import Vehicle
from app.models.insurance_policy import InsurancePolicy
from app.models.user import User
from datetime import datetime

onboarding_bp = Blueprint("onboarding", __name__)

# ---------- GET stored vehicle for a user ----------
@onboarding_bp.route("/vehicle", methods=["GET"])
def get_vehicle():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"success": False, "message": "User ID is required"}), 400
    vehicle = Vehicle.query.filter_by(user_id=user_id).first()
    if not vehicle:
        return jsonify({"success": True, "vehicle": None}), 200
    data = {
        "registration_number": vehicle.registration_number,
        "make": vehicle.make,
        "model": vehicle.model,
        "manufacturing_year": vehicle.manufacturing_year,
        "vehicle_type": vehicle.vehicle_type,
        "fuel_type": vehicle.fuel_type,
        "color": vehicle.color,
        "chassis_number": vehicle.chassis_number,
        "engine_number": vehicle.engine_number,
        "purchase_date": vehicle.purchase_date.isoformat() if vehicle.purchase_date else None,
        "previous_claim_history": vehicle.previous_claim_history,
    }
    return jsonify({"success": True, "vehicle": data}), 200

# ---------- POST save (or update) vehicle ----------
@onboarding_bp.route("/vehicle", methods=["POST"])
def save_vehicle():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "User ID is required"}), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    vehicle = Vehicle.query.filter_by(user_id=user_id).first()
    if not vehicle:
        vehicle = Vehicle(user_id=user_id)
        db.session.add(vehicle)
    # Update fields if present
    fields = [
        "registration_number",
        "make",
        "model",
        "manufacturing_year",
        "vehicle_type",
        "fuel_type",
        "color",
        "chassis_number",
        "engine_number",
        "purchase_date",
        "previous_claim_history",
    ]
    for f in fields:
        if f in data:
            if f == "purchase_date" and data[f]:
                try:
                    # Expect ISO date string (YYYY-MM-DD)
                    parsed = datetime.strptime(data[f], "%Y-%m-%d").date()
                except ValueError:
                    return jsonify({"success": False, "message": "purchase_date must be YYYY-MM-DD"}), 400
                setattr(vehicle, f, parsed)
            else:
                setattr(vehicle, f, data.get(f))
    db.session.commit()
    return jsonify({"success": True, "message": "Vehicle saved", "vehicle_id": vehicle.id}), 200

# ---------- POST save insurance policy ----------
@onboarding_bp.route("/insurance", methods=["POST"])
def save_insurance():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "User ID is required"}), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    policy = InsurancePolicy.query.filter_by(user_id=user_id).first()
    if not policy:
        policy = InsurancePolicy(user_id=user_id)
        db.session.add(policy)
    fields = ["provider", "policy_number", "policy_type", "start_date", "expiry_date", "coverage_type"]
    for f in fields:
        if f in data:
            if f in ["start_date", "expiry_date"] and data[f]:
                try:
                    parsed = datetime.strptime(data[f], "%Y-%m-%d").date()
                except ValueError:
                    return jsonify({"success": False, "message": f"{f} must be YYYY-MM-DD"}), 400
                setattr(policy, f, parsed)
            else:
                setattr(policy, f, data.get(f))
    db.session.commit()
    return jsonify({"success": True, "message": "Insurance policy saved", "policy_id": policy.id}), 200

# ---------- POST mark onboarding complete (or skip) ----------
@onboarding_bp.route("/complete", methods=["POST"])
def complete_onboarding():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "User ID is required"}), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    if hasattr(user, "onboarding_completed"):
        user.onboarding_completed = True
        db.session.commit()
        return jsonify({"success": True, "message": "Onboarding marked as completed"}), 200
    else:
        return jsonify({"success": False, "message": "Onboarding field missing in DB"}), 500
