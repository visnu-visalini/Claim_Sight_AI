from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():

    app = Flask(__name__)

    CORS(app)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///claimsight.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from app.models.user import User
    from app.models.claim import Claim
    from app.models.claim_image import ClaimImage
    from app.routes.auth import auth_bp
    from app.routes.claims import claims_bp
    from app.routes.images import images_bp
    from app.routes.cost import cost_bp
    from app.routes.generate import generate_bp
    from app.routes.review import review_bp
    from app.routes.profile import profile_bp
    from app.routes.admin import admin_bp
    from app.routes.report import report_bp

    app.register_blueprint(auth_bp,    url_prefix="/api/auth")
    app.register_blueprint(claims_bp,  url_prefix="/api/claims")
    app.register_blueprint(images_bp,  url_prefix="/api/claims")
    app.register_blueprint(cost_bp,    url_prefix="/api/claims")
    app.register_blueprint(generate_bp, url_prefix="/api/claims")
    app.register_blueprint(review_bp,  url_prefix="/api/claims")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(admin_bp,   url_prefix="/api/admin")
    app.register_blueprint(report_bp,  url_prefix="/api/claims")

    with app.app_context():
        db.create_all()

        # Safe migration: add submitted_at column if it does not exist yet
        try:
            with db.engine.connect() as conn:
                conn.execute(
                    db.text("ALTER TABLE claims ADD COLUMN submitted_at DATETIME")
                )
                conn.commit()
        except Exception:
            pass  # Column already exists — safe to ignore

        # Safe migration: add role column to users if it does not exist yet
        try:
            with db.engine.connect() as conn:
                conn.execute(
                    db.text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'")
                )
                conn.commit()
        except Exception:
            pass  # Column already exists — safe to ignore

    return app