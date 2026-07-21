from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Acceso restringido a administradores"}), 403
        return fn(*args, **kwargs)

    return wrapper


def analyst_or_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") not in ("admin", "analyst"):
            return jsonify({"error": "Acceso no autorizado"}), 403
        return fn(*args, **kwargs)

    return wrapper
