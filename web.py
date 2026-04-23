"""
web.py — Servidor HTTP del sistema IoT
Puerto: 8000

Interfaz web con:
  - Formulario de inicio de sesión
  - Validación de credenciales consultando auth_service (puerto 9000)
  - Panel de monitoreo (solo para usuarios autenticados)
  - Visualización de sensores activos y últimas mediciones
"""

import os
import json
import socket
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import hashlib
import secrets

# ──────────────────────────────────────────────
# CONFIGURACIÓN — sin IPs hardcodeadas
# ──────────────────────────────────────────────

AUTH_HOST  = os.environ.get("AUTH_HOST",   "127.0.0.1")
AUTH_PORT  = int(os.environ.get("AUTH_PORT", "9000"))

SERVER_HOST = os.environ.get("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8080"))

WEB_PORT   = int(os.environ.get("WEB_PORT", "8000"))

DATA_FILE  = "data.txt"

# Sesiones activas en memoria  {token: {"username": ..., "role": ...}}
SESSIONS: dict = {}


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def resolve_host(hostname: str) -> str:
    """Resuelve el hostname. Maneja excepción si falla DNS."""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror as e:
        print(f"[WEB] Advertencia: no se pudo resolver '{hostname}': {e}")
        return hostname   # intenta con el nombre igual (puede ser IP directa)


def query_auth_service(username: str, password: str) -> dict:
    """
    Consulta el servicio externo de autenticación.
    Retorna {"authenticated": bool, "role": str | None}
    """
    url = f"http://{resolve_host(AUTH_HOST)}:{AUTH_PORT}/auth"
    payload = json.dumps({"username": username, "password": password}).encode()

    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        print(f"[WEB] Error al contactar servicio de auth: {e}")
        return {"authenticated": False, "role": None, "error": str(e)}
    except Exception as e:
        print(f"[WEB] Error inesperado en auth: {e}")
        return {"authenticated": False, "role": None, "error": str(e)}


def call_register_service(username: str, password: str, role: str) -> dict:
    """Llama al endpoint /register del auth service."""
    url = f"http://{resolve_host(AUTH_HOST)}:{AUTH_PORT}/register"
    payload = json.dumps({"username": username, "password": password, "role": role}).encode()
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode())
        return {"registered": False, "error": body.get("error", str(e))}
    except Exception as e:
        return {"registered": False, "error": str(e)}


