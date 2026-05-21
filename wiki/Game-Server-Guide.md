# Game Server Manager — Gravity AI Bridge V15.0 PRO ⚔️

El módulo **Game Server Manager** (`core/game_server_manager.py`) proporciona un sistema de orquestación a nivel de sistema operativo para servidores de juegos que se ejecutan en la misma máquina física, operando como un orquestador híbrido de alto rendimiento diseñado específicamente para Windows Server y entornos locales optimizados.

Actualmente está integrado de forma nativa para **World of Warcraft Vanilla (MaNGOS / vMaNGOS)**, pero su arquitectura desacoplada y agnóstica permite extenderlo a cualquier proceso de servidor de videojuegos que requiera gestión de ciclo de vida de procesos, monitoreo de bases de datos y tuberías de logs circulares.

---

## ⚙️ 1. Configuración de Arquitectura (`config.yaml`)

El comportamiento del orquestador se define dentro del bloque `game_servers` en el archivo de configuración global:

```yaml
game_servers:
  wow_vanilla:
    enabled: true
    display_name: "WoW Vanilla (MaNGOS)"
    type: "mangos"
    server_dir: "F:\\Project_Anarchy_Core\\MaNGOS"
    worldserver_exe: "mangosd.exe"
    realmd_exe: "realmd.exe"
    mysql_start_bat: "F:\\Project_Anarchy_Core\\MaNGOS\\Start MySQL.bat"
    mysql_stop_bat: "F:\\Project_Anarchy_Core\\MaNGOS\\Stop MySQL.bat"
    log_file: "F:\\Project_Anarchy_Core\\MaNGOS\\logs\\Server.log"
    auto_restart: true
    restart_delay_seconds: 15
    db_host: "127.0.0.1"
    db_port: 3306
    db_name: "characters"
    db_user: "root"
    db_pass: "root"
    db_name_auth: "realmd"
```

### Variables Críticas de Configuración:
- **`server_dir`**: Directorio raíz absoluto donde residen los binarios del servidor de juegos.
- **`worldserver_exe` / `realmd_exe`**: Nombres de los ejecutables de juego (`world`) y autenticación (`realm`).
- **`mysql_start_bat` / `mysql_stop_bat`**: Rutas opcionales a scripts de procesamiento por lotes (`.bat`) para controlar motores de bases de datos portables en el entorno local.
- **`auto_restart`**: Bandera booleana para activar el Watchdog de autorecuperación en caso de fallos inesperados.
- **`db_host` / `db_port` / `db_user` / `db_pass`**: Credenciales de acceso de bajo nivel a la base de datos relacional MySQL.
- **`db_name` / `db_name_auth`**: Nombres de los esquemas de bases de datos para personajes (`characters`) y autenticación (`realmd`).

---

## 🛡️ 2. Mecanismos Internos del Motor (V15.0 PRO)

El motor `core/game_server_manager.py` implementa lógicas de resiliencia de clase empresarial:

```
                  ┌──────────────────────────────┐
                  │   Pre-Flight MySQL Check     │
                  └──────────────┬───────────────┘
                                 │ (¿MySQL Responde?)
                                 ▼
                  ┌──────────────────────────────┐
                  │    Start realmd & mangosd    │
                  └──────────────┬───────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌─────────────────┐                             ┌─────────────────┐
│ Memory Buffer   │                             │ Smart Watchdog  │
│ (stdout stream) │                             │ (Crash Monitor) │
└─────────────────┘                             └────────┬────────┘
                                                         │ (Si muere proc)
                                                         ▼
                                                ┌─────────────────┐
                                                │  Limit Check    │
                                                │ (Max 3 / 60s)   │
                                                └────────┬────────┘
                                                         │ (OK)
                                                         ▼
                                                ┌─────────────────┐
                                                │ Auto-Restart    │
                                                └─────────────────┘
```

### A. Pre-Flight MySQL Check
Para evitar bloqueos y fallos de aserción en el worldserver (que típicamente crashea de inmediato si la base de datos no está disponible), el cargador ejecuta una verificación previa. Intenta realizar conexiones TCP socket activas a la base de datos MySQL configurada durante un tiempo límite máximo de **30 segundos**. Si la base de datos no está lista o no responde, el inicio del servidor se aborta limpiamente para proteger la integridad de los datos.

### B. Intelligent Watchdog (Prevención de Loops de Crash)
El watchdog se ejecuta en un hilo secundario dedicado (`GravityWatchdog_<server_id>`). Si el proceso del mundo o de la autenticación muere de manera inesperada, el sistema lo detecta inmediatamente.
Para evitar loops de reinicio infinito en escenarios con archivos corruptos u otros errores críticos de carga, el watchdog implementa protección contra fallos en bucle (**Bug-25 Mitigated**):
- Registra la ventana de tiempo del crash.
- Si detecta **más de 3 caídas dentro de un periodo de 60 segundos**, detiene la autorecuperación automática.
- Marca el servidor con el estado crítico `error_loop` y requiere intervención manual del administrador del sistema.

