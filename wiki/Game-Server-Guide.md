# Game Server Manager — Gravity AI Bridge V10.0 ⚔️

El módulo **Game Server Manager** (`core/game_server_manager.py`) permite que Gravity AI controle totalmente servidores de juegos ejecutados en la misma máquina física, ofreciendo una capa de gestión profesional similar a un orquestador de contenedores pero nativo para Windows.

## ⚙️ 1. Configuración (`config.yaml`)

Toda la orquestación se basa en el bloque `game_servers` de tu archivo de configuración principal.

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

### Explicación de Campos Críticos:
- **`server_dir`**: Ruta absoluta a la carpeta raíz de tu core.
- **`worldserver_exe` / `realmd_exe`**: Nombres de los demonios de juego y de autenticación.
- **`mysql_start_bat`**: Script que arranca el motor de base de datos si es portable.
- **`auto_restart`**: Si se establece en `true`, el bridge reanimará los procesos si se cierran inesperadamente.
- **`db_*`**: Credenciales de la base de datos `characters` para el monitoreo de jugadores online.

---

## 📦 2. Dependencias Necesarias

Para habilitar la consulta en vivo de los jugadores que están online, debes instalar el cliente MySQL para Python:

```cmd
pip install pymysql
```
*Si no se instala esta librería, las funciones de encendido/apagado seguirán operativas, pero la tabla de jugadores online se mostrará desactivada.*

---

## 📡 3. Comandos de Consola (SOAP)

Para enviar comandos desde el Dashboard (ej: anunciar mensajes globales), habilita el protocolo SOAP en tu `mangosd.conf`:

```ini
SOAP.Enabled = 1
SOAP.IP = "127.0.0.1"
SOAP.Port = 7878
```

---

## 🖥️ 4. Uso del Dashboard Web

Navegando a la pestaña **Game Servers** en `http://localhost:7860`:

### Indicadores de Estado:
- **🟢 ONLINE:** Ambos procesos (mundo y realm) están activos.
- **🟠 PARCIAL:** Solo uno de los dos procesos está corriendo.
- **🔴 OFFLINE:** El servidor está totalmente detenido.

### Funciones Disponibles:
1. **Controles de Proceso:** Iniciar, Detener y Reiniciar con feedback instantáneo mediante avisos visuales (Toasts).
2. **Log de MaNGOS:** Consulta en tiempo real las últimas 150 líneas de log del worldserver.
3. **Jugadores Online:** Tabla dinámica que lee directamente de la base de datos MySQL (Nombre, Nivel, Raza, Clase, Zona).

---
## 🚀 Extensibilidad
Este módulo es agnóstico al motor. Aunque está optimizado para MaNGOS, puede adaptarse a cualquier proceso de juego (Minecraft, Terraria, CS2) configurando los ejecutables y archivos de log correspondientes en `config.yaml`.

---
*Manual Técnico del Game Server Manager — V10.0.*
