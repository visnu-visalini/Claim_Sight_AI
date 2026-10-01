import os
import uuid

from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename

from app import db
from app.models.claim import Claim
from app.models.claim_image import ClaimImage
from app.ai_damage import detect_damage


images_bp = Blueprint("images", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_upload_dir():
    upload_dir = os.path.join(
        current_app.root_path,
        "..",
        "uploads",
        "claim_images"
    )

    os.makedirs(upload_dir, exist_ok=True)

    return os.path.abspath(upload_dir)


@images_bp.route("/<int:claim_id>/images", methods=["POST"])
def upload_images(claim_id):

    user_id = request.form.get("user_id", type=int)

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
            "message": "You are not authorized to upload images for this claim"
        }), 403

    files = request.files.getlist("images")

    if not files or all(f.filename == "" for f in files):
        return jsonify({
            "success": False,
            "message": "No images provided"
        }), 400

    upload_dir = get_upload_dir()
    saved = []

    for file in files:

        if file.filename == "":
            continue

        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "message": (
                    f"File '{file.filename}' is not allowed. "
                    "Only JPG, JPEG, PNG are accepted."
                )
            }), 400

        # Check file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)

        if size > MAX_FILE_SIZE:
            return jsonify({
                "success": False,
                "message": (
                    f"File '{file.filename}' exceeds "
                    "the 10MB size limit."
                )
            }), 400

        if size == 0:
            return jsonify({
                "success": False,
                "message": f"File '{file.filename}' is empty."
            }), 400

        # Generate unique filename
        ext = file.filename.rsplit(".", 1)[1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(upload_dir, safe_name)

        # Save uploaded image
        file.save(file_path)

        # Run AI damage detection
        try:
            detections = detect_damage(file_path)

        except Exception as e:
            return jsonify({
                "success": False,
                "message": "AI damage detection failed",
                "error": str(e)
            }), 500

        # Default values when no damage is detected
        damage_detected = len(detections) > 0
        damage_type = None
        confidence = None
        bounding_box = None

        # Select highest-confidence detection
        if detections:
            best_detection = max(
                detections,
                key=lambda detection: detection["confidence"]
            )

            damage_type = best_detection["damage_type"]
            confidence = best_detection["confidence"]
            bounding_box = str(
                best_detection["bounding_box"]
            )

        # Save image + AI result to database
        image_record = ClaimImage(
            claim_id=claim_id,
            filename=secure_filename(file.filename),
            file_path=file_path,
            damage_detected=damage_detected,
            damage_type=damage_type,
            confidence=confidence,
            bounding_box=bounding_box
        )

        db.session.add(image_record)
        db.session.flush()

        # Add result to API response
        saved.append({
            "id": image_record.id,
            "filename": image_record.filename,
            "file_path": file_path,
            "damage_detected": damage_detected,
            "damage_type": damage_type,
            "confidence": confidence,
            "bounding_box": bounding_box
        })

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Images uploaded and analyzed successfully",
        "images": saved
    }), 201


@images_bp.route("/<int:claim_id>/images", methods=["GET"])
def get_images(claim_id):

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
            "message": "You are not authorized to view images for this claim"
        }), 403

    images = ClaimImage.query.filter_by(claim_id=claim_id).all()

    return jsonify({
        "success": True,
        "images": [
            {
                "id": img.id,
                "filename": img.filename,
                "image_url": f"http://127.0.0.1:5000/api/claims/{claim_id}/images/{img.id}/file",
                "damage_detected": img.damage_detected,
                "damage_type": img.damage_type,
                "confidence": img.confidence,
                "bounding_box": img.bounding_box,
                "uploaded_at": (
                    img.uploaded_at.isoformat()
                    if img.uploaded_at else None
                )
            }
            for img in images
        ]
    }), 200


@images_bp.route("/<int:claim_id>/images/<int:image_id>/file", methods=["GET"])
def serve_image(claim_id, image_id):

    image = ClaimImage.query.filter_by(
        id=image_id,
        claim_id=claim_id
    ).first()

    if not image:
        return jsonify({
            "success": False,
            "message": "Image not found"
        }), 404

    if not os.path.exists(image.file_path):
        return jsonify({
            "success": False,
            "message": "Image file not found on server"
        }), 404

    return send_file(image.file_path)