### C. Captura de Logs en Tiempo Real (Memory Buffers)
El sistema captura el flujo de salida estándar (`stdout`) y errores estándar (`stderr`) de los ejecutables de MaNGOS mediante el módulo `core/log_buffer.py`.
- Mantiene un **buffer circular de lectura rápida en memoria** limitado a las últimas **500 líneas**.
- Esto elimina las costosas operaciones de entrada/salida (I/O) en disco cuando el Dashboard web solicita ver el log en tiempo real.
- **Transparencia Activa**: Si el buffer circular en memoria no está listo, el motor realiza automáticamente una caída de retroceso (fallback) a leer las líneas físicas desde el archivo definido en `log_file`.

### D. Copias de Seguridad Automatizadas (Auto-Backup)
Cada vez que se detiene el servidor de juegos de forma programada mediante la API o el Dashboard:
1. El motor realiza un volcado de base de datos (`mysqldump`) en caliente y de manera asíncrona sobre la base de datos de personajes.
2. Genera un archivo `.sql` timestamped dentro del directorio `_saves/` (ej. `_saves/backup_wow_vanilla_20260521_080000.sql`).
3. Mantiene una rotación estricta en caliente: **conserva únicamente las últimas 5 copias de seguridad** y elimina automáticamente los archivos antiguos para optimizar el espacio en disco.

---

## 📡 3. Especificación Completa de la API REST

Todos los endpoints interactúan a través del servidor del puente en `http://localhost:7860/` y soportan de forma nativa llamadas de origen cruzado (CORS).

### Endpoints de Consulta (GET)

#### 1. Obtener Estado Global
*   **Ruta**: `GET /v1/gameserver/status`
*   **Descripción**: Devuelve un JSON detallado con el estado actual de los procesos, PIDs activos, marcas de tiempo y el estado de la librería MySQL.
*   **Respuesta Exitosa (200 OK)**:
    ```json
    {
      "servers": {
        "wow_vanilla": {
          "status": "running",
          "display_name": "WoW Vanilla (MaNGOS)",
          "started_at": "2026-05-21T08:00:00Z",
          "stopped_at": null,
          "world_pid": 14208,
          "realm_pid": 9812,
          "world_alive": true,
          "realm_alive": true,
          "errors": [],
          "auto_restart": true
        }
      },
      "pymysql_available": true,
      "timestamp": "2026-05-21T08:05:00Z"
    }
    ```

#### 2. Lectura de Logs en Tiempo Real
*   **Ruta**: `GET /v1/gameserver/log?server=wow_vanilla&lines=100`
*   **Parámetros**:
    - `server` (opcional): ID del servidor configurado (default: `wow_vanilla`).
    - `lines` (opcional): Número de líneas finales a extraer (default: `100`).
*   **Descripción**: Lee dinámicamente las últimas N líneas del buffer de memoria circular del subproceso o del archivo de log físico en disco.
*   **Respuesta (200 OK)**:
    ```json
    {
      "server": "wow_vanilla",
      "source": "memory_buffer",
      "log_file": null,
      "lines": [
        "[WORLD] Server Startup Complete. Listening on port 8085",
        "[REALM] Realm Daemon Started. Listening on port 3724"
      ]
    }
    ```

#### 3. Consultar Jugadores en Línea
*   **Ruta**: `GET /v1/gameserver/players?server=wow_vanilla`
*   **Descripción**: Realiza una consulta SQL veloz sobre la tabla `characters` de la base de datos de juego para traer a los jugadores con estado online activo.
*   **Respuesta (200 OK)**:
    ```json
    {
      "server": "wow_vanilla",
      "count": 2,
      "players": [
        {
          "player": "DarckRovert",
          "level": 60,
          "race_id": 1,
          "class_id": 1,
          "zone_id": 12,
          "online": 1
        }
      ]
    }
    ```

#### 4. Servir Portal de Registro Web
*   **Ruta**: `GET /v1/gameserver/registro`
*   **Descripción**: Devuelve un portal HTML5/CSS3 estilizado en tema oscuro y dorado de alta definición ("Forge Account") que permite a los usuarios finales registrar sus cuentas interactuando directamente con el puente.

---

### Endpoints de Control y Acción (POST)

> **Nota**: Todos los endpoints POST esperan una cabecera `Content-Type: application/json` y un cuerpo serializado en formato JSON.

#### 1. Iniciar Servidor
*   **Ruta**: `POST /v1/gameserver/start`
*   **Cuerpo (Body)**:
    ```json
    {
      "server": "wow_vanilla"
    }
    ```
*   **Descripción**: Ejecuta el chequeo MySQL, levanta `realmd` y `mangosd` en consolas independientes, e inicializa el buffer circular y el watchdog.

