# 🔌 Referencia Oficial de API del Sistema de Ecosistema Gravity

El puente procesa y levanta sus peticiones bajo HTTP puro local (`127.0.0.1:7860`). Diseñado con candados contra Rate-Limits y limitadores de sesión para estabilidad en entornos con latencia o alto tráfico.

## 📡 Eje de Control y Telemetría del Entorno

### `GET /v1/status`
Recopila el estado binario del Puente y lista el mejor proveedor LLM encadenado a la intranet en el momento (Modelos activos, conectividad a red).
### `GET /v1/hardware`
Extrae del Profiler información fidedigna de las Tarjetas Gráficas y NPU operativas que tu AI asume. Devuelve VRAM, Cores, Threads de CPU de tu servidor.
### `GET /v1/cost`
Devuelve el `session_cost`, `daily_limit` y métricas asociadas al gasto fraccionado e incesante de Tokens IN/OUT operados a la hora.
### `GET /v1/security`
Reporta pasivamente la sanidad operativa de todo subproceso (`security_monitor.py`), descartando por Whitelist interna y auditando si los puertos de fondo sufren injección intrusista, protegiendo Windows Server y World Of Warcraft Server.

## 🧠 Núcleo de Inteligencia Artificial

### `POST /v1/agent/compare`
Motor del Multi-Agent Orchestrator. 
- Acepta parámetros de `messages`, `n_models` y `mode: vote/parallel`.
- Devuelve las percepciones fraccionadas por N inteligencias artificiales concurrentes.

### `GET /v1/rag/status`
Analizador del Retrieval-Augmented Generation (Memoria vectorizada o asociativa del proyecto). Retorna documentos cargados, chunks particionados y peso vivo (MB) listos para ingestión por el LLM en consultas complejas sobre lore o códigos de servidor WoW.
### `GET /v1/sessions`
Lista de estados. Muestra cuantos historiales de conversaciones y "State Locks" tiene el modelo salvaguardado silenciosamente en su base circular interna.

## ⚔️ Game Server (World of Warcraft) y Utilidad Difusiva

### `POST /v1/gameserver/start` y `POST /v1/gameserver/stop`
Maneja directamente los triggers ejecutables compilados del MangosD y RealmD subyacentes. Internamente llama el validador MySQL para anulación antes-del-vuelo e invoca el *AutoBackup Dump* automático del DB Characters resguardado.

### `GET /v1/gameserver/log`
Retorna bajo Event-Deque la colección en vivo (Ram Buffer, 0 discos HDD/SSD gastados) de todo lo que el motor WoW escupe para visualización rápida anti-crash.
### `POST /v1/gameserver/register`
Inyección directa de cuenta con su SRP-6a para servidores MaNGOs, saltando burocracia de consolas In-Game y permitiendo altas HTTP encriptadas.

### `GET /v1/fooocus/status` y `GET /v1/queue`
Verifican el latir del ecosistema Difusor local en puerto `7861`, y consultan las colas de procesamiento paralelos en imagen. Fooocus ahora hace auto-verificación difusora diferencial (`diff` del archivo físico Output).
### `GET /v1/queue/stream`
Flujo puro **SSE Event-Stream Server**. La base para tu FrontEnd. Devuelve métricas `text/event-stream` del progreso asíncrono temporal sin requerir Pooling constante.

## 💻 Automatiza Deploy Remoto (FabricaWeb)

### `GET /v1/fabricaweb/status` y `POST /v1/fabricaweb/deploy`
El puente funciona de Pipeline CI/CD interno. Encripta tu WebApp de front-end alojada en `_integrations` tras leer dinámicamente tu framework desde el `package.json` (`/out`, `/dist`) e incrustándolo hacia hostings de netlify mediante tokens puros o repos locales.

## 🎬 Video Studio V10.3 (CPU-Only)

### `POST /v1/video/create`
Encola un trabajo de generación de video completo. Flujo: LLM (guión) → Fooocus (imágenes, CPU) → pyttsx3/SAPI (TTS) → ffmpeg (ensamblado clips y concatenación). Parámetros: `topic`, `n_scenes` (4–10), `voice_speed` (ppm).

### `POST /v1/video/cancel`
Cancela un trabajo **pendiente** por `job_id`. No interrumpe trabajos en ejecución.

### `GET /v1/video/status`
Estado completo de la cola: pendientes, job activo con `progress` (0–100) y `step` en tiempo real, historial de los últimos 20 videos generados con estado y ruta de salida.

### `GET /v1/video/download?file=nombre.mp4`
Servicio de descarga directa del MP4 generado. Streaming chunk-based (65 KB) para archivos grandes. Validación de path traversal incluida.

## 🛡️ Endpoints de Administración V10.3

### `POST /v1/audit/rotate`
Forza rotación inmediata del audit log activo con archivado por timestamp.

### `POST /v1/rag/toggle`
Activa/desactiva el contexto RAG en el pipeline de chat en caliente. Estado persistido en `_settings.json`.
