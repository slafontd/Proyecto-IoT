from flask import Flask
import socket

app = Flask(__name__)

HOST = "127.0.0.1"
PORT = 8080

@app.route("/")
def index():
    s = socket.socket()
    s.connect((HOST, PORT))
    s.send(b"GET_STATUS")
    data = s.recv(4096).decode()
    s.close()

    html = "<h1>Sistema IoT</h1>"

    for line in data.split("\n"):
        if line:
            id, tipo, valor = line.split()
            alerta = "🔴" if int(valor) > 80 else "🟢"
            html += f"<p>{id} ({tipo}) → {valor} {alerta}</p>"

    return html

app.run(host="0.0.0.0", port=8000)