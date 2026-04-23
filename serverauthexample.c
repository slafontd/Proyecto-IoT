/*
 * server_auth_example.c
 * ─────────────────────
 * Fragmento de ejemplo que muestra cómo integrar auth_client.h
 * dentro del servidor principal (server.c).
 *
 * Cuando el servidor recibe el mensaje:
 *   AUTH <username> <password>
 *
 * Llama a auth_query() para validar contra el servicio externo
 * y responde al cliente con OK <role> o ERROR.
 *
 * ── Integración en server.c ─────────────────────────────────
 *
 * 1. Al inicio del archivo agregar:
 *      #include "auth_client.h"
 *
 * 2. Definir (o recibir por argumento) el host/puerto del auth service:
 *      #define AUTH_SERVICE_HOST  "auth.iot.local"
 *      #define AUTH_SERVICE_PORT  9000
 *
 * 3. Dentro del hilo/función que atiende cada cliente, llamar a:
 *      handle_auth_command(client_fd, buffer);
 *
 * ── Compilación ──────────────────────────────────────────────
 *   gcc server.c auth_client.c -o server -lpthread
 */

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "auth_client.h"

#define AUTH_SERVICE_HOST  "auth.iot.local"
#define AUTH_SERVICE_PORT  9000

/*
 * handle_auth_command()
 * ─────────────────────
 * Parsea el mensaje "AUTH <username> <password>" recibido del cliente,
 * consulta el servicio externo de autenticación y responde al socket.
 *
 * Respuestas al cliente:
 *   "AUTH OK <role>\n"       — autenticación exitosa
 *   "AUTH ERROR <motivo>\n"  — credenciales inválidas o error de red
 */
void handle_auth_command(int client_fd, const char *message)
{
    char username[64]  = {0};
    char password[128] = {0};
    char response[256] = {0};

    /* Parsear "AUTH <username> <password>" */
    if (sscanf(message, "AUTH %63s %127s", username, password) != 2) {
        snprintf(response, sizeof(response),
                 "AUTH ERROR Formato invalido. Uso: AUTH <usuario> <password>\n");
        send(client_fd, response, strlen(response), 0);
        return;
    }

    printf("[SERVER] Autenticando usuario '%s' via servicio externo...\n", username);

    /* ── Consultar servicio externo de autenticación ── */
    AuthResult result = auth_query(AUTH_SERVICE_HOST, AUTH_SERVICE_PORT,
                                   username, password);

    if (result.authenticated) {
        printf("[SERVER] Auth exitosa: usuario='%s' rol='%s'\n",
               result.username, result.role);
        snprintf(response, sizeof(response),
                 "AUTH OK %s\n", result.role);
    } else {
        printf("[SERVER] Auth fallida: usuario='%s' error='%s'\n",
               username, result.error);

        if (strlen(result.error) > 0) {
            snprintf(response, sizeof(response),
                     "AUTH ERROR %s\n", result.error);
        } else {
            snprintf(response, sizeof(response),
                     "AUTH ERROR Credenciales invalidas\n");
        }
    }

    send(client_fd, response, strlen(response), 0);
}


/*
 * Ejemplo de uso dentro del bucle principal del servidor:
 *
 *   void *handle_client(void *arg) {
 *       int  client_fd = *(int *)arg;
 *       char buffer[1024];
 *       memset(buffer, 0, sizeof(buffer));
 *       recv(client_fd, buffer, sizeof(buffer) - 1, 0);
 *
 *       if (strncmp(buffer, "AUTH ", 5) == 0) {
 *           handle_auth_command(client_fd, buffer);
 *       } else if (strncmp(buffer, "SENSOR ", 7) == 0) {
 *           handle_sensor_data(client_fd, buffer);
 *       } else {
 *           // ...
 *       }
 *
 *       close(client_fd);
 *       return NULL;
 *   }
 */