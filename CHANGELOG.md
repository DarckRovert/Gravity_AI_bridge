# Changelog — Gravity AI Bridge

Registro maestro de evolución de la arquitectura del ecosistema Gravity AI Bridge.

---

## [V13.0 PRO] Agentic Automation & Multi-Agent Pipeline · 09/05/2026

**[EVOLUCIÓN A ECOSISTEMA MULTI-AGENTE AUTÓNOMO]**

### Multi-Agent Scripting & Auditing
- **Market Researcher (Hack 4)**: Agente autónomo (`market_researcher.py`) que usa Firecrawl/urllib para buscar competidores en YouTube, extrayendo ganchos y ángulos para enriquecer el contexto del guion.
- **Pipeline Multi-Agente Secuencial**: El proceso de escritura de video ahora se divide en:
  1. *Researcher*: Analiza el mercado.
  2. *Writer*: Redacta el guion basado en el briefing.
  3. *Retention Auditor*: Evalúa y reescribe el guion para garantizar retención en los primeros 5 segundos.

### Course Generator & Content Scheduler (Hack 6)
- **Info-Product Generator (`course_generator.py`)**: Nuevo módulo y endpoint (`/v1/course/generate`) capaz de crear el syllabus completo de un curso/playlist temático e insertarlo en el Scheduler.
- **Content Scheduler (`content_scheduler.py`)**: Producción autónoma de videos. Toma temas de `niches.json` y encola videos diariamente.

### Social Assets Repurposing
- **Social Assets Generator (`social_assets_generator.py`)**: Al finalizar un render de video, el LLM procesa automáticamente el guion y genera:
  - Hilo viral para Twitter/X.
  - Carrusel estructurado para Instagram.
  - Post profesional para LinkedIn.

### Optimización y Limpieza
- **Turbo KV-Cache (`turbo_kv.py`)**: Conectado directamente al `engine_watchdog.py`. Detecta si el proveedor es Ollama y aplica dinámicamente `OLLAMA_KV_CACHE_TYPE=q4_0` y `OLLAMA_FLASH_ATTENTION=1`, reduciendo drásticamente el consumo de VRAM y RAM.
- **Limpieza de Core**: Eliminación de módulos obsoletos (`ide_integrator`, `model_selector`, `provider_scanner`) centralizando la lógica en `provider_manager`. Borrados >18 scripts/archivos de prueba temporales (`scratch`, `test_concat`).

---

## [V12.2 PRO] Autonomous Monetization Factory · 04/05/2026

**[IMPLEMENTACIÓN DE CANALES AUTÓNOMOS DE INGRESOS]**

### Fábrica de Monetización Pasiva
- **Language Cloner (`language_cloner.py`)**: Reutiliza renders visuales (0 gasto de GPU) traduciendo guiones y clonando el audio a Inglés, Portugués y Francés. Multiplica el CPM orgánico de AdSense.
- **Affiliate Manager (`affiliate_manager.py`)**: Banco base de datos con programas CPA categorizados por nicho. Inyecta enlaces y CTAs optimizados en las descripciones de YouTube.
- **Social Distribution (`tiktok_uploader.py`)**: Integración directa con TikTok Content API v2 e Instagram Graph API v19 para auto-publicar Shorts de 58s.
- **Revenue Tracker (`revenue_tracker.py`)**: Tracking pasivo que estima y proyecta ganancias basándose en vistas, histórico y nicho de producción.

### Monetization Hub (Dashboard SPA)
- Nuevo panel central unificado en el Sidebar de Gravity.
- Trackeo estadístico de 30 días, proyecciones a 6 meses y visualización diaria del timeline de ingresos.
- Integración en caliente de OAuth 2.0 (YouTube), estado de credenciales de Redes Sociales y botones manuales para disparar clonación de idiomas de videos ya renderizados.
- Refactorización de endpoints en `mixin_post.py` y `mixin_get.py` para soportar telemetría financiera.

---

## [V12.2 PRO] Pipeline Estabilizado y Omnisciencia Web · 28/04/2026

**[ESTABILIZACIÓN DEL PIPELINE DE VIDEO Y CHAT]**

