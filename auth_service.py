"""
SERVICIO EXTERNO DE AUTENTICACIÓN
Puerto: 9000
Este servicio es el único que conoce los usuarios y sus roles.
El servidor principal (C) lo consulta vía HTTP para validar credenciales.
"""

from flask import Flask, request, jsonify
import json
import hashlib
import os
import logging
from datetime import datetime

app = Flask(__name__)

# Configurar logging del servicio de auth
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AUTH] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("auth.log")
    ]
)
logger = logging.getLogger(__name__)

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def load_users():
    """Carga la base de usuarios desde el archivo JSON."""
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Archivo de usuarios no encontrado: {USERS_FILE}")
        return {}
    except json.JSONDecodeError:
        logger.error("Error al parsear users.json")
        return {}


def hash_password(password: str) -> str:
    """Hashea una contraseña con SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@app.route("/auth", methods=["POST"])
def authenticate():
    """
    Valida credenciales de un usuario.

    Body JSON:
        { "username": "...", "password": "..." }

    Respuesta exitosa:
        { "authenticated": true, "role": "operator", "username": "..." }

    Respuesta fallida:
        { "authenticated": false, "role": null }
    """
    data = request.get_json(silent=True)

    if not data:
        logger.warning("Petición sin cuerpo JSON")
        return jsonify({"authenticated": False, "role": None,
                        "error": "Body JSON requerido"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        logger.warning(f"Petición incompleta: username='{username}'")
        return jsonify({"authenticated": False, "role": None,
                        "error": "username y password requeridos"}), 400

    users = load_users()

    if username in users:
        user = users[username]
        if user["password"] == hash_password(password):
            logger.info(f"Login exitoso: {username} | rol={user['role']} | IP={request.remote_addr}")
            return jsonify({
                "authenticated": True,
                "role": user["role"],
                "username": username
            }), 200

    logger.warning(f"Login fallido: username='{username}' | IP={request.remote_addr}")
    return jsonify({"authenticated": False, "role": None}), 401


@app.route("/validate_role", methods=["POST"])
def validate_role():
    """
    Valida credenciales Y comprueba que el usuario tenga un rol específico.

    Body JSON:
        { "username": "...", "password": "...", "required_role": "operator" }

    Útil para que el servidor C compruebe si quien se conecta
    tiene permisos de operador o de sensor.
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"authorized": False, "error": "Body JSON requerido"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")
    required_role = data.get("required_role", "")

    users = load_users()

    if username in users:
        user = users[username]
        if user["password"] == hash_password(password):
            role = user["role"]
            authorized = (role == required_role or role == "admin")
            logger.info(
                f"validate_role: {username} rol={role} required={required_role} "
                f"authorized={authorized} IP={request.remote_addr}"
            )
            return jsonify({
                "authorized": authorized,
                "role": role,
                "username": username
            }), 200

    logger.warning(f"validate_role fallido: username='{username}' IP={request.remote_addr}")
    return jsonify({"authorized": False, "role": None}), 401


@app.route("/register", methods=["POST"])
def register():
    """
    Registra un nuevo usuario.

    Body JSON:
        { "username": "...", "password": "...", "role": "operator" }

    Roles permitidos al registrarse: operator, sensor
    (admin solo se crea manualmente con add_user.py)
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"registered": False, "error": "Body JSON requerido"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")
    role     = data.get("role", "operator").strip().lower()

    if not username or not password:
        return jsonify({"registered": False, "error": "username y password requeridos"}), 400

    if len(username) < 3:
        return jsonify({"registered": False, "error": "El usuario debe tener al menos 3 caracteres"}), 400

    if len(password) < 4:
        return jsonify({"registered": False, "error": "La contraseña debe tener al menos 4 caracteres"}), 400

    if role not in ("operator", "sensor"):
        role = "operator"

    users = load_users()

    if username in users:
        logger.warning(f"Registro fallido: usuario '{username}' ya existe")
        return jsonify({"registered": False, "error": "El usuario ya existe"}), 409

    users[username] = {"password": hash_password(password), "role": role}

    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)
    except Exception as e:
        logger.error(f"Error al guardar usuario: {e}")
        return jsonify({"registered": False, "error": "Error interno al guardar"}), 500

    logger.info(f"Usuario registrado: {username} rol={role} IP={request.remote_addr}")
    return jsonify({"registered": True, "username": username, "role": role}), 201


@app.route("/health", methods=["GET"])
def health():
    """Endpoint de comprobación de vida del servicio."""
    return jsonify({"status": "ok", "service": "auth", "timestamp": datetime.utcnow().isoformat()}), 200


@app.route("/users", methods=["GET"])
def list_users():
    """
    Lista usuarios y roles (SIN contraseñas).
    Solo para administración/debug.
    """
    users = load_users()
    safe = {u: {"role": data["role"]} for u, data in users.items()}
    return jsonify(safe), 200


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    logger.info(f"Servicio de autenticación iniciando en puerto {port}...")
    logger.info(f"Usuarios cargados: {list(load_users().keys())}")
    app.run(host="0.0.0.0", port=port, debug=False)