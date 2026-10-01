from flask import Blueprint, request, jsonify

from app.models.claim import Claim
from app.models.claim_image import ClaimImage
from app.cost_estimation import estimate_claim


cost_bp = Blueprint("cost", __name__)


@cost_bp.route("/<int:claim_id>/cost", methods=["GET"])
def get_cost_estimate(claim_id):

    user_id = request.args.get("user_id", type=int)

    if not user_id:
        return jsonify({
            "success": False,
            "message": "user_id is required"
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
            "message": "You are not authorized to view this claim"
        }), 403

    images = ClaimImage.query.filter_by(claim_id=claim_id).all()

    estimate = estimate_claim(images)

    return jsonify({
        "success": True,
        "claim_id": claim_id,
        "estimate": estimate
    }), 200