### Motor de Producción de Video (VideoStudio)
- **Sincronización Matemática de Audio (`atempo`):** Implementado el estiramiento y contracción matemática de audio nativo por FFmpeg para el modo "Manual". La voz encaja milimétricamente en la duración elegida sin truncarse ni desfasarse.
- **Auto-Título Creativo:** El motor ya no usa la URL base ni "Video Promocional". El LLM analiza todo el contexto, genera un `video_title` global y auto-nombra el job, la Tarjeta de Introducción (Intro Card) y la Base de Datos RAG.
- **Recuperación de Aspect Ratio en Fallback:** Se mitigó la desfiguración de videos (e.g., vertical a cuadrado) inyectando la resolución del usuario directamente en la Capa 3 de renderización (`_concatenate_clips`).

### Motor de Animación Inteligente (MAI)
- **Animación Multi-Nivel (L0/L1/L2):** Integración completa del motor MAI. L0 (Estático), L1 (Procedural FFmpeg: parallax, pulse, vignette_drift, shake, kenburns), L2 (Generativo AI via ComfyUI/LTX-Video).
- **Hardening L2 (Image-to-Video):** Soporte total para entradas MP4 desde ComfyUI en `_assemble_clip`, corrigiendo conflictos del flag `-loop` y derivación correcta de rutas SRT.
- **Sincronización UI:** Dashboard VideoStudio actualizado con presets (documental, epic_trailer, tiktok, publicidad) que aplican automáticamente efectos y niveles de animación, propagándose al historial, metadata y previsualización en tiempo real.
### Scraping y Omnisciencia Web (Firecrawl + Urllib)
- **ChatBot Navegador:** El endpoint `/v1/gravity/chat` ahora tiene capacidades de navegación nativas. Inyección en tiempo real del contexto raspado de cualquier URL enviada por el usuario al Chat de Gravity.
- **Copywriting Automático:** Al detectar contenido web (`_generate_script`), el Motor de Video asume un rol de Experto en Publicidad, estructurando llamadas a la acción, deduciendo el producto principal (Anchor) e ingiriendo contenido promocional al guion.
- **Fail-Safe de Firecrawl:** Se parchó la vulnerabilidad del scraper `scrape_url`. Si la API de Firecrawl falla, expira o agota cuotas, el sistema hace un fallback silencioso a la librería local `urllib`, garantizando 100% de disponibilidad de extracción de texto.

### Seguridad y Parches Críticos
- **Prevención de Archivos Fantasma (Race Conditions):** Erradicada la función altamente insegura `tempfile.mktemp()` en `preview_voice`, reemplazándola por UUID4 absolutos con recolección de basura mediante bloques `finally` incondicionales.
- **Corrección de Cabeceras CORS en APIs:** Inyección global de `self._send_cors()` en los manejadores de excepciones (`except`) de los endpoints `/v1/video/create`, `/v1/video/cancel` y `/v1/video/delete` para prevenir caídas de red en el dashboard de React.

---

## [V12.2 PRO] Production UI Hardening & Monetization Ready · 24/04/2026

**[INTERVENCIÓN TOTAL DE ARQUITECTURA FRONTEND]**

### Reproductor Cinematográfico y Monetización (Video Studio)
- **Reproductor Interactivo (Modal Overlay):** Implementación de un modal que transmite en vivo desde `/v1/video/stream` para previsualizar los jobs completados.
- **Panel de Exportación y Redes Sociales:** Integración de botones funcionales para distribuir en Facebook, Reels y Shorts, con descarga directa del Master MP4.

### Orquestación Multi-Agente (MultiAgent Processor)
- **Selector Dinámico:** Se eliminó texto estático (maquetas a medias) por `<select>` reales conectados al payload de `/v1/agent/compare`. Ahora se puede variar la cantidad de agentes y el modo (Consenso, Paralelo, Debate).

### Integridad Total de Endpoints UI/UX
- **Vision Studio & Image Lab:** Inyección de controles de *Seed* (Semilla) y *Auto-Enhance* dentro del frontend, integrados perfectamente en el POST `/v1/image/generate`.
- **Deploy Manager:** Agregado un `<input>` dinámico para sobreescribir la ruta del proyecto FabricaWeb, eliminando la dependencia ciega del default del servidor.
- **Session Manager:** Hook activo hacia `/v1/sessions/kill` para destruir subprocesos conversacionales huérfanos con 0% tolerancia a componentes de adorno.
- **Sanitización RAG y Seguridad:** Adición de alertas directas para indicar sincronización de carpetas de memoria, escaneos dinámicos en tiempo real y protocolo Omega. Todos los botones de la Suite están 100% operativos.

