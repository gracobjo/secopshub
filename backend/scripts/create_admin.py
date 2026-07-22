#!/usr/bin/env python3
"""CLI para crear el primer administrador (o uno adicional).

Uso (desde backend/):
  source venv/bin/activate
  python scripts/create_admin.py --username admin --email admin@secops.local
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys

# Permite ejecutar el script desde backend/ o backend/scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User


def main() -> int:
    parser = argparse.ArgumentParser(description="Crear usuario administrador")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--email", default="admin@secops.local")
    parser.add_argument(
        "--password",
        help="Si se omite, se solicita de forma interactiva",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Actualizar contraseña si el usuario ya existe",
    )
    args = parser.parse_args()

    password = args.password or getpass.getpass("Contraseña (mín. 12 caracteres): ")
    if len(password) < 12:
        print("ERROR: la contraseña debe tener al menos 12 caracteres", file=sys.stderr)
        return 1

    app = create_app()
    with app.app_context():
        existing = User.query.filter(
            (User.username == args.username) | (User.email == args.email)
        ).first()

        if existing:
            if not args.force:
                print(
                    f"ERROR: ya existe usuario '{existing.username}'. "
                    "Usa --force para actualizar la contraseña.",
                    file=sys.stderr,
                )
                return 1
            existing.set_password(password)
            existing.role = "admin"
            db.session.commit()
            print(f"OK: contraseña actualizada para '{existing.username}'")
            return 0

        user = User(username=args.username, email=args.email, role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"OK: administrador '{args.username}' creado")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
