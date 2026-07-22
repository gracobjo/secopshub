from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models import User
from app.utils.decorators import admin_required
from app.utils.helpers import log_action

users_bp = Blueprint("users", __name__)


@users_bp.route("", methods=["GET"])
@jwt_required()
@admin_required
def list_users():
    users = User.query.order_by(User.username.asc()).all()
    return jsonify([u.to_dict() for u in users]), 200


@users_bp.route("/<int:user_id>", methods=["PATCH"])
@jwt_required()
@admin_required
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json() or {}
    changes: list[str] = []

    if "role" in data:
        role = (data.get("role") or "").strip()
        if role not in ("admin", "analyst"):
            return jsonify({"error": "Rol inválido"}), 400
        if role != user.role:
            changes.append(f"role {user.role}→{role}")
            user.role = role

    if "is_active" in data:
        active = bool(data.get("is_active"))
        if active != user.is_active:
            changes.append(f"is_active {user.is_active}→{active}")
            user.is_active = active

    if "email" in data:
        email = (data.get("email") or "").strip()
        if email and email != user.email:
            if User.query.filter(User.email == email, User.id != user.id).first():
                return jsonify({"error": "Email ya en uso"}), 409
            changes.append(f"email→{email}")
            user.email = email

    if "password" in data and data.get("password"):
        password = data["password"]
        if len(password) < 8:
            return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400
        user.set_password(password)
        changes.append("password rotated")

    if not changes:
        return jsonify(user.to_dict()), 200

    db.session.commit()
    log_action("Usuario actualizado", f"{user.username}: {'; '.join(changes)}")
    return jsonify(user.to_dict()), 200
