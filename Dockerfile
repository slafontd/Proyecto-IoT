FROM ubuntu:22.04

RUN apt update && apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    gcc \
    build-essential

WORKDIR /app

COPY . .

RUN pip3 install flask

RUN gcc server.c -o server -lpthread

EXPOSE 8000

CMD ./server 8080 log.txt & \
    python3 auth_service.py & \
    python3 web.py
