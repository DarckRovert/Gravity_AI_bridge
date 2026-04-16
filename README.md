# Gravity AI Bridge V10.0 🌐

[![Versión](https://img.shields.io/badge/Versión-10.0-4f46e5.svg)](CHANGELOG.md)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-22c55e.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![DarckRovert](https://img.shields.io/badge/Desarrollado_por-DarckRovert-7c3aed.svg)](https://twitch.tv/darckrovert)
[![GitHub](https://img.shields.io/badge/GitHub-DarckRovert-181717.svg)](https://github.com/DarckRovert)

> **El ecosistema de IA local más avanzado**, con arquitectura Omni-Tier, enrutamiento dinámico, Dashboard Web con 9 paneles, generación de imágenes CPU, Security Monitor, cola de trabajos SQLite, pipeline de deploy automatizado y gestión nativa de servidores de juegos (WoW Vanilla MaNGOS).

---

## ✨ Características Principales

| Categoría | Funcionalidad |
|-----------|--------------|
| 🔌 **Local** | Ollama · LM Studio · vLLM · KoboldCPP · Jan AI · Lemonade |
| ☁️ **Cloud** | OpenAI · Anthropic · Google Gemini · Groq · Cohere |
| 🧠 **Enrutamiento** | Dinámico por latencia TTFT + especialización de tareas |
| 🛡️ **Seguridad** | API Keys cifradas DPAPI · Security Monitor · Rate Limiting · Audit Log inmutable |
| 📡 **Observabilidad** | Dashboard SPA V10.0 (9 paneles) · Prometheus `/metrics` · Streaming SSE |
| 🎨 **Visión** | Fooocus CPU mode · Vision Studio UI · JuggernautXL SDXL |
| 🖼️ **Image Queue** | Cola SQLite persistente · Worker daemon · Sin bloqueo del servidor HTTP |
| 🚀 **Deploy** | npm build → Netlify deploy automatizado · Log en tiempo real |
| ⚔️ **Game Servers** | WoW Vanilla MaNGOS · Auto-restart · Jugadores online · Log en vivo |
| 🔬 **RAG** | Embeddings CPU/ONNX · BM25 + vectorial · PDFs |
| 🤖 **MCP** | Model Context Protocol · Herramientas externas stdio |
| 🔍 **Verificación** | VerificationAgent adversarial antes de cada cambio |
| 💻 **CLI** | 20+ comandos · Sesiones · Branches · Export MD/HTML |
| ⚡ **Cache** | SQLite WAL · Hash-aware reasoning · TTL configurable |
| 🌐 **Web** | FabricaWeb (Next.js + Web3) integrado en el angling |

---

## 🚀 Instalación Rápida

### Requisito previo para generación de imágenes (AMD GPU)
Si usas una GPU AMD (Radeon 780M / RX series), instala el runtime HIP:
```
AMD-Software-PRO-Edition-26.Q1-Win11-For-HIP.exe
```
Disponible en [amd.com/en/support](https://www.amd.com/en/support). Reinicia Windows tras instalar.

### Opción A — Instalador TUI interactivo (recomendado)
```cmd
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge
launchers\INSTALAR.bat
```

### Opción B — Instalación manual
```cmd
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge
pip install -r requirements.txt
python bridge_server.py
```

### Dependencias opcionales
```cmd
pip install psutil    # Security Monitor (monitoreo de procesos y puertos)
pip install pymysql   # Game Server Manager (jugadores online desde BD)
pip install pyyaml    # Lectura de game_servers desde config.yaml
```

---

## ▶️ Cómo Usar

### Flujo normal (recomendado)

Abre **un solo archivo** para arrancar todo el ecosistema:
```
launchers\INICIAR_TODO.bat
```
Esto levanta automáticamente:
1. Bridge Server + Dashboard Web (puerto 7860)
2. Motor Fooocus modo CPU (API imágenes, puerto 7861)
3. Vision Studio UI (interfaz de imágenes, puerto 7862)

### Launchers disponibles en `launchers\`

| Archivo | Función |
|---------|---------|
| `INICIAR_TODO.bat` ⭐ | **Arranque completo** — uso diario |
| `INICIAR_SERVIDOR.bat` | Solo Bridge Server + Dashboard (`localhost:7860`) |
| `GRAVITY_VISION_PRO.bat` | Arranca todo el Ecosistema Visión independiente |
| `INICIAR_AUDITOR.bat` | Solo CLI de terminal |
| `INSTALAR.bat` | Instalador TUI |
| `DESINSTALAR.bat` | Desinstalador |
| `INICIAR_FABRICAWEB.bat` | Lanzador motor Web3 / Frontend (Next.js) |
| `Deploy_GravityBridge.bat` | Sync a GitHub |
| `MODO_FANTASMA.vbs` | Auditor sin ventana |

---

## 💻 Uso del CLI

```cmd
gravity                              # Modo interactivo
gravity "explica esta función"       # Pregunta directa
gravity --server                     # Iniciar bridge server
gravity --status                     # Estado de todos los motores
gravity --install                    # Lanzar instalador TUI
```

### Comandos del Auditor

| Comando | Descripción |
|---------|-------------|
| `/help` | Lista todos los comandos |
| `/model` | Cambiar motor/modelo activo |
| `/mode` | Cambiar modo: production / development / Omni-Audit |
| `/providers` | Estado real-time de todos los backends |
| `/keys set\|list\|del` | Gestión de API Keys cifradas |
| `/search <query>` | Búsqueda web inyectada como contexto |
| `/rag <query>` | Búsqueda en índice local de documentos |
| `/index <ruta>` | Indexar archivos/carpetas al RAG |
| `/verify <archivo>` | Auditar código con VerificationAgent |
| `/plan <tarea>` | Modo planificación antes de codificar |
| `/mcp <ruta>` | Conectar servidor MCP externo |
| `/save [nombre]` | Guardar sesión actual |
| `/load <nombre>` | Cargar sesión guardada |
| `/sessions` | Listar todas las sesiones |
| `/cost` | Desglose de costes por modelo |
| `/branch <nombre>` | Fork de la sesión actual |
| `/export md` | Exportar sesión a Markdown |
| `/clear` | Limpiar contexto |
| `!aprende <texto>` | Persiste una regla en el knowledge base |
| `/exit` | Salir limpiamente |

---

## 🌐 Dashboard Web — `localhost:7860`

Accede tras ejecutar `INICIAR_SERVIDOR.bat` o `INICIAR_TODO.bat`.
El dashboard V10.0 incluye **9 paneles**:

| Panel | Descripción |
|-------|-------------|
| 💬 **Chat** | Chat en tiempo real con streaming SSE y Markdown renderizado |
| 🎨 **Vision Studio** | iFrame de Fooocus CPU para generación manual |
| 🖼️ **Image Queue** | Cola SQLite de trabajos · Historial · Progreso en vivo |
| 🚀 **Deploy** | Pipeline npm build → Netlify con log en tiempo real |
| ⚔️ **Game Servers** | Control WoW Vanilla MaNGOS · Start/Stop/Restart · Jugadores · Log |
| 📡 **System Status** | Estado de proveedores con latencia en vivo y gráfica RTO |
| 🛡️ **Security** | Procesos · Puertos TCP · Integridad SHA-256 de archivos críticos |
| 📋 **Audit Log** | Historial de inferencias con tokens, coste y latencia |
| ⚙️ **Config** | API Keys · Ruta de proyecto activo · Links de observabilidad |

---

## ⚔️ Game Server Manager (WoW Vanilla)

Gestión de servidores de juegos directamente desde el Dashboard y la API REST.

### Configuración en `config.yaml`

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

### Endpoints de Game Server

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/v1/gameserver/status` | Estado de todos los servidores registrados |
| POST | `/v1/gameserver/start` | Iniciar servidor `{"server": "wow_vanilla"}` |
| POST | `/v1/gameserver/stop` | Detener servidor |
| POST | `/v1/gameserver/restart` | Reiniciar servidor |
| POST | `/v1/gameserver/command` | Enviar comando GM |
| GET | `/v1/gameserver/log?server=wow_vanilla&lines=100` | Últimas N líneas del log |
| GET | `/v1/gameserver/players?server=wow_vanilla` | Jugadores online (requiere pymysql) |

---

## 🛡️ Security Monitor

Daemon que escanea cada 60 segundos:
- **Procesos**: Detecta procesos nuevos vs los conocidos al arranque
- **Puertos TCP**: Compara puertos en escucha con lista blanca configurable
- **Integridad**: Hash SHA-256 de archivos críticos del core
- **Alertas**: Registradas con nivel CRITICAL / WARNING / INFO

Requiere `pip install psutil` para funcionalidad completa.

---

## 🎨 Generación de Imágenes (Vision Studio)

Arquitectura de dos capas unificadas en CPU:

```
Vision Studio UI (7862) ──→ fooocus_client.py ──→ Fooocus API (7861)
         ↑                                                    ↓
  Interfaz Gradio                                   Ryzen 7 8700G (CPU/fp32)
  (Prompt, Aspect Ratio,                            JuggernautXL SDXL
   Performance, Styles)                             Output → /outputs/
```

**Generación CPU-safe:** El modo CPU previene crashes de DirectML. Espera 60-90 segundos para inicialización del motor, luego las generaciones toman entre 3 a 8 minutos.

---

## 📊 API Completa — Referencia de Endpoints

```bash
# Chat e Inferencia
POST http://localhost:7860/v1/chat/completions    # Chat con streaming SSE
GET  http://localhost:7860/v1/models              # Modelos disponibles
GET  http://localhost:7860/v1/status              # Estado del sistema + versión

# Auditoría y Métricas
GET  http://localhost:7860/v1/audit               # Audit Log JSON (últimas 100)
GET  http://localhost:7860/metrics                # Métricas formato Prometheus
GET  http://localhost:7860/health                 # Health check básico

# Imágenes
POST http://localhost:7860/v1/generate            # Generar imagen (síncrono)
POST http://localhost:7860/v1/queue/add           # Encolar trabajo de imagen
GET  http://localhost:7860/v1/queue               # Estado de la cola
GET  http://localhost:7860/v1/images              # Imágenes generadas
GET  http://localhost:7860/v1/fooocus/status      # Estado del motor Fooocus

# Seguridad
GET  http://localhost:7860/v1/security            # Estado del Security Monitor
POST http://localhost:7860/v1/security/scan       # Forzar escaneo inmediato

# Deploy
POST http://localhost:7860/v1/deploy              # Iniciar pipeline build+deploy
GET  http://localhost:7860/v1/deploy/status       # Estado del último deploy

# Game Servers
GET  http://localhost:7860/v1/gameserver/status   # Estado de todos los servidores
POST http://localhost:7860/v1/gameserver/start    # Iniciar servidor
POST http://localhost:7860/v1/gameserver/stop     # Detener servidor
POST http://localhost:7860/v1/gameserver/restart  # Reiniciar servidor
POST http://localhost:7860/v1/gameserver/command  # Comando GM
GET  http://localhost:7860/v1/gameserver/log      # Log del servidor
GET  http://localhost:7860/v1/gameserver/players  # Jugadores online

# Keys (cifrado DPAPI)
POST http://localhost:7860/v1/keys                # Guardar API Key cifrada
```

---

## 📁 Estructura del Proyecto

```
Gravity_AI_bridge/
├── launchers/                 ← Todos los scripts de arranque
│   ├── INICIAR_TODO.bat       ← Arranque completo (recomendado)
│   ├── INICIAR_SERVIDOR.bat
│   └── ...
├── core/                      ← Módulos de infraestructura (26 módulos)
│   ├── security_monitor.py    ← [V10.0] Vigilancia procesos, puertos, integridad
│   ├── image_queue.py         ← [V10.0] Cola SQLite de generación de imágenes
│   ├── deploy_manager.py      ← [V10.0] Pipeline build → Netlify automatizado
│   ├── game_server_manager.py ← [V10.0] Gestión WoW Vanilla / MaNGOS
│   └── ... (22 módulos existentes)
├── providers/                 ← Plugins de proveedores IA
├── tools/                     ← Herramientas del agente + Vision Studio
│   ├── fooocus_client.py      ← Cliente Fooocus HTTP Bridge
│   └── native_trigger.py      ← Trigger REST puro para Fooocus
├── web/dashboard.html         ← SPA Dashboard V10.0 (9 paneles)
├── rag/                       ← Motor RAG híbrido
├── wiki/                      ← Documentación técnica completa
├── _archivo/                  ← Archivos obsoletos (limpieza ordenada)
├── ask_deepseek.py            ← CLI principal (Auditor Senior)
├── bridge_server.py           ← Servidor HTTP OpenAI-compatible
├── dashboard.py               ← Servidor del Dashboard SPA (hot-reload)
├── health_check.py            ← Herramienta de diagnóstico
├── config.yaml                ← Configuración principal
└── _image_queue.sqlite        ← BD persistente de cola de imágenes
```

---

## 🛠️ Requisitos del Sistema

| Componente | Mínimo | Recomendado |
|-----------|--------|-------------|
| Python | 3.10 | 3.11+ |
| RAM | 8 GB | 16 GB+ |
| OS | Windows 10 | Windows 11 |
| Motor IA | LM Studio / Ollama | LM Studio (activo en tu sistema) |
| CPU solamente | Ollama (CPU) | Fooocus (CPU --all-in-fp32) |
| AMD GPU / iGPU | LM Studio / Ollama | Fooocus (CPU --all-in-fp32) |

---

## 🌐 Integración con IDEs

```
Base URL: http://localhost:7860/v1
API Key:  gravity-local
Modelo:   gravity-bridge-auto
```

Archivos de configuración incluidos:
- `.continue/config.json` — Continue.dev
- `.vscode/settings.json` — VS Code

---

## 📖 Documentación Completa

| Documento | Descripción |
|-----------|-------------|
| [Arquitectura](wiki/Arquitectura.md) | Diagrama y decisiones de diseño |
| [Guía de API](wiki/Guia_API.md) | Referencia completa de todos los endpoints |
| [Manual de Usuario](wiki/Manual_Usuario.md) | Tutorial paso a paso |
| [FAQ](wiki/FAQ.md) | Preguntas frecuentes |
| [Game Server Guide](wiki/Game_Server_Guide.md) | Guía completa de Game Server Manager |

---

## 🤝 Contribuir

Lee [CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) · [SECURITY.md](SECURITY.md)

---

## 📜 Licencia

Distribuido bajo la **Licencia MIT** (2026). Ver [LICENSE](LICENSE) para detalles.

---

<div align="center">

Desarrollado con ❤️ por **DarckRovert**

[![Twitch](https://img.shields.io/badge/Twitch-darckrovert-9146FF?logo=twitch)](https://twitch.tv/darckrovert)
[![GitHub](https://img.shields.io/badge/GitHub-DarckRovert-181717?logo=github)](https://github.com/DarckRovert)

*Gravity AI Bridge — Orquestando la inteligencia local, la seguridad y el entretenimiento.*

</div>
