from functools import wraps
from flask import request, abort, g
from app.models.user import User

def require_user(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Example: token in Authorization header `"Bearer <user_id>"`
        auth = request.headers.get("Authorization", "")
        try:
            token = auth.split()[1]
            user = User.query.get(int(token))   # replace with real JWT decode
        except Exception:
            abort(401, description="Missing or invalid token")
        g.current_user = user

        # Pull user_id from JSON, query, or header
        payload_id = (
            request.json.get("user_id")
            if request.is_json else None
        )
        if payload_id and payload_id != user.id:
            abort(403, description="User ID mismatch")
        return fn(*args, **kwargs)
    return wrapper