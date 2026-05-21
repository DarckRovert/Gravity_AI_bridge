# 🔌 Referencia Completa de API — Gravity AI Bridge V15.0 PRO
**Omniscient-Tier Edition** · Puerto por defecto: `7860` · Base URL: `http://localhost:7860`

---

## 📡 Sistema y Telemetría

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/health` | Health check básico del bridge (HTTP 200 OK) |
| GET | `/v1/status` | Estado completo del bridge, proveedores de IA, latencias y uptime |
| GET | `/v1/models` | Lista de modelos disponibles en todos los proveedores activos (Compatible OpenAI) |
| GET | `/metrics` | Métricas en formato Prometheus (peticiones, tokens, latencias, errores) |
| GET | `/v1/processes` | Lista y estado de procesos y subprocesos locales gestionados por el bridge |

---

## 🧠 Chat & Completions (Compatible OpenAI / Conciencia Sistémica)

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/v1/chat/completions` | Completions de chat estándar con streaming SSE o respuesta completa. Auto-inyecta reglas de `_knowledge.json` y RAG si está activo |
| POST | `/v1/completions` | Endpoint de completions legacy (redirecciona internamente a `/v1/chat/completions`) |
| POST | `/v1/gravity/chat` | Chat avanzado con inyección automática de la conciencia sistémica actual y extracción Firecrawl al vuelo si se detectan URLs |
| GET | `/v1/gravity/context` | Retorna el prompt contextual del sistema que inyecta `gravity_brain.py` para la orquestación total |

---

## 🤖 Multi-Agent Orchestrator

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/v1/agent/compare` | Envía un prompt a múltiples modelos en paralelo y compara sus respuestas |

*Modos soportados:*
- `"parallel"`: Retorna las respuestas individuales de los N modelos.
- `"vote"`: Ejecuta votación consensuada donde un modelo juez califica las respuestas y selecciona la ganadora (`vote_score`).

---

## 💾 Session Manager (Multi-Session Parallel)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/sessions` | Lista las sesiones de conversación persistentes guardadas en la carpeta `_saves/` |
| GET | `/v1/sessions/active` | Retorna la lista de trabajadores de sub-sesiones interactivos (`SessionSpawner`) en ejecución |
| POST | `/v1/sessions/spawn` | Levanta un worker interactivo asíncrono con un rol opcional (`auditor`, `planner`, `coder`, etc.) sin bloquear el bridge principal |
| POST | `/v1/sessions/kill` | Termina forzadamente un worker de sub-sesión activo por su PID |

---

## 🛡️ HITL — Human in the Loop (Seguridad Zero-Trust)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/hitl/pending` | Lista todas las acciones y comandos del agente de alto riesgo que requieren aprobación |
| POST | `/v1/hitl/approve` | Aprueba la ejecución de una acción pendiente por su `request_id` |
| POST | `/v1/hitl/reject` | Rechaza la ejecución de una acción pendiente, indicando el motivo |

---

## 🕷️ Firecrawl / Web Scraper

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/tools/firecrawl/health` | Verifica la validez de la API key de Firecrawl y el estado del servicio |
| POST | `/v1/tools/scrape` | Extrae el contenido limpio de una URL externa directo a Markdown legible |

---

## 🔌 MCP — Model Context Protocol

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/mcp/status` | Estado de las conexiones con servidores MCP, listando herramientas y recursos expuestos |
| GET | `/v1/mcp/resource` | Lee un recurso específico expuesto por un servidor MCP. Requiere parámetros `server` y `uri` |

---

## 📚 RAG (Retrieval-Augmented Generation)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/rag/status` | Estado actual del índice vectorial RAG (número de documentos, chunks y espacio en disco) |
| GET | `/v1/rag/search` | Búsqueda semántica vectorial de prueba. Requiere parámetro query string `?q=consulta` |
| POST | `/v1/rag/toggle` | Activa o desactiva la auto-inyección de fragmentos RAG en el flujo del chat de completions |
| POST | `/v1/rag/ingest` | Ingesta de archivos o texto plano al almacenamiento vectorial persistente |

