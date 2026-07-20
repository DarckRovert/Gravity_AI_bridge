# Changelog — Gravity AI Bridge

Registro maestro de evolución de la arquitectura del ecosistema Gravity AI Bridge.

## [V30.0 MYTHOS] Monolito de Excelencia & Resiliencia L9 · 20/07/2026

**[MONOLITO V30.0 MYTHOS EDITION — AUDITORÍA UNIVERSAL DE ENDPOINTS, PYDANTIC FRONTIER, GUARDRAILS DETERMINISTAS, SSE STREAM BUS, THERMAL THROTTLING Y HOME ASSISTANT IOT]**

### Arquitectura Nuclear & Resiliencia LLM
- **Pydantic Frontier (`core/llm_frontier.py`)**: Interfaz de validación Pydantic estricta con 3 niveles de auto-corrección para eliminar salidas JSON frágiles de proveedores LLM.
- **Pre-LLM Guardrails (`core/guardrails.py`)**: Intercepción determinista en microsegundos de comandos críticos (`stop`, `reset`, `handoff`) en `/v1/chat/completions` y `/v1/gravity/chat`.
- **Universal LLM Endpoint Auditor (`core/endpoint_auditor.py`)**: Demonio de auditoría continua en segundo plano que prueba la disponibilidad real (`max_tokens: 1`) de los modelos configurados en proveedores cloud y detecta modelos descontinuados (HTTP 404/410).
- **Server-Sent Events (SSE) Stream (`/v1/events/stream`)**: Canal de notificaciones en vivo desacoplado para alimentar el Dashboard React sin polling.
- **Daemon Threading Security (`bridge_server.py`)**: Hilos HTTP configurados como `daemon_threads = True` para evitar congelamientos en apagado o reinicio.

### Sensores & Domótica (J.A.R.V.I.S Tools)
- **Thermal Watchdog (`core/thermal_watchdog.py`)**: Control térmico activo con `psutil` que suspende procesos de inferencia pesados (`ollama`, `ffmpeg`, `comfyui`) si la temperatura supera 85°C.
- **IoT Controller (`core/tools/iot_controller.py`)**: Conexión REST verídica a `/api/states` de Home Assistant para telemetría de sensores, cámaras y alarmas.
- **Tinka Engine (`tools/tinka_engine.py`)**: Motor estadístico real sobre la base de datos `tinka_history.db`.

### Documentación & Auditoría Global
- **Sincronización Total Mythos**: Actualizados `README.md`, `SECURITY.md`, `ULTRA_MASTER_PLAN.md`, `remotion_workspace/README.md`, `landing_page/index.html` y todos los folios de `wiki/`.
- **Purga de Deuda Técnica**: Eliminados más de 20 archivos clonados `(1)` en cachés, assets y logs.

---

## [V17.0 PRO] The Sovereign Forge & Quality Shield · 08/07/2026

**[INTEGRACIÓN DE AGENTE QA ANTI-ALUCINACIONES, MÉTRICAS DE PALABRAS, HITL Y ESTANDARIZACIÓN LITERARIA]**

### La Forja Literaria (Escritura y Refinado Resilientes)
- **Agente QA Integrado (`core/chapter_qa.py`)**: Implementación de un validador anti-alucinaciones autónomo. Realiza análisis semántico sobre capítulos recién generados y refinados comparándolos con el Lore y la sinopsis. Si falla la consistencia, realiza una reescritura correctiva automática en caliente antes de persistir cualquier cambio.
- **Extractor de JSON Robusto**: El Agente QA ahora limpia etiquetas de bloques de código Markdown (````json ... ````) de manera nativa mediante Regex, evitando saltos accidentales de validación por fallos de parseo.
- **Métricas de Palabras en Tiempo Real**: Inyección de acumuladores incrementales de conteo físico de palabras en `book_writer.py`, `fiction_writer.py`, `research_writer.py`, `book_refiner.py` y `research_refiner.py`. Las métricas se actualizan atómicamente en `progreso_metadata.json` o `progreso.json`.
- **Estandarización de Separadores**: Migración absoluta de separadores de capítulos al estándar inmutable `=== CAPITULO ===` en todos los generadores, refinadores y en el empaquetador ePub, eliminando desajustes visuales y falsos positivos causados por el uso tradicional de líneas horizontales (`---`).
- **Modo HITL para Escaletas**: Integración opcional de intercepción humana para depuración de la estructura de capítulos en todos los writers antes de ejecutar la producción por lotes.
- **Limpieza de Invocaciones LLM**: Purga de llamadas directas a `provider_manager.complete` en refinadores, redirigiéndolas exclusivamente a `safe_complete` en `tools.llm_utils` para garantizar reintentos automáticos, limpieza de pensamientos y estabilidad de APIs.
- **PDF Exporter (`tools/pdf_exporter.py`)**: Integración de un motor de exportación profesional para generar copias digitales limpias en formato PDF con portadas embebidas.

