from datetime import datetime

from flask import Blueprint, request, jsonify

from app import db
from app.models.claim import Claim
from app.models.claim_image import ClaimImage
from app.models.user import User
from app.cost_estimation import estimate_claim


admin_bp = Blueprint("admin", __name__)

VALID_STATUSES = {"draft", "submitted", "approved", "rejected"}


def _verify_admin(user_id):
    """
    Returns (user, error_dict, status_code).
    error_dict is None when the user is a valid admin.
    """
    if not user_id:
        return None, {"success": False, "message": "user_id is required"}, 400

    user = User.query.get(user_id)

    if not user:
        return None, {"success": False, "message": "User not found"}, 404

    if user.role != "admin":
        return None, {"success": False, "message": "Access denied. Admins only."}, 403

    return user, None, None


def _serialize_claim(claim):
    """Build the full admin claim dict, reusing estimate_claim from cost_estimation."""
    images = ClaimImage.query.filter_by(claim_id=claim.id).all()
    cost = estimate_claim(images)

    claimant = User.query.get(claim.user_id)

    damage_types = list({
        img.damage_type
        for img in images
        if img.damage_detected and img.damage_type
    })

    return {
        "claim_id": claim.id,
        "status": claim.status,
        "created_at": claim.created_at.isoformat() if claim.created_at else None,
        "submitted_at": claim.submitted_at.isoformat() if claim.submitted_at else None,
        "claimant": {
            "id": claimant.id if claimant else None,
            "name": claimant.name if claimant else "Unknown",
            "email": claimant.email if claimant else "Unknown",
        },
        "vehicle": {
            "vehicle_number": claim.vehicle_number,
            "make": claim.vehicle_make,
            "model": claim.vehicle_model,
            "year": claim.vehicle_year,
        },
        "accident": {
            "date": claim.accident_date.isoformat() if claim.accident_date else None,
            "location": claim.accident_location,
            "description": claim.accident_description,
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
    }


# ── GET /api/admin/claims?user_id=<admin_id> ───────────────────────────────

@admin_bp.route("/claims", methods=["GET"])
def get_all_claims():

    user_id = request.args.get("user_id", type=int)
    _, err, code = _verify_admin(user_id)

    if err:
        return jsonify(err), code

    claims = Claim.query.order_by(Claim.created_at.desc()).all()

    return jsonify({
        "success": True,
        "claims": [_serialize_claim(c) for c in claims]
    }), 200


# ── GET /api/admin/stats?user_id=<admin_id> ────────────────────────────────

@admin_bp.route("/stats", methods=["GET"])
def get_stats():

    user_id = request.args.get("user_id", type=int)
    _, err, code = _verify_admin(user_id)

    if err:
        return jsonify(err), code

    total     = Claim.query.count()
    draft     = Claim.query.filter_by(status="draft").count()
    submitted = Claim.query.filter_by(status="submitted").count()
    approved  = Claim.query.filter_by(status="approved").count()
    rejected  = Claim.query.filter_by(status="rejected").count()

    return jsonify({
        "success": True,
        "stats": {
            "total_claims":     total,
            "draft_claims":     draft,
            "submitted_claims": submitted,
            "approved_claims":  approved,
            "rejected_claims":  rejected,
        }
    }), 200


# ── PUT /api/admin/claims/<claim_id>/status ────────────────────────────────

@admin_bp.route("/claims/<int:claim_id>/status", methods=["PUT"])
def update_claim_status(claim_id):

    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "Request body is required"}), 400

    user_id = data.get("user_id")
    _, err, code = _verify_admin(user_id)

    if err:
        return jsonify(err), code

    claim = Claim.query.get(claim_id)

    if not claim:
        return jsonify({"success": False, "message": "Claim not found"}), 404

    new_status = data.get("status", "").strip().lower()

    if new_status not in VALID_STATUSES:
        return jsonify({
            "success": False,
            "message": f"Invalid status. Allowed values: {', '.join(sorted(VALID_STATUSES))}"
        }), 400

    claim.status = new_status

    # Mirror the existing submit workflow: set submitted_at when moving to submitted
    if new_status == "submitted" and not claim.submitted_at:
        claim.submitted_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Claim status updated to '{new_status}'.",
        "claim_id": claim.id,
        "status": claim.status,
        "submitted_at": claim.submitted_at.isoformat() if claim.submitted_at else None,
    }), 200
