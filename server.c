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

    read(client_fd, buffer, BUFFER_SIZE);

    printf("\n==============================\n");
    printf("[SERVIDOR] Mensaje recibido: %s\n", buffer);

    // guardar en log
    FILE *log = fopen(logfile, "a");
    if (log != NULL) {
        fprintf(log, "%s\n", buffer);
        fclose(log);
    }

    // TEMP
    if (strstr(buffer, "TEMP")) {
        int temp;
        sscanf(buffer, "SENSOR TEMP %d", &temp);
        if (temp > 35) {
            printf("[ALERTA] Temperatura alta!\n");
        }
    }

    // HUM
    if (strstr(buffer, "HUM")) {
        int hum;
        sscanf(buffer, "SENSOR HUM %d", &hum);
        if (hum > 80) {
            printf("[ALERTA] Humedad alta!\n");
        }
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