import socket
import time
import random
import sys

HOST = "127.0.0.1"   # debes configurarlo en hosts
PORT = 8080

tipos = ["TEMP", "HUM", "PRESS", "VIB", "ENERGY"]

# 🔹 validar argumento
if len(sys.argv) < 2:
    print("Uso: python sensor.py <sensor_id>")
    exit()

sensor_id = sys.argv[1]

# 🔹 cada sensor tiene un tipo fijo
tipo = tipos[hash(sensor_id) % len(tipos)]

print(f"[INFO] Sensor iniciado: {sensor_id} ({tipo})")

while True:
    try:
        valor = random.randint(0, 100)

        s = socket.socket()
        s.connect((HOST, PORT))

        msg = f"DATA {sensor_id} {tipo} {valor}"
        s.send(msg.encode())

        print(f"[SEND] {msg}")

        s.close()

    except Exception as e:
        print("[ERROR]", e)

    time.sleep(2)