import socket
import time
import random
import os

HOST = os.getenv("SERVER_HOST", "localhost")
PORT = int(os.getenv("SERVER_PORT", 8080))

tipos = ["TEMP", "HUM", "PRESS", "VIB", "ENERGY"]

while True:
    sensor_id = f"sensor{random.randint(1,5)}"
    tipo = random.choice(tipos)
    valor = random.randint(0,100)

    try:
        s = socket.socket()
        s.connect((HOST, PORT))

        msg = f"DATA {sensor_id} {tipo} {valor}"
        s.send(msg.encode())

        print(msg)

        s.close()

    except Exception as e:
        print("[ERROR]", e)

    time.sleep(2)