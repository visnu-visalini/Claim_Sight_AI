from datetime import datetime

from flask import Blueprint, request, jsonify

from app.models.claim import Claim
from app.models.claim_image import ClaimImage
from app.cost_estimation import estimate_claim
from app.routes.generate import build_summary
from app.ai_openai import get_agreement_state


review_bp = Blueprint("review", __name__)


def _ownership_checks(claim_id, user_id):
    """
    Shared validation used by both endpoints.
    Returns (claim, error_response, status_code).
    error_response is None when validation passes.
    """
    if not user_id:
        return None, {"success": False, "message": "user_id is required"}, 400

    claim = Claim.query.get(claim_id)

    if not claim:
        return None, {"success": False, "message": "Claim not found"}, 404

    if claim.user_id != user_id:
        return (
            None,
            {"success": False, "message": "You are not authorized to access this claim"},
            403,
        )

    return claim, None, None


def _assemble_claim_data(claim, images, cost):
    """Build the full claim dict shared by both review and generate."""
    # Build a lookup of combined assessment fields from cost damage_items
    cost_by_image = {item["image_id"]: item for item in cost.get("damage_items", [])}

    damage_items = []
    for img in images:
        cost_item = cost_by_image.get(img.id, {})
        damage_items.append({
            "image_id": img.id,
            "filename": img.filename,
            "damage_detected": img.damage_detected,
            "damage_type": img.damage_type,
            "confidence": img.confidence,
            "bounding_box": img.bounding_box,
            "image_url": (
                f"http://127.0.0.1:5000/api/claims/{claim.id}"
                f"/images/{img.id}/file"
            ),
            "openai_available":       img.openai_available,
            "openai_damage_present":  img.openai_damage_present,
            "openai_damage_type":     img.openai_damage_type,
            "openai_severity":        img.openai_severity,
            "openai_affected_part":   img.openai_affected_part,
            "openai_assessment":      img.openai_assessment,
            "openai_confidence":      img.openai_confidence,
            "openai_agrees_with_yolo": img.openai_agrees_with_yolo,
            "openai_agreement_state":  get_agreement_state(
                img.damage_type,
                img.openai_available,
                img.openai_agrees_with_yolo,
                img.openai_damage_type,
            ),
            # 50/50 combined assessment fields (from cost engine)
            "combined_damage_type": cost_item.get("combined_damage_type"),
            "combined_confidence":  cost_item.get("combined_confidence"),
            "yolo_weight":          cost_item.get("yolo_weight"),
            "openai_weight":        cost_item.get("openai_weight"),
            "combination_note":     cost_item.get("combination_note"),
        })

    return {
        "claim_id": claim.id,
        "status": claim.status,
        "created_at": (
            claim.created_at.isoformat() if claim.created_at else None
        ),
        "submitted_at": (
            claim.submitted_at.isoformat() if claim.submitted_at else None
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
            "description": claim.accident_description,
        },
        "damage_assessment": {
            "has_damage": cost["has_damage"],
            "total_images": len(images),
            "damaged_images": sum(1 for img in images if img.damage_detected),
            "items": damage_items,
        },
        "cost_estimation": {
            "min": cost["total_estimated_min"],
            "max": cost["total_estimated_max"],
            "average": cost["total_estimated_average"],
            "has_unknown_damage": cost["has_unknown_damage"],
            "estimation_method": cost["estimation_method"],
            "openai_adjustment_applied": cost.get("openai_adjustment_applied"),
            "openai_adjustment_factor":  cost.get("openai_adjustment_factor"),
            "openai_adjustment_reason":  cost.get("openai_adjustment_reason"),
        },
        "summary": build_summary(claim, images, cost),
    }


# ── GET /api/claims/<claim_id>/review ──────────────────────────────────────

@review_bp.route("/<int:claim_id>/review", methods=["GET"])
def get_claim_review(claim_id):

    user_id = request.args.get("user_id", type=int)
    claim, err, code = _ownership_checks(claim_id, user_id)

    if err:
        return jsonify(err), code

    images = ClaimImage.query.filter_by(claim_id=claim_id).all()
    cost = estimate_claim(images)
    claim_data = _assemble_claim_data(claim, images, cost)

    return jsonify({
        "success": True,
        "claim": claim_data
    }), 200


# ── POST /api/claims/<claim_id>/submit ─────────────────────────────────────

@review_bp.route("/<int:claim_id>/submit", methods=["POST"])
def submit_claim(claim_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required"
        }), 400

    user_id = data.get("user_id")
    claim, err, code = _ownership_checks(claim_id, user_id)

    if err:
        return jsonify(err), code

    if claim.status == "submitted":
        return jsonify({
            "success": False,
            "message": "Claim has already been submitted.",
            "claim_id": claim.id,
            "status": claim.status,
            "submitted_at": (
                claim.submitted_at.isoformat()
                if claim.submitted_at else None
            ),
        }), 409

    claim.status = "submitted"
    claim.submitted_at = datetime.utcnow()

    from app import db
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Claim submitted successfully.",
        "claim_id": claim.id,
        "status": claim.status,
        "submitted_at": claim.submitted_at.isoformat(),
    }), 200
