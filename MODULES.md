# 📦 Documentación de Módulos (Architecture)

La capa V4.0 God-Tier sigue una filosofía modular pura. Cada sistema se aísla, previendo que en un futuro los módulos puedan usarse como librería `import gravity` en otros proyectos Python.

## Core Modules

### 1. `provider_scanner.py` (El Descubridor Estelar)
Un escáner multihilo no bloqueante de red.
**Responsabilidad:** Rastrear los puertos locales `[11434, 1234, 8000, 1337]`.
**Superpoder:** Es capaz de extraer no solo los modelos instalados, sino deducir **cuál está cargado y pesando en la VRAM de tu GPU**, permitiendo a todo el stack preferir enviar peticiones al motor que ya está caliente y evitar 3 segundos eternos de "cold start".

### 2. `bridge_server.py` (El Corazón Proxy)
Servidor minimalista en CPython plano (cero dependencias como FastAPI para máxima compatibilidad).
**Responsabilidad:** Implementar las especificaciones `GET /v1/models` y `POST /v1/chat/completions`.
**Superpoder:** Actúa como enrutador dinámico. Un IDE que envíe un prompt pesado al server no sabe si esto es Ollama o LM Studio; el servidor local proxy escanea el mejor módulo, altera el schema del payload, lo envía y trae de vuelta los streams binarios transparentes al editor.

### 3. `ask_deepseek.py` (La Capa de Presentación Inteligente)
El front-end cli de la aplicación y gestor de estado.
**Responsabilidades:**
- **UI:** Gestiona el CLI Rich en tiempo real (spinners, panels, alineaciones V4).
- **Control de Mando:** Parsea regex y prefijos `!`, `/`.
- **Ecosistema IO:** Posee el código que soporta pipes directos (`sys.stdin`), permitiendo su uso global en bash.

### 4. `health_check.py` (Módulo Visual de Triage)
Encargado de invocar al Scanner de forma visual la primera vez y actuar de escudo (si no hay motores encendidos de fondo en tu PC, el health check frena al software antes de emitir exceptions sucios por toda la terminal).

## Componentes de Almacenamiento Cifrado (State)
Gravity no usa SQLite. Todo es JSON portátil.
- `_settings.json`: La verdad universal del entorno.
- `_knowledge.json`: Reglas duras adheridas sintéticamente al System Prompt.
- `_history.json`: Historial efímero activo.
- `_saves/`: El multi-verso donde se guardan sesiones enteras archivadas y listas para cargar.
