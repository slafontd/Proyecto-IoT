import os
import json
import socket
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import secrets

# CONFIG
AUTH_HOST = os.environ.get("AUTH_HOST", "auth.iot.local")
AUTH_PORT  = int(os.environ.get("AUTH_PORT", "9000"))

SERVER_HOST = os.environ.get("SERVER_HOST", "iot-server.local")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8080"))

WEB_PORT   = int(os.environ.get("WEB_PORT", "8000"))

SESSIONS = {}

# HELPERS

def resolve_host(hostname: str) -> str:
    try:
        return socket.gethostbyname(hostname)
    except:
        return hostname


def query_auth_service(username: str, password: str) -> dict:
    url = f"http://{resolve_host(AUTH_HOST)}:{AUTH_PORT}/auth"
    payload = json.dumps({"username": username, "password": password}).encode()

    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except:
        return {"authenticated": False}


def call_register_service(username: str, password: str, role: str) -> dict:
    url = f"http://{resolve_host(AUTH_HOST)}:{AUTH_PORT}/register"
    payload = json.dumps({
        "username": username,
        "password": password,
        "role": role
    }).encode()

    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except:
        return {"registered": False}


def read_sensor_data():
    try:
        s = socket.socket()
        s.connect((resolve_host(SERVER_HOST), SERVER_PORT))
        s.sendall(b"GET_STATUS\n")

        data = ""
        while True:
            part = s.recv(1024).decode()
            if not part:
                break
            data += part

        s.close()

        sensores_html = ""

        for line in data.split("\n"):
            if line.strip():
                parts = line.split()
                if len(parts) == 3:
                    sid, tipo, valor = parts
                    valor_int = int(valor)

                    color = "red" if valor_int > 80 else "lime"

                    sensores_html += f"""
                    <div class="sensor">
                        <b>{sid}</b> ({tipo})<br>
                        Valor: {valor}
                        <span style="color:{color}; font-size:20px">&#9679;</span>
                    </div>
                    """

        if sensores_html == "":
            sensores_html = "<p>No hay sensores activos</p>"

        return sensores_html

    except Exception as e:
        return f"<p>Error conectando con servidor: {e}</p>"


def get_session(cookie):
    if not cookie:
        return None
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith("session="):
            return SESSIONS.get(part.split("=")[1])
    return None


STYLE = """
body { font-family: Arial; background: #111; color: white; margin:0; }

header {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:15px;
    background:#0d1b2a;
}

.sensor {
    padding:15px;
    margin:15px;
    background:#222;
    border-radius:10px;
}

.box {
    background:#222;
    padding:20px;
    margin:40px auto;
    width:300px;
    border-radius:10px;
}

input, select {
    width:90%;
    padding:8px;
    margin:5px;
}

button {
    padding:10px;
    background:#0af;
    border:none;
    color:white;
    cursor:pointer;
}

a { color:#4ea8de; text-decoration:none; }
"""


def page_login(error=""):
    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{STYLE}</style>
    </head>
    <body>
    <div class="box">
    <h2>Login</h2>
    <p style='color:red'>{error}</p>
    <form method='POST' action='/login'>
        <input name='username' placeholder='Usuario'><br>
        <input name='password' type='password' placeholder='Contraseña'><br>
        <button>Entrar</button>
    </form>
    <a href='/register'>Registrarse</a>
    </div>
    </body>
    </html>
    """


def page_register(msg=""):
    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{STYLE}</style>
    </head>
    <body>
    <div class="box">
    <h2>Registro</h2>
    <p>{msg}</p>
    <form method='POST' action='/register'>
        <input name='username'><br>
        <input name='password' type='password'><br>
        <select name='role'>
            <option value='operator'>Operador</option>
            <option value='sensor'>Sensor</option>
        </select><br>
        <button>Registrar</button>
    </form>
    <a href='/'>Volver</a>
    </div>
    </body>
    </html>
    """


def page_dashboard(user, role):
    sensores = read_sensor_data()

    hay_alerta = "color:red" in sensores

    alerta_html = ""
    script_alerta = ""

    if hay_alerta:
        alerta_html = """
        <div style="background:red; padding:10px; text-align:center; font-weight:bold;">
            ⚠ ALERTA: sensores en estado crítico
        </div>
        """

        script_alerta = """
        <script>
            alert("⚠ Hay sensores en estado crítico");
        </script>
        """

    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{STYLE}</style>
    </head>
    <body>

    {alerta_html}

    <header>
        <h2>IoT Monitor</h2>
        <div>{user} ({role}) | <a href='/logout'>Salir</a></div>
    </header>

    <div id="sensores">
        {sensores}
    </div>

    {script_alerta}

    <script>
        setTimeout(() => location.reload(), 3000);
    </script>

    </body>
    </html>
    """


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(self.path).path
        session = get_session(self.headers.get("Cookie"))

        if path == "/":
            if session:
                self.respond(page_dashboard(
                    session["username"],
                    session["role"]
                ))
            else:
                self.respond(page_login())
            return

        if path == "/register":
            self.respond(page_register())
            return

        if path == "/logout":
            self.send_response(303)
            self.send_header("Location", "/")
            self.send_header("Set-Cookie", "session=; Max-Age=0")
            self.end_headers()
            return

        self.respond("404", 404)


    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        data = parse_qs(body)

        if self.path == "/login":
            user = data.get("username", [""])[0]
            pwd  = data.get("password", [""])[0]

            auth = query_auth_service(user, pwd)

            if auth.get("authenticated"):
                token = secrets.token_hex(16)
                SESSIONS[token] = {
                    "username": user,
                    "role": auth.get("role", "unknown")
                }

                self.send_response(303)
                self.send_header("Location", "/")
                self.send_header("Set-Cookie", f"session={token}")
                self.end_headers()
            else:
                self.respond(page_login("Credenciales incorrectas"))

        elif self.path == "/register":
            user = data.get("username", [""])[0]
            pwd  = data.get("password", [""])[0]
            role = data.get("role", ["operator"])[0]

            res = call_register_service(user, pwd, role)

            if res.get("registered"):
                self.respond(page_register("Registrado correctamente"))
            else:
                self.respond(page_register("Error en registro"))

    def respond(self, html, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


if __name__ == "__main__":
    print(f"[WEB] corriendo en puerto {WEB_PORT}")
    server = HTTPServer(("0.0.0.0", WEB_PORT), Handler)
    server.serve_forever()