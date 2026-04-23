#!/usr/bin/env python3
"""
add_user.py — Agrega o actualiza un usuario en users.json

Uso:
    python3 add_user.py <username> <password> <role>

Roles válidos: admin, operator, sensor

Ejemplo:
    python3 add_user.py juan secreto123 operator
"""

import sys
import json
import hashlib
import os

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
VALID_ROLES = {"admin", "operator", "sensor"}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def main():
    if len(sys.argv) != 4:
        print("Uso: python3 add_user.py <username> <password> <role>")
        print(f"Roles válidos: {', '.join(VALID_ROLES)}")
        sys.exit(1)

    username = sys.argv[1].strip()
    password = sys.argv[2]
    role     = sys.argv[3].strip().lower()

    if role not in VALID_ROLES:
        print(f"Error: rol '{role}' no válido. Usa: {', '.join(VALID_ROLES)}")
        sys.exit(1)

    # Cargar usuarios actuales
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}

    action = "Actualizado" if username in users else "Creado"
    users[username] = {
        "password": hash_password(password),
        "role": role
    }

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

    print(f"✅ {action}: usuario='{username}' rol='{role}'")


if __name__ == "__main__":
    main()