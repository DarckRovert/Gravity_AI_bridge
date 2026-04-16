# CHANGELOG — Gravity AI Bridge

Todos los cambios notables se documentan en este archivo siguiendo [Keep a Changelog](https://keepachangelog.com/es/).

---

## [V10.0] -- 2026-04-16 [Gravity Ecosistema Total]

### Nuevos Módulos Core
- **Game Server Manager** (`core/game_server_manager.py`): Gestión nativa de servidores PvP/PvE. Soporte inicial para WoW Vanilla (MaNGOS / AzerothCore). Control de procesos de realm/world, arranque automático (Watchdog), lectura en vivo de logs y consulta a MySQL para lista de jugadores online.
- **Security Monitor** (`core/security_monitor.py`): Daemon de vigilancia perimetral. Escanea puertos TCP activos contra una lista blanca, detecta procesos nuevos y verifica la integridad estática de los archivos del core vía SHA-256. Alertas registradas en `_audit_log.jsonl`.
- **Image Queue** (`core/image_queue.py`): Sistema de cola persistente basada en SQLite (`_image_queue.sqlite`). Permite encolar múltiples peticiones de generación de imágenes por API sin colapsar el servidor HTTP. Worker daemon procesa secuencialmente para CPU-safety.
- **Deploy Manager** (`core/deploy_manager.py`): Pipeline CI/CD local integrado. Detecta binarios `npm` y `netlify`, ejecuta el build `next build` en una ruta definida y hace el deploy automáticamente mediante la Netlify CLI capturando stdout en tiempo real.

### Mejoras Globales
- **Dashboard V10.0 (SPA)**: Incorporados 4 paneles nuevos (Game Servers, Deploy Manager, Security, Image Queue). Los paneles consultan por polling inteligente sólo cuando están activos.
- **Dashboard Hot-Reload**: Refactorización de `dashboard.py` para leer el archivo `web/dashboard.html` del SO durante peticiones HTTP. Desacoplado de la memoria RAM del servidor puente web.
- **ConfigManager Update**: Nueva opción `game_servers` en el `.yaml` central con configuraciones dinámicas. 
- Refactorización de versiones: Limpieza de string patterns pasados (`9.3.1 PRO PRO`).
- API expone 9 nuevos endpoints.

---

## [V9.3.1 PRO] -- 2026-04-14 [Orquestación de Fooocus y Unificación Web]

### Correcciones Críticas (P0)
- **tools/fooocus_client.py**: Resolución definitiva del error `ValueError: needed: 153, got: 0` y la desconexión vía WebSockets (`Unknown protocol: ws`). El trigger ahora realiza un escaneo dinámico de los IDs del cliente de Fooocus y utiliza peticiones REST (HTTP POST) en lugar de sockets, asegurando inmunidad a futuras actualizaciones en la cantidad de parámetros.
- **bridge_server.py / INICIAR_TODO.bat**: Fin de los errores CORS y estado "offline" de la interfaz gráfica. El servidor del Bridge ahora expone un host web local nativo en el puerto 7860 y sirve el Dashboard como Single Page Application local. `INICIAR_TODO.bat` abre el navegador automáticamente a `http://127.0.0.1:7860/` eliminando las llamadas `file:///`.
- **health_check.py**: Se parcheó un vector de debilidad (`UnicodeEncodeError`) en consolas de Windows estándar que no soportaban los Emojis y artes ASCII (`cp1252`), forzando `utf-8` sobre `sys.stdout` nativamente.

---

## [V9.3.1] -- 2026-04-13 [Hotfix -- Arquitectura Real de Fooocus]

### Hallazgo Critico
- **Fooocus 2.5.5 NO expone API REST** (/v1/generation/...): Todos los endpoints retornaban 404. Solo expone UI Gradio. Generaciones via fooocus_client.py fallaban silenciosamente.

### Correcciones P0
- **tools/fooocus_studio_ui.py**: Reescritura. Ahora usa monitoreo de directorio de salida (OUTPUT_DIR). La generacion ocurre en el motor nativo (:7861) y Studio detecta la imagen nueva en disco.
- **tools/fooocus_client.py - health_check()**: Detecta disponibilidad via root URL (Gradio 200 en /), no via endpoint REST inexistente.

### Mejoras
- Galeria: Tab con todas las imagenes generadas y boton de actualizacion manual.
- server_name='0.0.0.0': Accesible desde localhost:7862 y 127.0.0.1:7862.

---

## [V9.3.0] — 2026-04-13 [Next-Level — Unified API & Real Monitoring]

### Nuevo
- **[NEW] `bridge_server.py` → `GET /v1/fooocus/status`**: Endpoint que hace health check real al motor Fooocus (7861), cuenta imágenes generadas y retorna versión del motor. Alimenta el dashboard en tiempo real sin fetch opaco.
- **[NEW] `bridge_server.py` → `POST /v1/generate`**: Endpoint REST nativo para generar imágenes desde cualquier cliente HTTP. Parámetros: `prompt`, `negative_prompt`, `width`, `height`, `num_images`, `performance`, `style_selections`. Retorna JSON con paths de imágenes generadas.

### Correcciones Críticas
- **[P0] `_integrations/Fooocus/Fooocus/config.txt`**: Todos los `path_*` de modelos apuntaban a `F:\Fooocus_win64_2-5-0` (inexistente). Fooocus cargaba relativo como fallback (frágil). Fix: rutas absolutas al directorio interno `_integrations/Fooocus/Fooocus/models/`. Elimina todas las advertencias de arranque.

### Mejoras
- **`web/dashboard.html`**: `checkFooocusBackend()` reemplazado. Antes hacía un `fetch modo no-cors` opaco que nunca reportaba estado real. Ahora consume `/v1/fooocus/status` y muestra: online/offline, versión, cantidad de imágenes generadas.
- **`launchers/INICIAR_TODO.bat`**: Tiempo de espera entre Motor Fooocus (paso 3) y Studio UI (paso 4) incrementado de 5s a 15s. Evita que Studio UI intentara conectar al motor no inicializado.
- **Banners de versión**: Sincronizados a V9.2 en `core/engine_watchdog.py`, `core/provider_manager.py`, `core/config_manager.py`, `health_check.py`.

---

## [V9.2.1] — 2026-04-13 [Hotfix — Fooocus Args]

### Correcciones Críticas
- **[P0] `_integrations/Fooocus/run_amd.bat`**: `--cpu` y `--disable-cuda-malloc` son argumentos inexistentes en Fooocus 2.5.5 (verificado en `ldm_patched/modules/args_parser.py`). Fooocus arrancaba y cerraba inmediatamente con `error: unrecognized arguments`. Fix: migrado a `--always-cpu` + `--disable-async-cuda-allocation` (args válidos reales).
- **[P0] `_integrations/Fooocus/Fooocus/config.txt`**: `path_outputs` apuntaba a `ComfyUI-Zluda/output` (directorio inexistente post-migración). Fix: ruta corregida a `_integrations/Fooocus/Fooocus/outputs` (directorio real).
- **[P1] `health_check.py`**: banner de versión desactualizado a `V9.0 PRO`. Fix: actualizado a `V9.2 PRO`.
- **[P1] `fooocus_client.py` / `fooocus_studio_ui.py`**: docstrings y comentarios internos referenciaban `--cpu` (arg inválido). Fix: actualizados a `--always-cpu`.

---

## [V9.2 PRO] — 2026-04-13 [Diamond-Tier Edition]

### Correcciones Críticas
- **[P0] Pipeline de imágenes**: Fooocus crasheaba con `RuntimeError: cast_bias_weight` en sampler `dpmpp_sde_gpu` por incompatibilidad con DirectML. Fix: `--directml --always-normal-vram` → `--cpu --all-in-fp32` en `run_amd.bat`. Sampler cambiado a `euler` (CPU-safe) en `fooocus_client.py`
- **[P0] `bridge_server.py`**: `from dashboard import DASHBOARD_HTML` fallaba silenciosamente porque `dashboard.py` nunca exportaba esa constante. Resultado: el dashboard servía siempre el fallback básico en vez del SPA premium. Fix: `DASHBOARD_HTML: bytes` ahora se expone a nivel de módulo en `dashboard.py`
- **[P0] `tests/test_core.py`**: `from core.logger import sanitize_json` producía `ImportError` — la función no existía. Fix: `sanitize_json(data: dict) -> dict` agregada a `core/logger.py`
- **[P1] `tests/test_server.py`**: aserción `version == "8.0"` contra un servidor que devuelve `"9.1"`. Test nunca pasaba. Fix: versión actualizada a `"9.2"`
- **[P1] `providers/cloud/anthropic_provider.py`**: `BETAS = "interleaved-thinking-2025-05-14"` — fecha posterior a la actual causaba `400 Bad Request`. Fix: `"interleaved-thinking-2025-01-05,output-128k-2025-02-19"`
- **[P2] `core/logger.py`**: `StreamHandler` sin encoding UTF-8 en Windows → `UnicodeEncodeError` en consolas cp1252. Fix: `sys.stdout.reconfigure(encoding='utf-8', errors='replace')`
- **[P2] `bridge_server.py`**: rutas de imágenes hardcodeadas a `ComfyUI-Zluda/output` (engine eliminado). Fix: búsqueda dual en `Fooocus/outputs` y `ComfyUI-Zluda/output` con recursive glob

### Mejoras de Funcionalidad
- `tools/fooocus_studio_ui.py`: cold-start detection con 30 reintentos (2 min). Timeout de polling extendido a 15 min para CPU. Eliminada manipulación incorrecta de `sys.path`
- `tools/fooocus_client.py`: agrega `get_latest_outputs()`, `poll_job()` con timeout configurable. `generate_image()` usa sampler `euler` + `steps: 30`
- `launchers/INICIAR_TODO.bat`: agrega Paso 4 — inicia `fooocus_studio_ui.py` en puerto 7862. Limpia también puerto 7862 en pre-flight
- `providers/cloud/gemini_provider.py`: modelo ID actualizado `gemini-2.5-pro-exp-03-25`, añadido `gemini-2.0-flash-thinking-exp-01-21`
- `providers/cloud/anthropic_provider.py`: añadido `claude-3-7-sonnet-20250219` a la lista

### Sincronización de Versiones
- `bridge_server.py` status endpoint: `"9.1"` → `"9.2"`
- `ask_deepseek.py` banner: `V9.0 PRO` → `V9.2 PRO`
- `config.yaml` header: `V8.0` → `V9.2`
- `core/data_guardian.py` default knowledge: `"version": "8.0"` → `"9.2"`

### Configuración
- `config.yaml`: nueva sección `fooocus` con parámetros CPU-safe documentados
- `_integrations/Fooocus/run_amd.bat`: reescrito con encoding ASCII, modo `--cpu --all-in-fp32 --disable-cuda-malloc`

---

## [V9.1 PRO] — 2026-04-13 [Diamond-Tier Edition]

### Nuevas Funcionalidades
- `launchers/INICIAR_TODO.bat` — Launcher unificado que arranca todo el ecosistema con un clic
- `tools/fooocus_studio_ui.py` — Vision Studio con tabs completos: Settings, Styles, Models, Advanced
- `web/dashboard.html` — SPA V9.1: tab Vision Studio con iFrame integrado y galería de imágenes generadas
- Endpoint `GET /v1/images` y ruta `/static/output/` para servir imágenes desde ComfyUI

### Correcciones Críticas
- **[P0]** `requirements.txt`: typo `raiohttp` → `aiohttp` que impedía la instalación
- **[P0]** `tools/fooocus_studio_ui.py`: `get_latest_image()` comparaba nombres contra paths absolutos (set-mismatch) → nunca detectaba imagen nueva. Reescrito con `get_all_images()` + `get_newest_image()` usando set-difference de paths absolutos
- **[P1]** `fooocus_studio_ui.py`: parámetro inválido `server_ports=[]` en Gradio 6.12 → crash al iniciar. Reemplazado por variable de entorno `GRADIO_SERVER_PORT`
- **[P1]** `fooocus_studio_ui.py`: `inbrowser=False` → el browser nunca se abría automáticamente
- **[P1]** `bridge_server.py`: versión hardcodeada como `"8.0"` en `/v1/status` → actualizada a `"9.1"`
- **[P2]** Timeout de espera de imagen: 90s → 360s (necesario para primera compilación ZLUDA en Radeon 780M)

### Refactoring y Limpieza
- Eliminados todos los stubs `.bat` de la raíz (usuario accede desde `launchers/`)
- Eliminados: `dev_utils/` (19 scripts V5-V7 obsoletos), `tools/fooocus_client.py` (duplicate legacy), `%VBS_PATH%` (corrompido), `questvoice_debug.txt`, `temp_task.txt`, `_knowledge.json.bak_*`, `.antigravityrules.example`, `_last_scan.json`
- `launchers/GRAVITY_VISION_PRO.bat`: reescrito con liberación preventiva de puertos, detección de ComfyUI ya activo
- `launchers/Deploy_GravityBridge.bat`: reescrito con confirmación de usuario, resumen de cambios y manejo de errores

### Documentación
- `README.md`: reescrito completo con tabla de launchers, sección Vision Studio, requisito AMD HIP SDK
- `wiki/Arquitectura.md`: diagrama actualizado con pipeline Vision Studio, tabla de puertos del sistema
- `wiki/Guia_API.md`: documentados endpoints `/v1/images` y `/static/output/`, versión 9.1 en ejemplos
- `wiki/Manual_Usuario.md`: nueva sección §3 Launchers, nueva sección §7 Vision Studio con guía AMD HIP
- `wiki/FAQ.md`: nueva sección completa de Generación de Imágenes con troubleshooting AMD HIP SDK

---

## [V8.1.0] — 2026-04-13 · Satellite Migration (ComfyUI-ZLUDA)

### Añadido
- **ComfyUI Satellite Engine**: Transición de Fooocus/DirectML a ComfyUI-ZLUDA (HIP transpilation)
- **Hybrid VENV**: Emulación hermética de Python 3.11 con PyTorch CUDA 11.8
- **comfyui_client.py**: Cliente API en puerto 8188 con workflow SDXL + JuggernautXL

---

## [V8.0.0] — 2026-04-08 [Diamond-Tier Release]

### Añadido

#### CLI / Auditor Senior
- Instalador TUI premium (`INSTALAR.py`) con detección automática de hardware
- First-run wizard con onboarding interactivo
- 20+ comandos CLI: `/keys`, `/save`, `/load`, `/verify`, `/mcp`, `/mode`, `/search`, `/plan`, `/export`, `!aprende`, `/branch`
- Comando global `gravity` con flags `--help`, `--version`, `--install`, `--server`, `--status`

#### Dashboard Web
- SPA interactiva con Chat streaming SSE y Markdown renderizado
- 4 tabs: Chat · Estado del sistema · Audit Log · Configuración de API Keys
- Auto-refresco de métricas cada 15 segundos

#### Bridge Server
- `/v1/status` con `latency_ms` por proveedor
- `/v1/audit` con las últimas 100 entradas JSON
- CORS completo en todos los endpoints

#### Infraestructura
- Audit log JSONL inmutable
- ConfigManager YAML con migración automática desde `_settings.json`
- Rate Limiting por IP y API Key
- Prometheus metrics en `/metrics`
- VerificationAgent adversarial
- MCPAdapter stdio JSON-RPC 2.0
- Cache Engine SQLite WAL con TTL configurable

---

## [V7.1.0] — 2026-04-06

### Añadido
- Detección multi-GPU (iGPU + dGPU) con FEAT-14
- Soporte NPU Ryzen AI (XDNA) en `hardware_profiler.py`
- Cache WAL (SQLite Write-Ahead Logging) para concurrencia real
- Sliding Window de contexto 128k tokens

---

## [V7.0.0] — 2026-04-05

### Añadido
- Sistema de plugins de proveedores (`providers/registry.py`)
- Provider manager con escaneo RTO (Real-Time Observability)
- SessionManager con fork/merge de branches
- RAG híbrido (BM25 + embeddings vectoriales)
- KeyManager con cifrado DPAPI (Windows)
- CostTracker con registro JSON y estimación por modelo

---

## [V6.0.0] — 2026-04-01

- Primera versión pública con Ollama y LM Studio
- CLI básico con Rich
- Bridge HTTP OpenAI-compatible