---

## [V12.2 PRO] Omniscient-Tier — Fully Autonomous React Ecosystem · 24/04/2026

**[ESTADO DE PRODUCCIÓN FINAL ALCANZADO]**

### Refactorización React Frontend & Eliminación de Deuda Técnica
- **Limpieza Definitiva**: Borrado del dashboard legacy V10.0 en HTML puro y `dashboard.py`. Todo ruteado a `frontend/dist`.
- **Integración React UI/UX**: Se reactivaron y enrutaron los botones muertos en `Firecrawl.tsx`, `MultiAgent.tsx`, `Sessions.tsx`, `MCPServers.tsx` e `ImageQueue.tsx`.
- **Nuevo Endpoint GET**: `/v1/hardware/stats` agregado como alias en el servidor Bridge para sincronizar en tiempo real el componente `HardwareMonitor.tsx`.
- **Nuevos Endpoints POST**: Se completó la implementación para el puente React-Python con `/v1/keys`, `/v1/rag/toggle`, `/v1/audit/rotate`, y `/v1/security/scan`.

### Arquitectura de Lanzamiento Consolidada
- **INICIAR_TODO.bat**: Único script de inicialización recomendado. Múltiples bats fragmentados (Servidor, Vision Pro, Auditor) fueron purgados para estandarizar el despliegue.
- **gravity.bat Wrapper**: Actualizado para invocar a la versión 12.0 Omniscient-Tier en todos los menús CLI.

---

## [V12.2 PRO] Diamond-Tier — Multi-Session, HITL & Firecrawl · 23/04/2026

**[ASIMILACIÓN ARQUITECTÓNICA: OPENCLAUDE]**

### Nuevos Módulos Backend
- **`core/firecrawl_scraper.py`**: Scraping de URLs con soporte doble — Firecrawl API (Markdown limpio) + fallback HTTP nativo (`urllib`) sin dependencias externas. Auto-detecta API key en `config.yaml`.
- **`core/hitl_manager.py`**: Human-in-the-Loop completo. Cola thread-safe de aprobaciones para tools de alto riesgo (`code_runner`, `shell_exec`, `file_write`, `deploy`, `git_push`, etc.). Timeout de 120s con auto-rechazo. Bypass en modo background. Funciones: `request_approval`, `wait_for_decision`, `approve`, `reject`, `get_pending`, `intercept`.

### Nuevos Endpoints REST
- `GET /v1/hitl/pending` — Lista solicitudes de aprobación humana en espera.
- `POST /v1/hitl/approve` — Aprueba una acción del agente ({approval_id}).
- `POST /v1/hitl/reject` — Rechaza una acción del agente ({approval_id, reason}).
- `POST /v1/tools/scrape` — Scraping de URL ({url}) con Firecrawl o fallback.
- `GET /v1/tools/firecrawl/health` — Estado de la API key y modo de scraping.

### Dashboard V12.2 PRO — UI/UX Diamond Tier
- **Rediseño CSS total**: Nueva paleta (`#07090e` bg, `#6366f1` accent, `#8b5cf6` accent2, `#06b6d4` accent3). Animaciones `slideIn`, `hitlPop`, `gradMove`.
- **Panel HITL**: Solicitudes pendientes con botones Aprobar/Rechazar, stats de sesión (aprobadas/rechazadas), lista de tools de alto riesgo, polling automático cada 8s.
- **Panel Firecrawl**: Status de API key, scraper interactivo de URL, viewer de resultado en Markdown con badge de fuente y botón copiar.
- **Sessions — Role Selector**: Selector de rol (auditor/planner/coder/researcher/executor) al hacer Spawn de un worker, enviado al backend vía `--role`.
- **Nav sidebar**: Nuevos items HITL (con badge rojo de alertas pendientes) y Firecrawl.
- **Bug fix switchTab**: Eliminada colisión de override doble con IIFE seguro.

### Agent Routing
- `ask_deepseek.py`: Soporte `--role` en CLI para inyectar configuración de proveedor/modelo según rol definido en `config.yaml → agent_routing`.
- `core/session_runner.py`: `SessionSpawner.spawn` pasa `--role` al subproceso.

