/*
 * auth_client.h
 * ─────────────
 * Módulo C que permite al servidor principal consultar el servicio
 * de autenticación externo vía HTTP/TCP.
 *
 * El servidor principal NO almacena usuarios. Toda validación
 * se delega a auth_service.py (puerto 9000).
 */

#ifndef AUTH_CLIENT_H
#define AUTH_CLIENT_H

/* Resultado de autenticación devuelto por el servicio externo */
typedef struct {
    int  authenticated;   /* 1 = válido, 0 = inválido               */
    char role[32];        /* "admin", "operator", "sensor", ""       */
    char username[64];    /* nombre de usuario confirmado            */
    char error[128];      /* mensaje de error si authenticated == 0  */
} AuthResult;

/*
 * auth_query()
 * ────────────
 * Consulta el servicio externo de identidad.
 *
 * Parámetros:
 *   auth_host  – hostname o IP del servicio de auth (ej: "auth.iot.local")
 *   auth_port  – puerto del servicio (ej: 9000)
 *   username   – nombre de usuario a validar
 *   password   – contraseña en texto plano (el servicio la hashea)
 *
 * Retorna:
 *   AuthResult con los campos rellenos según la respuesta del servicio.
 *   Si hay error de red, authenticated = 0 y error describe el fallo.
 */
AuthResult auth_query(const char *auth_host, int auth_port,
                      const char *username, const char *password);

/*
 * auth_query_role()
 * ─────────────────
 * Igual que auth_query(), pero además verifica que el usuario tenga
 * el rol requerido (consulta /validate_role en el servicio).
 *
 * Parámetros adicionales:
 *   required_role – rol que debe tener el usuario ("operator", "sensor", etc.)
 *
 * Retorna:
 *   AuthResult; el campo authenticated indica si tiene el rol requerido.
 */
AuthResult auth_query_role(const char *auth_host, int auth_port,
                           const char *username, const char *password,
                           const char *required_role);

#endif /* AUTH_CLIENT_H */