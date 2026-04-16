# Game Server Manager — Gravity AI Bridge V10.0 ⚔️

El módulo **Game Server Manager** (`core/game_server_manager.py`) permite que Gravity AI controle totalmente servidores de juegos ejecutados en la misma máquina física.

Soporta nativamente **World of Warcraft Vanilla** utilizando motores modernos basados en MaNGOS (como AzerothCore, CMaNGOS, o vMaNGOS). El sistema orquesta el inicio de bases de datos, demonios de autenticación (`realmd`), demonios de mundo (`worldserver`/`mangosd`), y ofrece un watchdog de reinicio automático.

---

## 1. Configuración (`config.yaml`)

Todo está basado en el archivo principal `config.yaml`. Abre el archivo y localiza el bloque `game_servers`.

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
    log_file: "F:\\Project_Anarchy_Core\\MaNGOS\\logs\\mangosd.log"
    auto_restart: true
    restart_delay_seconds: 15
    db_host: "127.0.0.1"
    db_port: 3306
    db_name: "characters"
    db_user: "mangos"
    db_pass: ""
```

**Explicación de los campos:**
- `server_dir`: Ruta donde se encuentran los ejecutables de tu servidor.
- `worldserver_exe` / `realmd_exe`: Nombres de los procesos centrales.
- `mysql_start_bat`: Script Batch que inicia una base de datos portable (MySQL/MariaDB) si la tienes. Si el MySQL es nativo de la PC, puedes dejar esto vacío.
- `auto_restart`: Activa el modo "Watchdog". Si Gravity detecta que el proceso cayó, lo reiniciará automáticamente.
- Bloque `db_*`: Credenciales de acceso a la base de datos `characters` para leer en tiempo real la lista de jugadores conectados.

---

## 2. Dependencias Necesarias

Si deseas habilitar la consulta en vivo de los jugadores que están online dentro del juego, debes instalar el cliente MySQL para Python:

```cmd
pip install pymysql
```

Sin esta librería, el panel simplemente te indicará que no está disponible pero el encendido y apagado de servidor seguirán funcionando con normalidad.

---

## 3. Comandos de Consola (SOAP)

Para inyectar comandos de Game Master directamente desde el Dashboard Web (ej. dar experiencia, anunciar mensajes en el chat general), el servidor WoW debe tener habilitado el puerto SOAP.

Ve al archivo `mangosd.conf` en el directorio de tu servidor y asegúrate de tener:

```ini
SOAP.Enabled = 1
SOAP.IP = "127.0.0.1"
SOAP.Port = 7878
```

Gravity v10.0 enviará comandos a través de la interfaz nativa del sistema, pero el soporte SOAP permite mayor robustez en integraciones HTTP.

---

## 4. Uso del Dashboard

Ingresando en `http://localhost:7860/` y navegando a la pestaña **Game Servers**:

1. **Estado**: Un sistema de colores indicará (Verde, Naranja, Rojo) si ambos módulos (mundo y realm) están activos, si hay un fallo parcial, o si está offline.
2. **Botones de Control**: `▶ Iniciar`, `⏹ Detener`, `↺ Reiniciar`.
3. **Log de MaNGOS**: Un panel que consulta a demanda las últimas 150 líneas de log del motor en tiempo real.
4. **Jugadores Online**: Una tabla que despliega nombre, nivel, raza, clase y zona del personaje, leyendo directamente la tabla `characters` a través de TCP/3306.

---

## 5. Extensibilidad

Este módulo fue diseñado abstractamente para tolerar otros servidores de juego en el futuro (ej. Minecraft `server.jar`, Terraria, CS2).
Las bases están sentadas bajo el mismo mecanismo: orquestar subprocesos (`subprocess.Popen`), interceptar logs usando *tailing*, y proporcionar monitorización ininterrumpida.
