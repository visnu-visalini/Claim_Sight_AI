from app import db
from datetime import datetime


class Claim(db.Model):
    __tablename__ = "claims"

    id = db.Column(db.Integer, primary_key=True)

    # Link claim to the user who created it
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Claim status
    status = db.Column(db.String(50), nullable=False, default="draft")

    # Vehicle information
    vehicle_number = db.Column(db.String(50), nullable=True)
    vehicle_make = db.Column(db.String(100), nullable=True)
    vehicle_model = db.Column(db.String(100), nullable=True)
    vehicle_year = db.Column(db.Integer, nullable=True)

    # Accident information
    accident_date = db.Column(db.Date, nullable=True)
    accident_location = db.Column(db.String(255), nullable=True)
    accident_description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    submitted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Claim {self.id}>"