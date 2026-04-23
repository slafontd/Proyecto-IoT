PROTOCOLO DE APLICACIÓN

El sistema utiliza un protocolo basado en texto para la comunicación entre sensores y servidor.

Formato del mensaje:
SENSOR <TIPO> <VALOR>

Donde:
- SENSOR: identificador del origen
- TIPO: tipo de dato (TEMP, HUM)
- VALOR: valor numérico del sensor

Ejemplos:
SENSOR TEMP 30
SENSOR HUM 75

El servidor recibe, procesa y almacena el último valor recibido.
