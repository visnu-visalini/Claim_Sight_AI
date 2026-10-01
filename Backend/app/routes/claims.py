from flask import Blueprint, request, jsonify

from app import db
from app.models.claim import Claim
from app.models.claim_image import ClaimImage
from app.models.user import User
from app.cost_estimation import estimate_claim


claims_bp = Blueprint("claims", __name__)


@claims_bp.route("/", methods=["POST"])
def create_claim():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request data is required"
        }), 400

    user_id = data.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "User ID is required"
        }), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    claim = Claim(
        user_id=user_id,
        status="draft"
    )

    db.session.add(claim)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Claim created successfully",
        "claim": {
            "id": claim.id,
            "user_id": claim.user_id,
            "status": claim.status
        }
    }), 201


@claims_bp.route("/<int:claim_id>", methods=["GET"])
def get_claim(claim_id):

    user_id = request.args.get("user_id", type=int)

    if not user_id:
        return jsonify({
            "success": False,
            "message": "User ID is required"
        }), 400

    claim = Claim.query.get(claim_id)

    if not claim:
        return jsonify({
            "success": False,
            "message": "Claim not found"
        }), 404

    if claim.user_id != user_id:
        return jsonify({
            "success": False,
            "message": "You are not authorized to access this claim"
        }), 403

    return jsonify({
        "success": True,
        "claim": {
            "id": claim.id,
            "user_id": claim.user_id,
            "status": claim.status,
            "vehicle_number": claim.vehicle_number,
            "vehicle_make": claim.vehicle_make,
            "vehicle_model": claim.vehicle_model,
            "vehicle_year": claim.vehicle_year,
            "accident_date": (
                claim.accident_date.isoformat()
                if claim.accident_date else None
            ),
            "accident_location": claim.accident_location,
            "accident_description": claim.accident_description,
            "created_at": (
                claim.created_at.isoformat()
                if claim.created_at else None
            ),
            "updated_at": (
                claim.updated_at.isoformat()
                if claim.updated_at else None
            )
        }
    }), 200


@claims_bp.route("/<int:claim_id>", methods=["PUT"])
def update_claim(claim_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request data is required"
        }), 400

    user_id = data.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "User ID is required"
        }), 400

    claim = Claim.query.get(claim_id)

    if not claim:
        return jsonify({
            "success": False,
            "message": "Claim not found"
        }), 404

    if claim.user_id != user_id:
        return jsonify({
            "success": False,
            "message": "You are not authorized to update this claim"
        }), 403

    # Vehicle information
    if "vehicle_number" in data:
        claim.vehicle_number = data.get("vehicle_number")

    if "vehicle_make" in data:
        claim.vehicle_make = data.get("vehicle_make")

    if "vehicle_model" in data:
        claim.vehicle_model = data.get("vehicle_model")

    if "vehicle_year" in data:
        claim.vehicle_year = data.get("vehicle_year")

    # Accident information
    if "accident_date" in data:
        from datetime import datetime

        accident_date = data.get("accident_date")

        if accident_date:
            try:
                claim.accident_date = datetime.strptime(
                    accident_date,
                    "%Y-%m-%d"
                ).date()
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "Accident date must be in YYYY-MM-DD format"
                }), 400
        else:
            claim.accident_date = None

    if "accident_location" in data:
        claim.accident_location = data.get("accident_location")

    if "accident_description" in data:
        claim.accident_description = data.get("accident_description")

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Claim updated successfully",
        "claim": {
            "id": claim.id,
            "user_id": claim.user_id,
            "status": claim.status,
            "vehicle_number": claim.vehicle_number,
            "vehicle_make": claim.vehicle_make,
            "vehicle_model": claim.vehicle_model,
            "vehicle_year": claim.vehicle_year,
            "accident_date": (
                claim.accident_date.isoformat()
                if claim.accident_date else None
            ),
            "accident_location": claim.accident_location,
            "accident_description": claim.accident_description
        }
    }), 200


@claims_bp.route("/my", methods=["GET"])
def get_my_claims():

    user_id = request.args.get("user_id", type=int)

    if not user_id:
        return jsonify({
            "success": False,
            "message": "user_id is required"
        }), 400

    claims = (
        Claim.query
        .filter_by(user_id=user_id)
        .order_by(Claim.created_at.desc())
        .all()
    )

    result = []

    for claim in claims:

        images = ClaimImage.query.filter_by(claim_id=claim.id).all()

        # Reuse existing cost estimation logic
        cost = estimate_claim(images)

        # Collect unique damage types from damaged images
        damage_types = list({
            img.damage_type
            for img in images
            if img.damage_detected and img.damage_type
        })

        result.append({
            "claim_id": claim.id,
            "status": claim.status,
            "created_at": (
                claim.created_at.isoformat()
                if claim.created_at else None
            ),
            "submitted_at": (
                claim.submitted_at.isoformat()
                if claim.submitted_at else None
            ),
            "vehicle": {
                "vehicle_number": claim.vehicle_number,
                "make": claim.vehicle_make,
                "model": claim.vehicle_model,
                "year": claim.vehicle_year,
            },
            "accident": {
                "date": (
                    claim.accident_date.isoformat()
                    if claim.accident_date else None
                ),
                "location": claim.accident_location,
            },
            "damage": {
                "has_damage": cost["has_damage"],
                "damage_types": damage_types,
                "image_count": len(images),
            },
            "cost_estimate": {
                "min": cost["total_estimated_min"],
                "max": cost["total_estimated_max"],
                "average": cost["total_estimated_average"],
            },
        })

    return jsonify({
        "success": True,
        "claims": result
    }), 200
