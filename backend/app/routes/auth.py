import secrets

import pyotp
from flask import Blueprint, current_app, jsonify, redirect, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import generate_password_hash

from app import db
from app.models import User
from app.services.auth_cookies import clear_auth_cookies, cookie_mode, json_with_cookies
from app.services.ldap_auth import authenticate_ldap, ldap_enabled
from app.services.oidc_auth import (
    build_authorize_url,
    exchange_code,
    oidc_enabled,
    profile_from_userinfo,
)
from app.utils.decorators import admin_required
from app.utils.helpers import log_action

auth_bp = Blueprint("auth", __name__)


def _issue_tokens(user: User) -> dict:
    claims = {"role": user.role, "username": user.username}
    return {
        "access_token": create_access_token(
            identity=str(user.id), additional_claims=claims
        ),
        "refresh_token": create_refresh_token(
            identity=str(user.id), additional_claims=claims
        ),
        "user": user.to_dict(),
    }


def _authenticate_local(username: str, password: str) -> User | None:
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return None
    return user


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    otp = (data.get("otp") or data.get("mfa_code") or "").strip()

    if not username or not password:
        return jsonify({"error": "Usuario y contraseña son obligatorios"}), 400

    user = _authenticate_local(username, password)
    auth_via = "local"

    if user is None and ldap_enabled():
        profile = authenticate_ldap(username, password)
        if profile:
            user = User.query.filter_by(username=profile["username"]).first()
            if not user:
                user = User(
                    username=profile["username"],
                    email=profile["email"],
                    role=profile.get("role", "analyst"),
                    auth_source="ldap",
                    is_active=True,
                )
                # Password local aleatorio (login vía LDAP)
                user.password_hash = generate_password_hash(secrets.token_urlsafe(32))
                db.session.add(user)
                db.session.commit()
            elif not user.is_active:
                return jsonify({"error": "Usuario desactivado"}), 403
            auth_via = "ldap"

    if user is None:
        return jsonify({"error": "Credenciales inválidas"}), 401

    if not user.is_active:
        return jsonify({"error": "Usuario desactivado"}), 403

    if user.mfa_enabled:
        if not otp:
            return (
                jsonify(
                    {
                        "mfa_required": True,
                        "message": "Se requiere código MFA (TOTP)",
                    }
                ),
                401,
            )
        totp = pyotp.TOTP(user.mfa_secret or "")
        if not totp.verify(otp, valid_window=1):
            return jsonify({"error": "Código MFA inválido"}), 401

    tokens = _issue_tokens(user)
    tokens["auth_via"] = auth_via
    return json_with_cookies(tokens, 200)


@auth_bp.route("/config", methods=["GET"])
def auth_config():
    return jsonify(
        {
            "cookie_mode": cookie_mode(),
            "oidc_enabled": oidc_enabled(),
            "ldap_enabled": ldap_enabled(),
            "four_eyes": bool(current_app.config.get("PLAYBOOK_FOUR_EYES", True)),
        }
    ), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"message": "Sesión cerrada"})
    return clear_auth_cookies(response), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user or not user.is_active:
        return jsonify({"error": "Usuario no válido"}), 401
    return json_with_cookies(_issue_tokens(user), 200)


@auth_bp.route("/oidc/login", methods=["GET"])
def oidc_login():
    if not oidc_enabled():
        return jsonify({"error": "OIDC no está habilitado"}), 404
    try:
        url = build_authorize_url()
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    return redirect(url)


@auth_bp.route("/oidc/callback", methods=["GET"])
def oidc_callback():
    if not oidc_enabled():
        return jsonify({"error": "OIDC no está habilitado"}), 404

    error = request.args.get("error")
    if error:
        return jsonify({"error": error, "description": request.args.get("error_description")}), 400

    code = request.args.get("code")
    state = request.args.get("state")
    if not code or not state:
        return jsonify({"error": "Faltan code/state"}), 400

    try:
        exchanged = exchange_code(code, state)
        profile = profile_from_userinfo(exchanged.get("userinfo") or {})
    except Exception as exc:
        return jsonify({"error": f"OIDC callback falló: {exc}"}), 400

    user = User.query.filter(
        (User.username == profile["username"]) | (User.email == profile["email"])
    ).first()
    if not user:
        user = User(
            username=profile["username"],
            email=profile["email"],
            role=profile.get("role", "analyst"),
            auth_source="oidc",
            is_active=True,
        )
        user.password_hash = generate_password_hash(secrets.token_urlsafe(32))
        db.session.add(user)
        db.session.commit()
    elif not user.is_active:
        return jsonify({"error": "Usuario desactivado"}), 403

    tokens = _issue_tokens(user)
    tokens["auth_via"] = "oidc"
    frontend = current_app.config.get("OIDC_FRONTEND_REDIRECT", "http://localhost:5173/")
    # Redirige al SPA con tokens en fragment (si no cookie) o limpio (si cookie)
    if cookie_mode():
        from app.services.auth_cookies import attach_auth_cookies

        response = redirect(frontend.rstrip("/") + "/")
        return attach_auth_cookies(
            response, tokens["access_token"], tokens["refresh_token"]
        )

    from urllib.parse import urlencode

    qs = urlencode(
        {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        }
    )
    return redirect(f"{frontend.rstrip('/')}/login?{qs}")


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

    if len(password) < 8:
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400

    if role not in ("admin", "analyst"):
        return jsonify({"error": "Rol inválido"}), 400

    if User.query.filter(
        (User.username == username) | (User.email == email)
    ).first():
        return jsonify({"error": "Usuario o email ya existen"}), 409

    user = User(username=username, email=email, role=role, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    log_action("Usuario registrado", f"Usuario {username} creado con rol {role}")

    return jsonify({"message": "Usuario creado", "user": user.to_dict()}), 201


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user.to_dict()), 200


@auth_bp.route("/mfa/setup", methods=["POST"])
@jwt_required()
def mfa_setup():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    secret = pyotp.random_base32()
    user.mfa_secret = secret
    user.mfa_enabled = False
    db.session.commit()

    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email or user.username,
        issuer_name="SecOps Hub",
    )
    return jsonify({"secret": secret, "otpauth_uri": uri, "mfa_enabled": False}), 200


@auth_bp.route("/mfa/enable", methods=["POST"])
@jwt_required()
def mfa_enable():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    data = request.get_json() or {}
    otp = (data.get("otp") or "").strip()

    if not user or not user.mfa_secret:
        return jsonify({"error": "Ejecuta /mfa/setup primero"}), 400
    if not pyotp.TOTP(user.mfa_secret).verify(otp, valid_window=1):
        return jsonify({"error": "Código MFA inválido"}), 400

    user.mfa_enabled = True
    db.session.commit()
    log_action("MFA activado", f"Usuario {user.username}")
    return jsonify({"message": "MFA activado", "user": user.to_dict()}), 200


@auth_bp.route("/mfa/disable", methods=["POST"])
@jwt_required()
def mfa_disable():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    data = request.get_json() or {}
    password = data.get("password", "")
    otp = (data.get("otp") or "").strip()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    if user.auth_source == "local" and not user.check_password(password):
        return jsonify({"error": "Contraseña incorrecta"}), 401
    if user.mfa_enabled and user.mfa_secret:
        if not pyotp.TOTP(user.mfa_secret).verify(otp, valid_window=1):
            return jsonify({"error": "Código MFA inválido"}), 400

    user.mfa_enabled = False
    user.mfa_secret = None
    db.session.commit()
    log_action("MFA desactivado", f"Usuario {user.username}")
    return jsonify({"message": "MFA desactivado", "user": user.to_dict()}), 200