---

## 🎨 Generación de Imágenes (Fooocus & Pollinations)

### Cola de Imágenes (Fooocus Engine - Local)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/fooocus/status` | Health check del motor local Fooocus (puerto 7861) |
| GET | `/v1/queue` | Estado de la cola de generación de imágenes local |
| GET | `/v1/queue/stream` | EventStream SSE para monitorear el progreso del job en proceso en tiempo real |
| POST | `/v1/queue/add` | Encola un prompt para generación asíncrona |
| POST | `/v1/generate` | Generación directa inmediata (sin cola) vía Fooocus API |
| GET | `/v1/images` | Lista de imágenes generadas localmente en la carpeta de salida |

### Laboratorio de Imágenes (Pollinations.ai - Cloud Flux)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/image/health` | Estado de conectividad con la API externa de Pollinations |
| GET | `/v1/image/lab/history` | Historial de imágenes generadas mediante Pollinations en la sesión actual |
| POST | `/v1/image/generate` | Generación de imágenes al vuelo mediante Flux en cloud (Diamond-Tier bypass) |

---

## 🎬 Video Studio & Motor de Animación MAI (L0/L1/L2)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/video/status` | Retorna la cola de videos: pendientes, progreso en tiempo real del job activo e historial |
| GET | `/v1/video/list` | Lista de archivos de video `.mp4` generados y guardados en el directorio `_videos/` |
| GET | `/v1/video/voices` | Retorna la lista de voces SAPI5 locales instaladas en el sistema para la narración |
| GET | `/v1/video/animations` | Retorna el catálogo completo de efectos del Motor de Animación Inteligente (MAI L0/L1/L2) |
| GET | `/v1/video/engines` | Estado del motor de renderizado de video y configuraciones generales del pipeline |
| GET | `/v1/video/download` | Descarga el archivo MP4 generado. Parámetro: `?file=nombre.mp4` |
| GET | `/v1/video/stream` | Transmite el flujo de video en streaming directo al reproductor. Parámetro: `?path=nombre.mp4` |
| GET | `/v1/video/thumbnail` | Extrae y sirve la imagen miniatura de una escena. Parámetro: `?path=ruta_relativa` |
| POST | `/v1/video/create` | Inicia la generación asíncrona de un nuevo video desde un tema, guion y escenas |
| POST | `/v1/video/preview_voice` | Genera una vista previa rápida de audio con una voz y velocidad específicas |
| POST | `/v1/video/cancel` | Cancela un trabajo de video pendiente en la cola |
| POST | `/v1/video/delete` | Elimina el registro del historial de un trabajo de video y opcionalmente sus archivos en disco |

---