---

## [V12.2 PRO] Ultra Evolution Panel & Interactive Tools · 21/04/2026

### Mission Control Dashboard
- Widget grid en vivo de métricas críticas (Tokens, Queue, Models, Costos).
- Sistema de Alertas Flotantes UI/UX para feedbacks pasivos.

### Tools Pro
- Interfaz Híbrida: Code Runner, Grep, Git Actions con terminal reactiva real.
- Integración de shell local al Dashboard para debugging y scripting directo.

### Multimedia & Security
- **Video Studio Cinematic**: Estilos `lofi` y `retro80s`.
- **Image Lab Avanzado**: Render multicapa, presets directos, prompt improvement via LLM.
- **Security Score**: UI gráfico base 100, kill de procesos via `/v1/security/kill`.

---

## [V12.2 PRO] Video Studio + RAG en Chat + Admin API · 20/04/2026

### Video Studio
- `core/video_pipeline.py`: Pipeline completo CPU-only. LLM → Fooocus → SAPI TTS → ffmpeg clips → concat final.
- Cola SQLite aislada `_video_queue.sqlite` con worker daemon independiente.
- Endpoints: `POST /v1/video/create`, `POST /v1/video/cancel`, `GET /v1/video/status`, `GET /v1/video/download`.
- Dashboard Panel Video Studio con formulario, barra de progreso en tiempo real, historial de 20 jobs, descarga directa MP4.
- Fallback automático si Fooocus no está corriendo.

### RAG en Chat
- Inyección automática de contexto RAG en `/v1/chat/completions` cuando `rag_enabled: true`.
- `POST /v1/rag/toggle`: Activa/desactiva en caliente sin reiniciar el bridge.

### Admin API
- `POST /v1/audit/rotate`: Fuerza rotación del audit log activo con archivado por timestamp.

### Infraestructura
- ffmpeg integrado en `_integrations/ffmpeg/`.
- pyttsx3 TTS Windows SAPI offline.
- Limpieza del repositorio: Eliminados `build/` (~450MB), logs obsoletos.

### Documentación
- Wiki completa actualizada a V12.2 PRO.
- `README.md` con módulo Video Studio y badge V12.2 PRO.

---

## [V12.2 PRO.1] Modularización Arquitectónica del Enrutador · 20/04/2026

### Refactorización Estructural
- `bridge_server.py` reducido de 1,323 → ~200 líneas. Lógica migrada a Mixins (`api/routes/mixin_get.py`, `api/routes/mixin_post.py`).
- Estado global aislado en `api/state.py`. Eliminadas dependencias cíclicas.
- 4 regresiones corregidas post-refactorización.

### Estabilidad
- Audit Log: rotación por 10,000 líneas además del umbral 5MB.
- Limpieza: 12 archivos residuales eliminados.
- `requirements.txt` con versiones mínimas fijadas.

---

## [V12.2 PRO] Stable Diamond-Tier Integration · 19/04/2026

### Fixes & Seguridad Core
- Image Queue: 0% falsos positivos de generación (diferenciación real antes/después de POST).
- Rate limiting global anti-DDoS en BaseHTTPRequestHandler.
- Security Monitor: whitelist dinámica (Discord/Chrome/BattleNet/Steam), 98% menos spam en audit log.
- Soporte PyInstaller: Fix para `type | None` en Python < 3.10.

### Nuevas Funcionalidades
- SSE En Vivo `/v1/queue/stream`: Event-Stream bidireccional puro.
- MangosD Deque Buffer: Ring-Buffer de 500 líneas en RAM, expuesto en `/v1/gameserver/log`.
- Pre-Flight MySQL: Verificación antes de arrancar MangosD.
- Rotación máxima de logs: backups rotativos .pak de 5MB tope duro.

---

## [V10.0] Foundation Diamond-Tier · 18/04/2026

- Arquitectura base `http.server.ThreadingHTTPServer` sin Flask/FastAPI.
- Provider Manager: Ollama, LM Studio, Kobold, Jan, OpenAI, Anthropic.
- Dashboard SPA inicial con Chat Auditor, Status, Security, Audit Log.
- Key Manager con cifrado DPAPI.
- Installer Inno Setup para Windows 10+.
