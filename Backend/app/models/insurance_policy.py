from app import db
from datetime import datetime

class InsurancePolicy(db.Model):
    __tablename__ = "insurance_policies"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    provider = db.Column(db.String(100), nullable=True)
    policy_number = db.Column(db.String(100), nullable=True)
    policy_type = db.Column(db.String(50), nullable=True)  # Comprehensive / Third Party / Other
    start_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    coverage_type = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<InsurancePolicy {self.id} – {self.policy_number}>"