## 💰 Suite de Monetización Pasiva & Content Scheduler

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/scheduler/status` | Estado del planificador autónomo, hora de próxima publicación e histórico de ejecuciones |
| GET | `/v1/scheduler/niches` | Retorna los nichos de mercado activos configurados en `niches.json` |
| POST | `/v1/scheduler/trigger` | Fuerza la comprobación y ejecución autónoma del Content Scheduler de inmediato |
| POST | `/v1/scheduler/topic/add` | Agrega un tema de video personalizado para que el scheduler lo procese en su cola |
| GET | `/v1/youtube/status` | Estado de la autenticación OAuth2 de YouTube y tokens del canal |
| GET | `/v1/youtube/auth/url` | Genera y retorna la URL de autenticación OAuth de Google para vincular el canal |
| POST | `/v1/youtube/auth/exchange` | Intercambia el código de autorización de Google por tokens permanentes |
| POST | `/v1/youtube/upload` | Fuerza la subida inmediata de un job de video procesado a YouTube. Requiere `job_id` |
| GET | `/v1/video/upload-status` | Progreso y porcentaje de la subida del archivo MP4 actual a los servidores de YouTube |
| GET | `/v1/youtube/quota` | Información de la cuota diaria consumida y restante de la API de YouTube |
| GET | `/v1/social/status` | Estado de las conexiones de API para TikTok Content API e Instagram Graph API |
| POST | `/v1/social/distribute` | Fuerza la distribución Headless de un video corto (Short) a TikTok/Reels de forma asíncrona |
| GET | `/v1/affiliates/status` | Estado del sistema de afiliación CPA, conversiones estimadas y tasa de clics (CTR) |
| GET | `/v1/affiliates/programs` | Lista de programas de afiliados registrados organizados por nicho comercial |
| POST | `/v1/affiliates/program/add` | Registra un nuevo producto, enlace de afiliado y metadatos en un nicho específico |
| GET | `/v1/language/status` | Estado y disponibilidad del traductor y clonador de voz TTS multilingüe |
| POST | `/v1/language/clone` | Traduce y clona el audio narrativo de un job terminado a idiomas extra (inglés, portugués, francés) |
| GET | `/v1/revenue/summary` | Telemetría financiera consolidada: ingresos estimados totales, desglose de CPM e inversión |
| GET | `/v1/revenue/timeline` | Historial diarioizado de ingresos y vistas acumuladas para representación gráfica |
| GET | `/v1/revenue/top` | Ranking de los videos y nichos que han generado más ingresos acumulados |
| POST | `/v1/revenue/views/update` | Actualiza el contador de vistas externas de un video e indexa las nuevas ganancias calculadas |

---

## 🎭 Real-Time VTuber Engine (Aletheia V2V)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/v2v/status` | Estado del motor VTuber V4.0 (FasterLivePortrait), lista de modelos y configuraciones de avatar |
| POST | `/v1/v2v/init` | Arranca e inicializa el subproceso de FasterLivePortrait ONNX en GPU/CPU |
| POST | `/v1/v2v/drive` | Comienza la inyección de expresiones en caliente hacia el avatar seleccionado usando un video conductor |

---