---

## [V16.5 PRO] Zero-Trust Architecture & AppData Migration · 03/07/2026

**[BLINDAJE CONTRA GOOGLE DRIVE Y AISLAMIENTO TOTAL DE ESTADO]**

### Migración Definitiva a %LOCALAPPDATA%
- **Inmutabilidad del Directorio Raíz**: Toda la estructura de logs, colas asíncronas SQLite y archivos JSON transitorios de alta frecuencia (como `_periodista_state.json` o `_cost_log.json`) han sido migrados a `%LOCALAPPDATA%\Gravity\Databases` y `%LOCALAPPDATA%\Gravity\Logs`. Esto evita bloqueos de archivos cruzados por motores de sincronización en la nube (ej. Google Drive) durante las operaciones de escritura continua.
- **RAG Migración y Reparación**: Las métricas de estado de la base de memoria vectorial (RAG) han sido actualizadas para extraer telemetría dinámica directamente de la conexión a `index.sqlite` en AppData, purgando dependencias obsoletas hacia el antiguo directorio estático `_rag_index`.

---

## [V16.4 PRO] OODA Loop & Executive Packaging · 27/06/2026

**[CONSOLIDACIÓN AUTÓNOMA Y DESPLIEGUE COMO EJECUTABLE ÚNICO]**

### OODA Loop & Resource Management (`core/resource_watchdog.py`)
- **Resource Watchdog**: Daemon que corre en paralelo al ciclo OODA, vigilando la memoria compartida (VRAM/RAM) en sistemas APU como la Radeon 780M. Al detectar inactividad >120s y carga >65%, termina dinámicamente procesos huérfanos de IAs pesadas (`comfyui`, `lm studio`, `ollama`).
- **Autonomy Engine & Scraping (Orient)**: Inyección nativa del output de `bounty_hunter.py` dentro de la etapa *Orient* del Bucle OODA. Al encontrar nuevos contratos en el RSS de Freelancer o Reddit, la IA lo procesa inmediatamente como una *Oportunidad de Negocio*, trazando el flujo de ejecución (Act).

### Empaquetado Ejecutivo y Compilación (`build_exe.bat` & `build_installer.iss`)
- **Unificación Inmaculada PyInstaller**: Refactorización del flujo de compilación. `gravity_launcher.pyw` y `bridge_server.py` ahora se comprimen nativamente en un único binario **Gravity AI Launcher.exe**, evitando crasheos fatales por dependencias cruzadas.
- **Frontend SPA Integrado**: Todo el React UI es compilado (`npm run build`) y servido directamente desde `/frontend/dist` sin dependencias externas.
- **Instalador InnoSetup**: Script configurado para ensamblar el motor unificado de PyInstaller en un instalador Windows robusto y de mínima huella.

---

## [V16.3.1 PRO] Zero-Crash Frontend & Async Resilience · 27/06/2026

**[BLINDAJE TOTAL DE INTERFAZ REACT CONTRA FALLOS ASÍNCRONOS Y FALSOS POSITIVOS]**

