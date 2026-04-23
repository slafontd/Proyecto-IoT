import socket
import time
import random

HOST = "18.222.158.163"  # luego lo cambiamos a dominio
PORT = 8080

sensor_id = f"sensor{random.randint(1,100)}"

tipos = ["TEMP", "HUM", "PRESS", "VIB", "ENERGY"]
tipo = random.choice(tipos)

s = socket.socket()
s.connect((HOST, PORT))

# REGISTRO
mensaje = f"REGISTER {sensor_id} {tipo}"
s.send(mensaje.encode())
print("Enviado:", mensaje)

time.sleep(1)

while True:
    valor = random.randint(0, 100)
    mensaje = f"DATA {sensor_id} {valor}"
    s.send(mensaje.encode())
    print("Enviado:", mensaje)

    time.sleep(2)