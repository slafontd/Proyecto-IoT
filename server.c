#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>

#define BUFFER_SIZE 1024

char *logfile;

// función para manejar cada cliente
void *handle_client(void *arg) {
    int client_fd = *(int *)arg;
    free(arg);

    char buffer[BUFFER_SIZE];
    memset(buffer, 0, BUFFER_SIZE);

    int bytes = read(client_fd, buffer, BUFFER_SIZE);
    if (bytes <= 0) {
        close(client_fd);
        return NULL;
    }

    printf("\n==============================\n");
    printf("[SERVIDOR] Mensaje recibido: %s\n", buffer);

    // guardar en log
    FILE *log = fopen(logfile, "a");
    if (log != NULL) {
        fprintf(log, "%s\n", buffer);
        fclose(log);
    }

    // ==========================
    // PROTOCOLO
    // ==========================

    // REGISTER
    if (strncmp(buffer, "REGISTER", 8) == 0) {
        char id[50], tipo[50];
        sscanf(buffer, "REGISTER %s %s", id, tipo);

        printf("[REGISTER] Sensor %s tipo %s registrado\n", id, tipo);

        char response[] = "OK REGISTER\n";
        write(client_fd, response, strlen(response));
    }

    // DATA
    else if (strncmp(buffer, "DATA", 4) == 0) {
        char id[50];
        int valor;

        sscanf(buffer, "DATA %s %d", id, &valor);

        printf("[DATA] %s → %d\n", id, valor);

        // ALERTA automática
        if (valor > 80) {
            printf("[ALERTA] %s valor crítico: %d\n", id, valor);

            char alert_msg[BUFFER_SIZE];
            sprintf(alert_msg, "ALERT %s %d\n", id, valor);
            write(client_fd, alert_msg, strlen(alert_msg));
        } else {
            char response[] = "OK DATA\n";
            write(client_fd, response, strlen(response));
        }
    }

    // ALERT (manual)
    else if (strncmp(buffer, "ALERT", 5) == 0) {
        char id[50];
        int valor;

        sscanf(buffer, "ALERT %s %d", id, &valor);

        printf("[ALERT] Sensor %s reporta %d\n", id, valor);

        char response[] = "OK ALERT\n";
        write(client_fd, response, strlen(response));
    }

    // GET_STATUS
    else if (strncmp(buffer, "GET_STATUS", 10) == 0) {
        char response[] = "SYSTEM OK\n";
        write(client_fd, response, strlen(response));
    }

    else {
        char response[] = "ERROR UNKNOWN COMMAND\n";
        write(client_fd, response, strlen(response));
    }

    close(client_fd);
    return NULL;
}

int main(int argc, char *argv[]) {

    if (argc < 3) {
        printf("Uso: %s <puerto> <archivo_log>\n", argv[0]);
        return 1;
    }

    int port = atoi(argv[1]);
    logfile = argv[2];

    int server_fd;
    struct sockaddr_in address;
    int addrlen = sizeof(address);

    server_fd = socket(AF_INET, SOCK_STREAM, 0);

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port);

    bind(server_fd, (struct sockaddr*)&address, sizeof(address));
    listen(server_fd, 10);

    printf("Servidor escuchando en puerto %d...\n", port);

    while (1) {
        int *client_fd = malloc(sizeof(int));
        *client_fd = accept(server_fd, (struct sockaddr*)&address, (socklen_t*)&addrlen);

        pthread_t thread;
        pthread_create(&thread, NULL, handle_client, client_fd);
        pthread_detach(thread);
    }

    close(server_fd);
    return 0;
}