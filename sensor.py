import socket, time, random

HOST = "18.222.158.163"
PORT = 8080

sensor_id = f"sensor{random.randint(1,100)}"
tipo = random.choice(["TEMP","HUM","PRESS","VIB","ENERGY"])

while True:
    s = socket.socket()
    s.connect((HOST, PORT))

    msg = f"DATA {sensor_id} {tipo} {random.randint(0,100)}"
    s.send(msg.encode())

    print(msg)
    s.close()

    time.sleep(2)