### Frontend UI/UX Refactoring (`frontend/src/components/`)
- **Blindaje Asíncrono Global**: Auditoría y refactorización completa de los 35 submódulos del Dashboard (React + TypeScript). 
- **Prevención de JSON Truncado**: Inyección de una red de seguridad estricta `.catch(() => ({}))` en todas las llamadas `res.json()`. Garantiza que si el backend de Python o un modelo IA local colapsa interrumpiendo el socket HTTP, la UI no crasheará (Unhandled Promise Rejection).
- **Sellado de Falsos Positivos**: Implementación de validación estricta `if (!res.ok)` en mutaciones de estado y triggers de UI. Módulos críticos (como *Monetization Hub*, *System Settings*, *Bounty Hunter*, *Infiltrator*, *Software Factory*, *HITL Approval*, etc.) verifican el éxito HTTP antes de inyectar variables en memoria, evitando desincronizaciones de estado local vs backend.
- **Graceful Error Handling**: Fallbacks dinámicos en promesas múltiples concurrentes (`Promise.allSettled` / `Promise.all`), extracción segura de mensajes de error desde APIs externas, y notificaciones de interfaz precisas vía `showToast`.

---

## [V16.3 PRO] Autonomy & Workflow Engine Integration · 25/06/2026

**[FÁBRICA DE CONTENIDO Y CEREBRO AUTÓNOMO EN LAZOS ASÍNCRONOS]**

### Workflow Engine (`core/workflow_engine.py`)
- **Topological DAG Runner**: Nuevo motor basado en nodos atómicos y recetas JSON (`/workflows/`) para crear fábricas de contenido estandarizado, resolviendo dependencias con el Algoritmo de Kahn.
- **Node Registry Dinámico**: Nodos modulares (RAG, WebSearch, LLMQuery, etc) con interpolación de variables `{{node.output}}`.

### Migración del Reportero Autónomo a Workflow Engine
- **Eliminados monolitos**: `gravity_reporter.py` (26KB), `gravity_essayist.py` (18KB), `gravity_scientist.py` (16KB) archivados en `_archivo/`.
- **Nuevo workflow**: `workflows/reporter.json` — 7 nodos topológicos que replican y superan la funcionalidad del monolito.
- **Nuevos nodos atómicos**:
  - `core/nodes/rss_feed_node.py` — Parser RSS/Atom
  - `core/nodes/news_normalizer_node.py` — Slugify, imagen Pollinations, reparador JSON truncado, filtro `<think>`
  - `core/nodes/json_appender_node.py` — Escritura atómica, dedup por ID, límite configurable
  - `core/nodes/video_job_node.py` — Encola TikTok/Shorts en `core.video.pipeline`
- **Dependencias actualizadas**: `news_daemon.py`, `core/gravity_brain.py` (cmd `publish_news` + system prompt) migrados al motor de workflows.
- **Robustez**: 4 capas de fallback para parseo de JSON del LLM (directo, markdown block, regex brace, repair truncated).

### Autonomy Engine (`core/autonomy_engine.py`)
- **Autonomía Nivel 4**: Integración nativa del Cerebro (OODA Loop) con la fábrica de contenido. Ahora el núcleo puede ejecutar comandos `run_workflow` directamente sin intervención humana y de manera totalmente asíncrona usando threads en background.
- **Robustez de Parseo**: Blindaje de los parámetros generados por el LLM mediante `ast.literal_eval` soportando tanto comillas simples como parámetros opcionales.

---
## [V16.3 PRO] Intelligent Resource Guard & Specialized Task Routing · 23/06/2026

**[MONITOREO DINÁMICO DE RAM EN TIEMPO REAL Y ENRUTAMIENTO DE VISIÓN/EMBEDDINGS NATIVOS]**

### Native Llama Provider (`native_provider.py`)
- **Memory Guard Adaptativo (`psutil`)**: Integración dinámica de `psutil` para monitorear la memoria RAM libre del sistema en tiempo real. Si la RAM libre cae por debajo de 2.5 GB o el porcentaje de uso supera el 88%, el watchdog de inactividad de las IAs locales disminuye adaptativamente de 300s a 15s para limpiar memoria inactiva y evitar cuellos de botella u OOMs.
- **Desalojo LRU Proactivo ante Carga**: Antes de instanciar un nuevo modelo (`llama_cpp.Llama`), se evalúa el tamaño estimado en RAM del modelo GGUF a partir de su tamaño en disco. Si la RAM física libre es insuficiente, realiza un desalojo progresivo de los modelos más antiguos mediante LRU hasta liberar el espacio requerido de forma segura.

