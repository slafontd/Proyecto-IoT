from flask import Flask, jsonify
import socket

app = Flask(__name__)

HOST = "127.0.0.1"   # porque web y server están en AWS
PORT = 8080


# 🔹 función para pedir datos al server C
def obtener_datos():
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.send(b"GET_STATUS")
        data = s.recv(4096).decode()
        s.close()

        sensores = []

        for line in data.split("\n"):
            if line:
                parts = line.split()
                if len(parts) == 3:
                    sensores.append({
                        "id": parts[0],
                        "tipo": parts[1],
                        "valor": int(parts[2])
                    })

        return sensores

    except:
        return []


# 🔹 endpoint API (JSON)
@app.route("/data")
def data():
    return jsonify(obtener_datos())


# 🔹 interfaz web (tiempo real con JS)
@app.route("/")
def index():
    return """
    <html>
    <head>
        <title>Sistema IoT</title>
        <style>
            body { font-family: Arial; background: #111; color: white; }
            h1 { text-align: center; }
            .sensor {
                padding: 10px;
                margin: 10px;
                border-radius: 8px;
                background: #222;
            }
        </style>
    </head>
    <body>
        <h1>📡 Sistema IoT en Tiempo Real</h1>
        <div id="sensores"></div>

        <script>
        async function cargarDatos() {
            try {
                const res = await fetch('/data');
                const data = await res.json();

                let html = "";

                if (data.length === 0) {
                    html = "<p>No hay sensores activos</p>";
                }

                data.forEach(s => {
                    let color = s.valor > 80 ? "red" : "lime";

                    html += `
                    <div class="sensor">
                        <b>${s.id}</b> (${s.tipo})<br>
                        Valor: ${s.valor} 
                        <span style="color:${color}; font-size:20px">●</span>
                    </div>
                    `;
                });

                document.getElementById("sensores").innerHTML = html;

            } catch (err) {
                document.getElementById("sensores").innerHTML =
                    "<p>Error conectando con el servidor</p>";
            }
        }

        // actualización automática (TIEMPO REAL)
        setInterval(cargarDatos, 2000);

        // carga inicial
        cargarDatos();
        </script>
    </body>
    </html>
    """


# 🔹 correr servidor web
app.run(host="0.0.0.0", port=8000)