## 📽️ OBS Studio Control & Gravity Spark API

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/obs/status` | Estado de conexión con el WebSocket v5 de OBS Studio y metadatos de sesión |
| POST | `/v1/obs/connect` | Conecta manualmente al WebSocket de OBS. Body: `{"host": "...", "port": 4455, "password": "..."}` |
| GET | `/v1/obs/scenes` | Devuelve la lista completa de escenas de OBS Studio y la escena activa actual |
| GET | `/v1/obs/scene/items` | Lista los elementos de fuentes que pertenecen a una escena dada |
| GET | `/v1/obs/inputs` | Lista las entradas de audio de OBS, volumen en decibelios y estado de mute |
| GET | `/v1/obs/stream/status` | Indica si OBS está transmitiendo en vivo a la plataforma o grabando en disco |
| POST | `/v1/obs/scene/switch` | Cambia la escena activa de OBS. Body: `{"scene_name": "Nombre Escena"}` |
| POST | `/v1/obs/source/toggle` | Invierte la visibilidad de una fuente. Body: `{"scene_name": "S", "scene_item_id": 12}` |
| POST | `/v1/obs/source/visible` | Establece visibilidad explícita. Body: `{"scene_name": "S", "scene_item_id": 12, "visible": true}` |
| POST | `/v1/obs/stream/start` | Inicia la transmisión en directo en OBS Studio |
| POST | `/v1/obs/stream/stop` | Detiene la transmisión en directo en OBS Studio |
| POST | `/v1/obs/stream/toggle` | Alterna el estado de la transmisión en directo (inicia/detiene) |
| POST | `/v1/obs/record/start` | Inicia la grabación local de video en disco |
| POST | `/v1/obs/record/stop` | Detiene la grabación local de video en disco |
| POST | `/v1/obs/record/toggle` | Alterna el estado de la grabación local (inicia/detiene) |
| POST | `/v1/obs/audio/mute` | Alterna el estado de silencio (mute) de una fuente. Body: `{"input_name": "Mic/Aux"}` |
| POST | `/v1/obs/audio/volume` | Establece el volumen en decibelios. Body: `{"input_name": "Mic", "volume_db": -6.0}` |
| GET | `/v1/obs/overlays` | Lista todos los overlays activos inyectados por Gravity Spark en la sesión |
| POST | `/v1/obs/spark/generate` | Genera un widget dinámico usando IA local e inyecta la Browser Source en OBS |
| POST | `/v1/obs/spark/edit` | Edita en caliente el diseño/lógica de un overlay existente vía prompts asíncronos |
| POST | `/v1/obs/spark/remove` | Elimina la fuente de OBS y borra los archivos HTML generados del disco |
| GET | `/obs-overlay/<overlay_id>` | Sirve de forma estática el widget interactivo generado para su consumo en OBS |

---

## 🖥️ Hardware, Costes & Watchdog

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/hardware` | Perfilado de hardware: GPU (CUDA/ROCm), VRAM, NPU Ryzen AI, RAM y contexto de inferencia óptimo |
| GET | `/v1/cost` | Historial y desglose de costes en dólares por proveedor cloud, límite diario y balance de tokens |
| POST | `/v1/cost/limit` | Configura el límite de coste diario admitido en USD |
| GET | `/v1/watchdog` | Estado del Engine Watchdog (auto-switch entre motores locales y cloud) |
| POST | `/v1/watchdog/unlock` | Libera el lock manual de modelo activo y reactiva el modo de autogestión automática |
| GET | `/v1/audit` | Obtiene el registro inmutable de peticiones registradas por el servidor de auditoría |
| POST | `/v1/audit/rotate` | Archiva el archivo `_audit_log.jsonl` activo e inicializa un registro nuevo en blanco |

---

## 🔐 Seguridad Zero-Trust

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/v1/security` | Alertas del monitor de seguridad, intentos de inyección y auditorías en background |
| GET | `/v1/security/geoip` | Registro y mapa de geolocalización de IPs externas que han consultado la API |
| POST | `/v1/security/scan` | Fuerza una auditoría heurística heurística y escaneo de puertos de inmediato |
| POST | `/v1/security/kill` | Finaliza forzadamente una tarea del sistema o proceso sospechoso por PID |

---

## 🛠️ Sandbox de Herramientas (Tools)

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/v1/tools/run` | Ejecuta de forma controlada scripts en sandbox. Body: `{"code": "...", "lang": "python"}` |
| POST | `/v1/tools/search` | Ejecuta consultas de búsqueda en la web mediante el driver DuckDuckGo sin credenciales |
| POST | `/v1/tools/git` | Orquesta acciones de control de versiones programáticas (status, commit, branch, diff) |
| POST | `/v1/tools/grep` | Ejecuta búsquedas recursivas de patrones de texto en el filesystem local |
| POST | `/v1/tools/scrape` | Scrapeo de HTML/Markdown avanzado de URLs vía Firecrawl o motor alternativo |

---

## ⚙️ Configuración & Proveedores de IA

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/v1/keys` | Guarda de forma segura una API key utilizando Windows DPAPI (cifrado a nivel de usuario) |
| POST | `/v1/universal/config` | Modifica dinámicamente configuraciones en caliente de `config.yaml` |
| POST | `/v1/ai/start` | Arranca el ejecutable o subproceso de un proveedor local configurado (Ollama/LM Studio) |
| POST | `/v1/ai/stop` | Finaliza el subproceso de un proveedor de inferencia local activo |

---

<div align="center">
  <sub><i>© 2026 DarckRovert · Gravity AI Bridge V15.0 PRO Omniscient-Tier · Documentación de Referencia Técnica</i></sub>
</div>