def read_sensor_data() -> str:
    try:
        with open(DATA_FILE, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "No hay datos de sensores aún."


def get_session(cookie_header: str) -> dict | None:
    """Busca sesión activa a partir del header Cookie."""
    if not cookie_header:
        return None
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith("session="):
            token = part[len("session="):]
            return SESSIONS.get(token)
    return None


# ──────────────────────────────────────────────
# HTML helpers
# ──────────────────────────────────────────────

SHARED_STYLES = """
    body { font-family: Arial, sans-serif; background: #1a1a2e; color: #eee;
           display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .box { background: #16213e; padding: 2rem 3rem; border-radius: 12px;
            box-shadow: 0 0 30px rgba(0,0,0,0.5); width: 320px; }
    h2 { text-align: center; color: #e94560; }
    input, select { width: 100%; padding: 10px; margin: 8px 0; border-radius: 6px;
             border: 1px solid #444; background: #0f3460; color: #eee; box-sizing: border-box; }
    button { width: 100%; padding: 10px; background: #e94560; border: none;
              color: white; border-radius: 6px; font-size: 1rem; cursor: pointer; margin-top: 10px; }
    button:hover { background: #c73652; }
    .link { text-align: center; margin-top: 1rem; font-size: 0.9rem; color: #aaa; }
    .link a { color: #e94560; text-decoration: none; }
    .success { color: #4caf50; font-weight: bold; text-align: center; }
    .error { color: #e94560; font-weight: bold; text-align: center; }
"""

def page_login(error: str = "") -> str:
    msg_html = f'<p class="error">{error}</p>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>IoT Monitor — Iniciar sesión</title>
  <style>{SHARED_STYLES}</style>
</head>
<body>
  <div class="box">
    <h2>🌐 IoT Monitor</h2>
    {msg_html}
    <form method="POST" action="/login">
      <input type="text"     name="username" placeholder="Usuario" required>
      <input type="password" name="password" placeholder="Contraseña" required>
      <button type="submit">Iniciar sesión</button>
    </form>
    <div class="link">¿No tienes cuenta? <a href="/register">Regístrate</a></div>
  </div>
</body>
</html>"""


def page_register(error: str = "", success: str = "") -> str:
    msg_html = f'<p class="error">{error}</p>' if error else ""
    if success:
        msg_html = f'<p class="success">{success}</p>'
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>IoT Monitor — Registro</title>
  <style>{SHARED_STYLES}</style>
</head>
<body>
  <div class="box">
    <h2>📝 Registro</h2>
    {msg_html}
    <form method="POST" action="/register">
      <input type="text"     name="username" placeholder="Usuario (mín. 3 caracteres)" required>
      <input type="password" name="password" placeholder="Contraseña (mín. 4 caracteres)" required>
      <input type="password" name="password2" placeholder="Repetir contraseña" required>
      <select name="role">
        <option value="operator">Operador</option>
        <option value="sensor">Sensor</option>
      </select>
      <button type="submit">Crear cuenta</button>
    </form>
    <div class="link"><a href="/">← Volver al login</a></div>
  </div>
</body>
</html>"""


def page_dashboard(username: str, role: str, data: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="3">
  <title>IoT Monitor — Panel</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; margin: 0; padding: 0; }}
    header {{ background: #16213e; padding: 1rem 2rem; display: flex;
              justify-content: space-between; align-items: center; }}
    header h1 {{ color: #e94560; margin: 0; }}
    .badge {{ background: #0f3460; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; }}
    main {{ padding: 2rem; }}
    .card {{ background: #16213e; border-radius: 10px; padding: 1.5rem; margin-bottom: 1rem;
             box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
    .card h2 {{ color: #e94560; margin-top: 0; }}
    pre {{ background: #0f3460; padding: 1rem; border-radius: 6px;
           font-size: 1rem; white-space: pre-wrap; }}
    a {{ color: #e94560; text-decoration: none; }}
  </style>
</head>
<body>
  <header>
    <h1>🌐 IoT Monitor</h1>
    <span class="badge">👤 {username} &nbsp;|&nbsp; 🔖 {role} &nbsp;|&nbsp; <a href="/logout">Salir</a></span>
  </header>
  <main>
    <div class="card">
      <h2>📡 Estado del sistema</h2>
      <pre>{data}</pre>
      <small style="color:#888">Se actualiza cada 3 segundos</small>
    </div>
  </main>
</body>
</html>"""


# ──────────────────────────────────────────────
# Handler HTTP
# ──────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        """Silencia los logs por defecto de BaseHTTPRequestHandler (usamos el nuestro)."""
        print(f"[WEB] {self.client_address[0]}:{self.client_address[1]} — " + fmt % args)

    # ── GET ──────────────────────────────────────────────────────
    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path

        session = get_session(self.headers.get("Cookie", ""))

        if path == "/logout":
            cookie = self.headers.get("Cookie", "")
            for part in cookie.split(";"):
                part = part.strip()
                if part.startswith("session="):
                    SESSIONS.pop(part[len("session="):], None)
            self._redirect("/")
            return

        if path == "/register":
            self._send_html(page_register())
            return

        if path == "/":
            if session:
                self._send_html(page_dashboard(
                    session["username"], session["role"], read_sensor_data()
                ))
            else:
                self._send_html(page_login())
            return

        self._send_html("<h1>404</h1>", code=404)

    # ── POST ─────────────────────────────────────────────────────
    def do_POST(self):
        if self.path == "/register":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length).decode()
            params = parse_qs(body)

            username  = params.get("username",  [""])[0].strip()
            password  = params.get("password",  [""])[0]
            password2 = params.get("password2", [""])[0]
            role      = params.get("role",      ["operator"])[0]

            if password != password2:
                self._send_html(page_register(error="Las contraseñas no coinciden."))
                return

            result = call_register_service(username, password, role)

            if result.get("registered"):
                self._send_html(page_register(
                    success=f"✅ Usuario '{username}' creado. <a href='/'>Inicia sesión</a>"
                ))
            else:
                self._send_html(page_register(error=result.get("error", "Error al registrar.")))
            return

        if self.path == "/login":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length).decode()
            params = parse_qs(body)

            username = params.get("username", [""])[0].strip()
            password = params.get("password", [""])[0]

            if not username or not password:
                self._send_html(page_login("Usuario y contraseña requeridos."))
                return

            # ── Consultar servicio externo de autenticación ──
            auth = query_auth_service(username, password)

            if auth.get("authenticated"):
                token = secrets.token_hex(32)
                SESSIONS[token] = {
                    "username": auth["username"],
                    "role":     auth.get("role", "unknown")
                }
                self.send_response(303)
                self.send_header("Location", "/")
                self.send_header("Set-Cookie",
                    f"session={token}; Path=/; HttpOnly; SameSite=Strict")
                self.end_headers()
            else:
                error_msg = auth.get("error", "")
                if "connect" in error_msg.lower() or "URLError" in error_msg:
                    msg = "Servicio de autenticación no disponible. Intente más tarde."
                else:
                    msg = "Usuario o contraseña incorrectos."
                self._send_html(page_login(msg))
            return

            if auth.get("authenticated"):
                token = secrets.token_hex(32)
                SESSIONS[token] = {
                    "username": auth["username"],
                    "role":     auth.get("role", "unknown")
                }
                self.send_response(303)
                self.send_header("Location", "/")
                self.send_header("Set-Cookie",
                    f"session={token}; Path=/; HttpOnly; SameSite=Strict")
                self.end_headers()
            else:
                error_msg = auth.get("error", "")
                if "connect" in error_msg.lower() or "URLError" in error_msg:
                    msg = "Servicio de autenticación no disponible. Intente más tarde."
                else:
                    msg = "Usuario o contraseña incorrectos."
                self._send_html(page_login(msg))
            return

        self._send_html("<h1>405 Method Not Allowed</h1>", code=405)

    # ── Helpers ──────────────────────────────────────────────────
    def _send_html(self, html: str, code: int = 200):
        data = html.encode()
        self.send_response(code)
        self.send_header("Content-Type",   "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location: str):
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print(f"[WEB] Servidor HTTP iniciando en puerto {WEB_PORT}...")
    print(f"[WEB] Servicio de auth: {AUTH_HOST}:{AUTH_PORT}")
    server = HTTPServer(("0.0.0.0", WEB_PORT), Handler)
    server.serve_forever()