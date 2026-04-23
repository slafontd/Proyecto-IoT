import socket, time, random

HOST = "18.222.158.163"
PORT = 8080

tipos = ["TEMP","HUM","PRESS","VIB","ENERGY"]

while True:
    sensor_id = f"sensor{random.randint(1,10)}"
    tipo = random.choice(tipos)
    valor = random.randint(0,100)

    s = socket.socket()
    s.connect((HOST, PORT))

    msg = f"DATA {sensor_id} {tipo} {valor}"
    s.send(msg.encode())

    print(msg)

    s.close()
    time.sleep(2)