### Provider Manager & Autonomous Router (`provider_manager.py`)
- **Enrutamiento Especializado Multicapa**: Soporte y scoring explícito para las tareas de `"vision"` (enrutando a `llava-phi-3-mini-int4.gguf`) y `"embedding"` (enrutando a `nomic-embed-text-v1.5.f16.gguf`) con un bono masivo de +150.
- **Protección de Malas Rutas**: Añadida una penalización estricta de -250 para evitar que el modelo de embeddings (`nomic`) sea seleccionado para chats tradicionales, y una penalización de -60 para evitar que el modelo de visión (`llava`) interfiera en consultas estándar de texto puro.

---

## [V16.2 PRO] The Perfect Machine: Omniscient Router & Zero-Defect Stability · 22/06/2026

### Provider Manager & Autonomous Router (`provider_manager.py`)
- **Blindaje Anti-Caídas (Poison Pill Resilience)**: Reestructuración absoluta del hilo escáner asíncrono. En lugar de bloquear la aplicación entera esperando un motor colgado, ahora existe un temporizador global en tiempo real de 8.0 segundos. Los motores muertos (como un LM Studio que deja de responder) son aislados en contenedores `ProviderResult` sintéticos sin generar excepciones `TypeError`. Cero bloqueos.
- **Enrutamiento Inteligente por Tareas (`_score_model`)**: El router autónomo ahora inspecciona semánticamente los nombres de archivo `.gguf` o IDs de la nube para enrutar el tráfico dinámicamente según la carga de trabajo (`bounty`, `semantic`, `code`, `reason`), primando modelos locales como `Qwen2.5-Coder` o `Hermes-3-Llama-3.1`.

### Native Llama Provider (`native_provider.py`)
- **Gestión Asíncrona de Hardware AMD Ryzen / Vulkan**: El manejador interno de `llama-cpp-python` ahora instancia candados de concurrencia (`threading.RLock`) **a nivel de clase**, evitando colisiones cuando múltiples hilos paralelos (por ejemplo en simulaciones Multi-Agente) intentan inyectar o descargar modelos simultáneamente de la VRAM compartida de la APU (Radeon 780M).
- **Control Activo de Basura (Garbage Collection)**: Refuerzo del bucle `_load_model` para invocar activamente `gc.collect()` tras eliminar de la memoria RAM al modelo menos usado, evitando fugas crónicas de memoria durante sesiones extendidas.

### Multi-Agent Orchestrator (`multi_agent.py` & `bounty_hunter.py`)
- **Streaming Asíncrono Desbloqueado**: Modificada la inferencia de llm para procesarse **fuera del candado exclusivo**, permitiendo que múltiples instancias de agentes corran modelos en paralelo en el ecosistema sin hacer fila, exprimiendo la eficiencia del pipeline.

---

## [V16.1 PRO] Omniscient Chat Commands & Resiliencia · 20/06/2026

**[COMANDOS NATIVOS EN CHAT Y ESTABILIDAD BAJO ALTA CARGA]**

### Chat Auditor (Interfaz & Backend)
- **Botón de Pánico de Memoria (`/limpiar` o `/reset`)**: Limpieza inmediata de la memoria local en React para evitar OOM (Out Of Memory) en LLMs locales, reseteando la UI sin recargar la página.
- **Control RAG Dinámico (`/rag on/off`)**: Inyección de comando en el motor de ruteo (`gravity_brain.py`) para activar o desactivar la búsqueda documental en caliente, modificando el `_settings.json` instantáneamente.
- **Invocador de Fábrica de Software (`/fabrica <idea>`)**: Vinculación síncrona mediante llamada interna a `POST /v1/factory/generate`, permitiendo desarrollar software empaquetado (.zip) directamente desde el chat web con feedback visual en tiempo real.
- **Monitor de Tareas Universal (`/tareas` o `/jobs`)**: Consolidación del estado asíncrono de múltiples daemons (Video Studio, Infiltrator OSINT, VTuber V2V) y métricas de RAM física usando `psutil`, reportado en una consola virtual dentro del chat.
- **Navegador Local On-Demand (`/investiga <tema>`)**: Alias inteligente que mapea hacia el scraper nativo `WebSearch`, dotando al modelo local de acceso a internet bajo demanda.

### Provider Manager (Local LLMs)
- **Tolerancia a Estrangulamiento de RAM (`openai_compat_provider.py`)**: Se extendió drásticamente el `timeout` de los *health checks* de 0.8s a 2.5s. Esto previene que el Bridge descarte erróneamente a proveedores locales (como LM Studio u Ollama) cuando el procesador o la RAM están saturados, garantizando un enlace robusto con la IA en escenarios de alto estrés computacional.

