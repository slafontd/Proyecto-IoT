#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>

#define BUFFER_SIZE 1024
#define MAX_SENSORS 100

char *logfile;

typedef struct {
    char id[50];
    char tipo[50];
    int valor;
} Sensor;

Sensor sensores[MAX_SENSORS];
int sensor_count = 0;

pthread_mutex_t lock;

// buscar sensor
int find_sensor(char *id) {
    for (int i = 0; i < sensor_count; i++) {
        if (strcmp(sensores[i].id, id) == 0)
            return i;
    }
    return -1;
}

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

    printf("[MSG] %s\n", buffer);

    // ==========================
    // REGISTER
    // ==========================
    if (strncmp(buffer, "REGISTER", 8) == 0) {
        char id[50], tipo[50];
        sscanf(buffer, "REGISTER %s %s", id, tipo);

        pthread_mutex_lock(&lock);

        int idx = find_sensor(id);
        if (idx == -1 && sensor_count < MAX_SENSORS) {
            strcpy(sensores[sensor_count].id, id);
            strcpy(sensores[sensor_count].tipo, tipo);
            sensores[sensor_count].valor = 0;
            sensor_count++;
        }

        pthread_mutex_unlock(&lock);

        write(client_fd, "OK REGISTER\n", 12);
    }

    // ==========================
    // DATA
    // ==========================
    else if (strncmp(buffer, "DATA", 4) == 0) {
        char id[50], tipo[50];
        int valor;

        sscanf(buffer, "DATA %s %s %d", id, tipo, &valor);

        pthread_mutex_lock(&lock);

        int idx = find_sensor(id);
        if (idx == -1 && sensor_count < MAX_SENSORS) {
            strcpy(sensores[sensor_count].id, id);
            strcpy(sensores[sensor_count].tipo, tipo);
            sensores[sensor_count].valor = valor;
            sensor_count++;
        } else {
            sensores[idx].valor = valor;
        }

        pthread_mutex_unlock(&lock);

        printf("[DATA] %s %s %d\n", id, tipo, valor);

        if (valor > 80) {
            write(client_fd, "ALERT\n", 6);
        } else {
            write(client_fd, "OK\n", 3);
        }
    }

    // ==========================
    // GET_STATUS
    // ==========================
    else if (strncmp(buffer, "GET_STATUS", 10) == 0) {

        char response[BUFFER_SIZE * 10];
        strcpy(response, "");

        pthread_mutex_lock(&lock);

        for (int i = 0; i < sensor_count; i++) {
            char line[256];
            snprintf(line, sizeof(line), "%s %s %d\n",
                sensores[i].id,
                sensores[i].tipo,
                sensores[i].valor
            );
            strcat(response, line);
        }

        pthread_mutex_unlock(&lock);

        write(client_fd, response, strlen(response));
    }

    close(client_fd);
    return NULL;
}

int main(int argc, char *argv[]) {

    if (argc < 3) {
        printf("Uso: %s <puerto> <log>\n", argv[0]);
        return 1;
    }

    int port = atoi(argv[1]);
    logfile = argv[2];

    pthread_mutex_init(&lock, NULL);

    int server_fd;
    struct sockaddr_in address;
    int addrlen = sizeof(address);

    server_fd = socket(AF_INET, SOCK_STREAM, 0);

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port);

    bind(server_fd, (struct sockaddr*)&address, sizeof(address));
    listen(server_fd, 10);

    printf("Servidor en puerto %d\n", port);

    while (1) {
        int *client_fd = malloc(sizeof(int));
        *client_fd = accept(server_fd,
            (struct sockaddr*)&address,
            (socklen_t*)&addrlen);

        pthread_t thread;
        pthread_create(&thread, NULL, handle_client, client_fd);
        pthread_detach(thread);
    }

    return 0;
}