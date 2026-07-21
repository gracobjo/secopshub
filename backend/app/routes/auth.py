from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app import db
from app.models import User
from app.utils.decorators import admin_required
from app.utils.helpers import log_action

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Usuario y contraseña son obligatorios"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "username": user.username},
    )

    return jsonify({"access_token": token, "user": user.to_dict()}), 200


@auth_bp.route("/register", methods=["POST"])
@jwt_required()
@admin_required
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "analyst")

    if not username or not email or not password:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    if role not in ("admin", "analyst"):
        return jsonify({"error": "Rol inválido"}), 400

    if User.query.filter(
        (User.username == username) | (User.email == email)
    ).first():
        return jsonify({"error": "Usuario o email ya existen"}), 409

    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    log_action("Usuario registrado", f"Usuario {username} creado con rol {role}")

    return jsonify({"message": "Usuario creado", "user": user.to_dict()}), 201


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user.to_dict()), 200