#### 2. Detener Servidor
*   **Ruta**: `POST /v1/gameserver/stop`
*   **Cuerpo (Body)**:
    ```json
    {
      "server": "wow_vanilla"
    }
    ```
*   **Descripción**: Apaga de manera ordenada los procesos del mundo y autenticación usando interrupción controlada. Si la parada ordenada no responde en 10 segundos, fuerza el cierre mediante `terminate/kill`. Ejecuta un backup SQL asíncrono y apaga la base de datos local si hay un batch de apagado configurado.

#### 3. Reiniciar Servidor
*   **Ruta**: `POST /v1/gameserver/restart`
*   **Cuerpo (Body)**:
    ```json
    {
      "server": "wow_vanilla"
    }
    ```
*   **Descripción**: Levanta un hilo de fondo asíncrono que realiza un ciclo completo de apagado (`stop`), espera 3 segundos de gracia para liberar recursos de red, y realiza un encendido limpio (`start`). Responde inmediatamente con confirmación de tarea encolada.

#### 4. Enviar Comandos GM (Consola SOAP)
*   **Ruta**: `POST /v1/gameserver/command`
*   **Cuerpo (Body)**:
    ```json
    {
      "server": "wow_vanilla",
      "command": ".server info"
    }
    ```
*   **Descripción**: Inyecta comandos administrativos de consola utilizando el protocolo SOAP de MaNGOS (puerto default: `7878`). Si SOAP no está configurado o activo en `mangosd.conf`, retorna una respuesta indicando los pasos para habilitarlo en la configuración.

#### 5. Registrar Cuentas de Jugador (SRP-6a / SHA1)
*   **Ruta**: `POST /v1/gameserver/register`
*   **Cuerpo (Body)**:
    ```json
    {
      "server": "wow_vanilla",
      "username": "NUEVOJUGADOR",
      "password": "MIPASSWORD123"
    }
    ```
*   **Descripción**: Crea un registro en la tabla `account` del esquema de autenticación.
*   **Criptografía Avanzada**:
    - **Modo vMaNGOS (SRP-6a)**: Detecta automáticamente si la tabla de cuentas posee las columnas de verifier `v` y salt `s`. Si existen, calcula mediante potencias modulares con el primo seguro de 1024 bits de SRP-6a (`N`), el generador `g = 7` y una clave de salt criptográficamente segura generada por hardware (`os.urandom(32)`), evitando almacenar cualquier contraseña o hashes SHA1 planos en la base de datos.
    - **Modo MaNGOS Clásico (SHA1)**: Si la tabla no posee SRP-6a, genera y almacena la contraseña hasheada en formato clásico de firma digital `SHA1(USERNAME:PASSWORD)`.

#### 6. Exposición WAN y Firewall Automatizado
*   **Ruta**: `POST /v1/gameserver/expose_wan`
*   **Cuerpo (Body)**:
    ```json
    {
      "server": "wow_vanilla",
      "public_address": "wow.darckrovert.com"
    }
    ```
*   **Descripción**: Configura el sistema operativo y la base de datos para tráfico público en una sola llamada:
    1. Ejecuta llamadas de sistema nativas `netsh advfirewall` (con privilegios de Administrador) para inyectar una regla de firewall entrante entrante que expone los puertos de WoW TCP `8085` (juego) y `3724` (autenticación) al exterior.
    2. Modifica la base de datos de autenticación (`realmd`), reescribiendo la fila `realmlist` con la dirección IP pública o subdominio DDNS indicado para que los clientes del juego puedan enrutarse correctamente al servidor.

---

## 🛠️ 4. Guía de Extensibilidad a otros Juegos

Aunque el módulo incluye soporte explícito de consultas de base de datos para arquitecturas MaNGOS/Trinity, extenderlo a otros servidores como **Minecraft (Spigot/Paper)**, **Terraria** o **Counter-Strike 2** es simple:

1.  **Definir en `config.yaml`**: Añade una clave con el ID de tu servidor (ej: `minecraft_server`).
2.  **Configurar los ejecutables**:
    - Apuntar `worldserver_exe` a tu ejecutable de consola o script de arranque (ej: `run_paper.bat`).
    - Configurar el archivo de log correspondiente en `log_file` (ej: `logs/latest.log`).
    - Apagar el demonio secundario `realmd_exe` dejándolo vacío o nulo.
3.  **Desactivar base de datos WoW**: Pon las variables de base de datos `db_*` en vacío o configura una conexión MySQL correspondiente si el servidor de juegos en cuestión la usa para almacenar información.

El Watchdog, el buffer de logs en memoria en tiempo real, los backups automáticos de archivos físicos y el inicio/parada asíncronos funcionarán de manera inmediata y nativa para tu nuevo servidor de juegos sin cambiar una sola línea de código en el núcleo del sistema.

---
*Documentación Técnica Oficial de Gravity AI Bridge V15.0 PRO.*