---

## [V16.0 PRO] Motor Cinematic V2.0 PBR — God-Tier Visual Engine · 02/06/2026

**[EVOLUCIÓN A MOTOR GRÁFICO HÍBRIDO GLSL/REMOTION CON POST-PROCESADO HOLLYWOOD]**

### Motor Gráfico GLSL PBR V13 (`core/video/glsl_renderer_v13.py`)
- **Image-Based Lighting (IBL)**: Inyección universal de `uniform sampler2D iChannel0` en los 3 Fragment Shaders principales (`SPACE_ODYSSEY_FS`, `JULIA_FS`, `QUANTUM_TUNNEL_FS`). La imagen AI de Pollinations es mapeada como ecosfera luminosa, generando reflejos fisicamente correctos sobre toda la geometría SDF 3D.
- **Textura Fallback 1×1**: Creada una textura negra de 1×1 pixel que se bindea incondicionalmente a `iChannel0` antes de cada frame para prevenir errores de sampler no-inicializado en GPUs integradas (Intel UHD, AMD Radeon Vega).
- **Cyber Glitch Digital Reactivo** (`COMPOSITE_FS` + `POST_PROCESS_FS`): Efecto de desgarro digital de scanlines horizontales acoplado a la intensidad del bajo (`bass > 0.85`). Desplazamiento asimétrico de coordenadas UV con `glitchShift` + inversión subliminal de colores (`col.rgb = 1.0 - col.rgb`) en franjas aleatorias.
- **Aberración Cromática Extrema**: Separación de canales RGB proporcional a `bass * 2.5 * shake`, simulando lentes anamórficos a máxima apertura en los momentos de mayor energía musical.
- **Film Grain Orgánico Reactivo**: Ruido procedural calculado con `hash2()` cuya amplitud escala con las frecuencias altas (`high`), emulando la textura de película kodak 35mm.
- **Vignette Cinematográfica Profunda**: Oscurecimiento perimetral acentuado (`smoothstep(0.95, 0.2, vdist)`) con vigencia mínima `0.2` en los bordes (vs. `0.35` anterior), encuadrando la atención hacia el centro compositivo.
- **Sincronización `COMPOSITE_FS` ↔ `POST_PROCESS_FS`**: Ambos pipelines de post-procesado ahora comparten exactamente el mismo conjunto de efectos God-Tier, garantizando coherencia visual tanto en el flujo AI-First como en el flujo GLSL puro.

### Generador AI Ultra-Resiliente (`core/video/ai_scene_generator.py`)
- **Cascading de Modelos Pollinations**: Sistema de rotación progresiva de 3 modelos con timeouts expansivos: `flux-realism` (90s) → `flux` (150s) → `turbo` (210s). Mitiga completamente los errores de "respuesta pequeña" (placeholder) que ocurrían en sesiones largas.
- **Fallback Procedural — Nebulosa Fractal (FBM)**: En caso de fallo total de la API en la nube, el sistema genera automáticamente un fondo cósmico de alta calidad usando Numpy. Algoritmo: 6 octavas de Ruido Fractal (Fractional Brownian Motion) → suavizado con filtro gaussiano → mezcla de dos capas de gas cósmico → puntos estelares procedurales aleatorios → viñeta negra perimetral. Produce imágenes de nivel artístico sin red neuronal.

### Pipeline Multi-Parte Shorts (`core/video/pipeline.py`)
- **Fix `except` duplicado**: Corregida la excepción duplicada que bloqueaba silenciosamente la generación de Shorts.
- **Validación `os.path.isfile`**: Añadida verificación de existencia de `temp_short_src` antes de invocar FFmpeg, eliminando el error `Audio no encontrado`.

