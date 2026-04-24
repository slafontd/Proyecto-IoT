Sistema IoT Distribuido
Descripción

Este proyecto implementa un sistema IoT distribuido compuesto por:

Sensores simulados (Python)
Servidor central (C, sockets Berkeley)
Interfaz web (Python)
Servicio de autenticación externo (Flask)
Despliegue en AWS EC2

El sistema permite registrar sensores, enviar datos en tiempo real y visualizarlos desde una interfaz web protegida por autenticación.

Arquitectura
Sensores → Servidor (C)
Web → Servidor (consulta estado)
Web → Auth Service (login)
Componentes
1. Servidor (C)
Implementado con Berkeley Sockets
Manejo concurrente con pthreads
Soporta múltiples clientes simultáneos
Procesa protocolo personalizado
2. Sensores (Python)
Simulan múltiples tipos de sensores
Envían datos periódicamente
No contienen IPs hardcodeadas
3. Web (Python)
Interfaz con login
Consulta datos en tiempo real
Consume servicio de autenticación externo
4. Auth Service (Flask)
Registro de usuarios
Login
Validación externa
Variables de entorno

El sistema utiliza variables de entorno para evitar IPs hardcodeadas:

SERVER_HOST=localhost
AUTH_HOST=localhost
SERVER_PORT=8080
WEB_PORT=8000
Ejecución local
Servidor
gcc server.c -o server -lpthread
./server 8080 log.txt
Auth
python3 -m venv venv
source venv/bin/activate
pip install flask
python auth_service.py
Web
python web.py
Sensor
python sensor.py
Despliegue en AWS
Crear instancia EC2
Abrir puerto 8000 en Security Group
Clonar repositorio:
git clone <repo>
cd Proyecto-IoT
Ejecutar componentes como en local

Acceso:

http://IP_PUBLICA:8000
Requisitos cumplidos
No uso de IPs hardcodeadas
Concurrencia en servidor
Servicio de autenticación externo
Protocolo definido y documentado
Múltiples sensores simulados
Visualización en tiempo real
Despliegue en AWS
Autor

Proyecto académico de sistema IoT distribuido. Desarrollado por Samuel Llano y Santiago Lafont

Protocolo de Comunicación IoT
Descripción general

El sistema utiliza un protocolo de texto plano sobre TCP.
Cada mensaje es una cadena ASCII terminada en salto de línea.

Tipos de clientes
Sensores
Cliente Web
(Opcional) Cliente operador
Comandos del protocolo
1. REGISTER
Formato:
REGISTER <sensor_id> <tipo>
Ejemplo:
REGISTER sensor1 TEMP
Descripción:

Registra un sensor en el sistema.

Respuesta:
OK REGISTER
2. DATA
Formato:
DATA <sensor_id> <tipo> <valor>
Ejemplo:
DATA sensor1 TEMP 45
Descripción:

Envía una medición al servidor.

Comportamiento del servidor:
Actualiza el valor del sensor
Si el sensor no existe → lo crea
Respuestas:

Caso normal:

OK

Caso alerta (valor > 80):

ALERT
3. GET_STATUS
Formato:
GET_STATUS
Descripción:

Solicita el estado actual de todos los sensores.

Respuesta:

Lista de sensores:

sensor1 TEMP 45
sensor2 HUM 30
sensor3 PRESS 90
Manejo de errores

Si el formato es inválido:

ERROR
Conexión
Protocolo: TCP
Puerto: configurable (default 8080)
Codificación: UTF-8
Flujo típico
Sensor se conecta
Envía DATA
Servidor responde OK o ALERT
Web consulta con GET_STATUS
Servidor responde con todos los sensores
Consideraciones
Comunicación sin estado (stateless)
Cada conexión es independiente
Soporta múltiples clientes concurrentes

Ejecución en Visual Studio Code (WSL)

## Requisito
Este proyecto debe ejecutarse en WSL (Ubuntu), no en Windows directamente.

---

## 1. Abrir en WSL
En VS Code:
- Ctrl + Shift + P
- Escribir: WSL: Reopen Folder in WSL

---

## 2. Abrir terminal
Ctrl + ñ

---

## 3. Configurar Python (solo primera vez)
python3 -m venv venv
source venv/bin/activate
pip install flask

---

## 4. Compilar servidor (C)
gcc server.c -o server -lpthread

---

## 5. Ejecutar sistema (4 terminales)

### Terminal 1 - Servidor
./server 8080 log.txt

### Terminal 2 - Auth
source venv/bin/activate
python auth_service.py

### Terminal 3 - Web
source venv/bin/activate
export SERVER_HOST=127.0.0.1
export AUTH_HOST=127.0.0.1
python web.py

### Terminal 4 - Sensor
source venv/bin/activate
export SERVER_HOST=127.0.0.1
python sensor.py

---

## 6. Abrir en navegador
http://localhost:8000

---

## Notas
- Todo debe ejecutarse en WSL
- No mezclar con Windows

