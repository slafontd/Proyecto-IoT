#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>

#pragma comment(lib, "ws2_32.lib")

int main() {
    WSADATA wsa;
    SOCKET server_fd, client_fd;
    struct sockaddr_in address;
    int addrlen = sizeof(address);
    char buffer[1024];

    WSAStartup(MAKEWORD(2,2), &wsa);

    server_fd = socket(AF_INET, SOCK_STREAM, 0);

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(8080);

    bind(server_fd, (struct sockaddr*)&address, sizeof(address));
    listen(server_fd, 5);

    printf("Servidor escuchando en puerto 8080...\n");

    while (1) {
        client_fd = accept(server_fd, (struct sockaddr*)&address, &addrlen);

        memset(buffer, 0, 1024);
        recv(client_fd, buffer, 1024, 0);

        printf("\n==============================\n");
        printf("[SERVIDOR] Mensaje recibido: %s\n", buffer);

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

        closesocket(client_fd);
    }

    closesocket(server_fd);
    WSACleanup();
    return 0;
}