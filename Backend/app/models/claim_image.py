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

    def __repr__(self):
        return f"<ClaimImage {self.id} claim={self.claim_id}>"