### Interfaz Interactiva de Shorts (`remotion_workspace/src/ShortTemplate.tsx`)
- **Tipografía Cinematográfica**: Sustitución de `sans-serif` genérico por `Montserrat` e `Inter` (Google Fonts) con pesos 700/900. Importación garantizada via `@import url(...)` en `index.css` para asegurar fidelidad en renderizado headless Chromium.
- **Subtítulos Karaoke God-Tier**: Palabras activas animadas con color `#00f0ff` (Cyan Sci-Fi), `textShadow` de neón multicapa 3D, `scale(1.1)`, `translateY(-10px)` y `rotate(-2deg)`. Transición `cubic-bezier(0.175, 0.885, 0.32, 1.275)` para rebote orgánico.
- **Overlay VHS Scanlines**: Capa CSS `repeating-linear-gradient` con desplazamiento temporal sincronizado a `currentTime * 50 % 4` que simula la interferencia analógica de VHS moviéndose hacia abajo, completando el look Cyberpunk.
- **Viñeta Superior/Inferior (Letterbox)**: Capa `AbsoluteFill` con `inset boxShadow` de 150px arriba y 300px abajo para enmarcar el video central con aspecto cinematográfico de cine.

---

## [V16.0 PRO] Modular Architecture & Route Decoupling · 22/05/2026

**[EVOLUCIÓN A ARQUITECTURA DE SERVICIOS ULTRA MODULAR Y DISTRIBUIDA]**

### Desacoplamiento de Rutas (GET/POST Router)
- **Delegación Dinámica a Controladores (`api/routes/handlers/`)**: Se eliminó por completo el acoplamiento monolítico en `mixin_get.py` y `mixin_post.py`. Ahora todas las rutas se delegan dinámicamente a manejadores controllers independientes (como `video_handler.py`, etc.).
- **Compatibilidad 100% de CORS y Excepciones**: Los handlers capturan y manejan excepciones integrando los encabezados CORS nativos para evitar bloqueos del frontend de React.

### Modularización del Pipeline de Video (VideoStudio Core)
- **Conversión del Monolito a `/core/video/`**: El archivo monolítico original de 129 KB `core/video_pipeline.py` fue dividido en submódulos funcionales altamente mantenibles:
  - `audio_processor.py`: Procesamiento de TTS offline/online, motores Windows SAPI/pyttsx3/Gemini TTS, generadores BGM y normalizaciones.
  - `script_builder.py`: Escritura multi-agente, prompts estructurados para Pollinations/Fooocus, anclaje visual y lore contexts.
  - `renderer.py`: Renderizado de clips de video, Ken Burns, overlays de marca de agua, Remotion integrations y concatenación FFMPEG.
  - `pipeline.py`: Administración e inicialización SQLite con WAL mode, worker daemon thread pools, stuck job recovery y dispatches sociales.
- **Bridge Layer de Retrocompatibilidad (`core/video_pipeline.py`)**: Implementado un puente dinámico en caliente a nivel de módulo Python (`types.ModuleType`) que proxyifica todas las consultas y parches (monkeypatching de tests) de manera transparente a los submódulos. 100% libre de downtime y cero regresiones.

---

## [V16.0 PRO] Real-Time VTuber Engine V4.0 · 13/05/2026

**[EVOLUCIÓN A ARQUITECTURA "GENERATE ONCE, DRIVE REAL-TIME"]**

### Motor de Transferencia Neural de Movimiento
- **LivePortrait ONNX Integrado**: Se descartó la transformación ineficiente "frame-by-frame" con SD-Turbo. Ahora el sistema utiliza `FasterLivePortrait` puro a 30-60 FPS, procesando exclusivamente por DirectML.
- **Bypass de Compilación C++**: Se modificó estructuralmente el código base de LivePortrait (mock de la clase `Face` de Insightface) aislando la inferencia a puros pesos ONNX, eliminando al 100% la dependencia de MSVC Build Tools.
- **Doble Fase V4.0**:
  1. *Fase Generativa (Init)*: SD-Turbo se invoca *una sola vez* al cambiar de preset para generar un `reference_avatar` estático pero perfecto (evitando el flickering).
  2. *Fase Animación (Live)*: LivePortrait intercepta la webcam para trasladar parpadeos, respiración, rotación de cabeza y tracking labial al avatar maestro de manera hiperfluida.

### Actualización de UI (V2V Studio)
- Añadido disparador explícito **"Generar Avatar Base (SD-Turbo)"** para independizar el diseño de la sesión activa de streaming.
- Sincronización WebSocket optimizada con telemetría de estados separada (`base_dirty` y `bg_dirty`).

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
