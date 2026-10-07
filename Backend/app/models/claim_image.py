from app import db
from datetime import datetime


class ClaimImage(db.Model):
    __tablename__ = "claim_images"

    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey("claims.id"), nullable=False)

    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)

    # AI damage detection results
    damage_detected = db.Column(db.Boolean, default=False)
    damage_type = db.Column(db.String(100), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    bounding_box = db.Column(db.String(500), nullable=True)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Vehicle view — nullable for backward compatibility with existing rows
    # Valid values: front | back | left | right | top | None (legacy/unspecified)
    vehicle_view = db.Column(db.String(20), nullable=True)

    # OpenAI Vision second-opinion results (all nullable — existing rows unaffected)
    openai_available        = db.Column(db.Boolean,     nullable=True, default=False)
    openai_damage_present   = db.Column(db.Boolean,     nullable=True)
    openai_damage_type      = db.Column(db.String(100), nullable=True)
    openai_severity         = db.Column(db.String(50),  nullable=True)
    openai_affected_part    = db.Column(db.String(100), nullable=True)
    openai_assessment       = db.Column(db.Text,        nullable=True)
    openai_confidence       = db.Column(db.Float,       nullable=True)
    openai_agrees_with_yolo = db.Column(db.Boolean,     nullable=True)

    def __repr__(self):
        return f"<ClaimImage {self.id} claim={self.claim_id}>"