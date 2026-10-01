from flask import Blueprint, request, jsonify

from app.models.claim import Claim
from app.models.claim_image import ClaimImage
from app.cost_estimation import estimate_claim


generate_bp = Blueprint("generate", __name__)


def build_summary(claim, images, cost):
    """
    Build a deterministic human-readable claim summary from existing data.
    Does NOT use any AI/LLM — purely template-based.
    """

    # Vehicle line
    year  = claim.vehicle_year  or "Unknown Year"
    make  = claim.vehicle_make  or "Unknown Make"
    model = claim.vehicle_model or "Unknown Model"
    vnum  = claim.vehicle_number or "N/A"

    vehicle_line = f"{year} {make} {model} (vehicle number {vnum})"

    # Accident line
    acc_date     = claim.accident_date.isoformat() if claim.accident_date else "an unknown date"
    acc_location = claim.accident_location or "an unknown location"

    # Damage line
    damaged_images = [img for img in images if img.damage_detected]

    if not damaged_images:
        damage_line = (
            "No damage was detected in the submitted vehicle images "
            "by the AI damage detection system."
        )
        cost_line = "No repair cost estimate is applicable."
    else:
        damage_descriptions = []
        for img in damaged_images:
            dtype = img.damage_type or "unknown damage"
            conf  = img.confidence
            if conf is not None:
                damage_descriptions.append(
                    f"{dtype} with {round(conf * 100)}% confidence"
                )
            else:
                damage_descriptions.append(dtype)

        if len(damage_descriptions) == 1:
            damage_line = (
                "The submitted vehicle images were analyzed using the AI damage "
                f"detection system. The detected damage includes {damage_descriptions[0]}."
            )
        else:
            joined = ", ".join(damage_descriptions[:-1]) + f", and {damage_descriptions[-1]}"
            damage_line = (
                "The submitted vehicle images were analyzed using the AI damage "
                f"detection system. The detected damages include {joined}."
            )

        # Cost line
        if cost["has_damage"] and cost["total_estimated_average"] > 0:
            min_cost = cost["total_estimated_min"]
            max_cost = cost["total_estimated_max"]
            avg_cost = cost["total_estimated_average"]
            cost_line = (
                f"The estimated repair cost is ₹{min_cost:,} to ₹{max_cost:,}, "
                f"with an estimated average of ₹{avg_cost:,}."
            )
        else:
            cost_line = (
                "The repair cost could not be fully estimated due to "
                "unrecognised damage types. Manual assessment is recommended."
            )

    summary = (
        f"Vehicle insurance claim for a {vehicle_line} "
        f"following an accident on {acc_date} at {acc_location}.\n\n"
        f"{damage_line}\n\n"
        f"{cost_line}\n\n"
        "This is an AI-assisted prototype assessment and requires "
        "verification by the insurer or an authorised assessor before "
        "any official claim decision is made."
    )

    return summary


@generate_bp.route("/<int:claim_id>/generate", methods=["GET"])
def generate_claim(claim_id):

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

    # Reuse existing cost estimation logic — no duplication
    cost = estimate_claim(images)

    # Build damage assessment items (all images, not just damaged ones)
    damage_items = []
    for img in images:
        item = {
            "image_id": img.id,
            "filename": img.filename,
            "damage_detected": img.damage_detected,
            "damage_type": img.damage_type,
            "confidence": img.confidence,
            "bounding_box": img.bounding_box,
            "image_url": (
                f"http://127.0.0.1:5000/api/claims/{claim_id}"
                f"/images/{img.id}/file"
            ),
        }
        damage_items.append(item)

    summary_text = build_summary(claim, images, cost)

    return jsonify({
        "success": True,
        "claim": {
            "claim_id": claim.id,
            "status": claim.status,
            "created_at": (
                claim.created_at.isoformat()
                if claim.created_at else None
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
                "damaged_images": sum(
                    1 for img in images if img.damage_detected
                ),
                "items": damage_items,
            },
            "cost_estimation": {
                "min": cost["total_estimated_min"],
                "max": cost["total_estimated_max"],
                "average": cost["total_estimated_average"],
                "has_unknown_damage": cost["has_unknown_damage"],
                "estimation_method": cost["estimation_method"],
            },
            "summary": summary_text,
        }
    }), 200
