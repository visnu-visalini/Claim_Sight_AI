from flask import Blueprint, request, jsonify

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    # Temporary test credentials
    if email == "test@claimsight.ai" and password == "123456":

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "email": email,
                "name": "Test User"
            }
        }), 200

    return jsonify({
        "success": False,
        "message": "Invalid email or password"
    }), 401
