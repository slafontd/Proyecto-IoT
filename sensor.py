import socket
import time
import random

tipos = ["TEMP", "HUM"]

while True:
    s = socket.socket()
    s.connect(("18.222.158.163", 8080))
    
    tipo = random.choice(tipos)
    
    if tipo == "TEMP":
        valor = random.randint(20, 40)
    else:
        valor = random.randint(40, 90)
    
    mensaje = f"SENSOR {tipo} {valor}"
    
    s.send(mensaje.encode())
    s.close()
    
    print("Enviado:", mensaje)
    
    time.sleep(2)