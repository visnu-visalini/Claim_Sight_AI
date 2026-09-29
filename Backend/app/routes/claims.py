from flask import Blueprint, request, jsonify

from app import db
from app.models.claim import Claim
from app.models.user import User


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

    # Check whether the user exists
    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    # Create a new draft claim
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