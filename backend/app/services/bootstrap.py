"""Bootstrap del primer administrador cuando la BD no tiene usuarios."""

from __future__ import annotations

import os
import sys

from app import db
from app.models import User


def bootstrap_admin_if_needed() -> User | None:
    """Crea un admin inicial desde variables de entorno si no hay usuarios.

    Variables:
      BOOTSTRAP_ADMIN_USERNAME (default: admin)
      BOOTSTRAP_ADMIN_EMAIL (default: admin@secops.local)
      BOOTSTRAP_ADMIN_PASSWORD (obligatoria para crear el usuario)
    """
    if User.query.first() is not None:
        return None

    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "").strip()
    if not password:
        print(
            "WARNING: No hay usuarios y BOOTSTRAP_ADMIN_PASSWORD no está definida. "
            "Crea un admin con: python scripts/create_admin.py",
            file=sys.stderr,
        )
        return None

    if len(password) < 12:
        raise RuntimeError(
            "BOOTSTRAP_ADMIN_PASSWORD debe tener al menos 12 caracteres"
        )

    username = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "admin").strip() or "admin"
    email = (
        os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@secops.local").strip()
        or "admin@secops.local"
    )

    admin = User(username=username, email=email, role="admin")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"INFO: Usuario administrador inicial creado: {username}")
    return admin
