import socket
import time
import random

HOST = "18.222.158.163"
PORT = 8080

sensor_id = f"sensor{random.randint(1,100)}"
tipos = ["TEMP", "HUM", "PRESS", "VIB", "ENERGY"]
tipo = random.choice(tipos)

while True:
    s = socket.socket()
    s.connect((HOST, PORT))

    valor = random.randint(0, 100)
    mensaje = f"DATA {sensor_id} {valor}"

    s.send(mensaje.encode())
    print("Enviado:", mensaje)

    s.close()

    time.sleep(2)