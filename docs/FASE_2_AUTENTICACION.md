# Fase 2: autenticación y autorización

## Objetivo

Permitir consultas únicamente a usuarios registrados y con claves autorizadas.

## Conceptos

- **Autenticación:** comprobar quién es el usuario.
- **Autorización:** decidir qué puede consultar.
- **Hash:** transformación unidireccional para almacenar contraseñas de forma segura.

Las contraseñas nunca deben guardarse en texto plano.

## Roles propuestos

- administrador;
- reclutador;
- cliente;
- estudiante;
- colega;
- usuario general autorizado.

## Requisitos

1. Registro administrado.
2. Contraseñas con Argon2 o bcrypt.
3. Base de usuarios.
4. Bloqueo temporal tras varios intentos.
5. Auditoría.
6. Matriz de permisos.
7. Expiración de sesión.
8. Revocación de usuarios.
9. Pruebas de autorización.

## Matriz inicial

| Rol | Perfil | Certificaciones | Proyectos | Datos sensibles |
|---|---:|---:|---:|---:|
| Administrador | Sí | Sí | Sí | No por defecto |
| Reclutador | Sí | Sí | Sí | No |
| Cliente | Sí | Parcial | Sí | No |
| Estudiante | Sí | Parcial | Parcial | No |
| General | Sí | Parcial | Parcial | No |

## Actividad
Diseñe una base SQLite con tablas `users`, `roles`, `permissions` y `audit_events`. Implemente autenticación por consola antes de migrar a web.

Implementación incluida en este repositorio:

- Módulo: `src/auth.py` — administra la base SQLite y operaciones de usuarios.
- Hash de contraseñas: usa `argon2-cffi` (Argon2) para almacenar contraseñas de forma segura.
- Comportamiento: bloqueo temporal tras varios intentos fallidos, auditoría de eventos y roles iniciales.

Comandos sugeridos para inicializar la base (ejecutar desde el proyecto):

```powershell
python -c "from src.auth import AuthDB; AuthDB('storage/auth/auth.db').init_db()"
```

Para crear un usuario administrador (ejemplo):

```powershell
python -c "from src.auth import AuthDB; AuthDB('storage/auth/auth.db').create_user('admin','securepassword','administrador')"
```

El `src/cli.py` realiza una verificación simple al entrar en `chat` cuando la DB existe: solicita usuario y contraseña por consola.
