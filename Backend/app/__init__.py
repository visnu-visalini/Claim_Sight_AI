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
    from app.routes.auth import auth_bp
    from app.routes.claims import claims_bp

    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth"
    )

    app.register_blueprint(
        claims_bp,
        url_prefix="/api/claims"
    )

    with app.app_context():
        db.create_all()

    return app