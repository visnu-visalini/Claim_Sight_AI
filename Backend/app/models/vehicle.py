from app import db
from datetime import datetime

class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Core vehicle fields (all optional to allow progressive onboarding)
    registration_number = db.Column(db.String(50), nullable=True)
    make = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    manufacturing_year = db.Column(db.Integer, nullable=True)
    vehicle_type = db.Column(db.String(50), nullable=True)
    fuel_type = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(30), nullable=True)
    chassis_number = db.Column(db.String(100), nullable=True)
    engine_number = db.Column(db.String(100), nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    previous_claim_history = db.Column(db.Text, nullable=True)  # free‑form JSON/string

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Vehicle {self.id} – {self.registration_number}>"

