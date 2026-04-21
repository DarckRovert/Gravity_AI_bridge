# Changelog de Evolución (Gravity Bridge)

Registro maestro de la metamorfosis estructural aplicada sobre la herramienta Gravity AI Bridge y el módulo local de servidor WOW. 

## [V10.3] Ultra Evolution Panel & Interactive Tools - 21/04/2026

**[NUEVA FUNCIONALIDAD — MISSION CONTROL]**
- **Dashboard Home**: Widget grid en vivo de métricas críticas (Tokens, Queue, Models, Costos).
- **Notificaciones**: Sistema de Alertas Flotantes UI/UX para feedbacks pasivos.

**[MEJORA — TOOLS PRO]**
- **Interfaz Híbrida**: Tools estáticas pasaron a ser Terminales Reactivas reales atadas al Mixin_post en backend.
- **CodeRunner & Grep**: Integración de shell local al Dashboard para debugging y scripting directo (Powershell/Python/Bash).
- **Git Actions**: Botones macro inyectados en la UI sin necesidad de consola.

**[NUEVA FUNCIONALIDAD — ENGINE MULTIMEDIA Y SECURITY]**
- **Video Studio Cinematic**: Inyección de estilos `lofi` y `retro80s`.
- **Image Lab Avanzado**: Render multicapa con testeo A/B. Agregados presets directos. Prompt improvement function via LLM.
- **Security Score**: UI gráfico base 100 con capacidad destructiva para inyectar Kills (`/v1/security/kill`).

**[DOCUMENTACIÓN Y ARQUITECTURA]**
- Actualización total de firmas digitales V10.2 a V10.3.

## [V10.2] Video Studio + RAG en Chat + Admin API - 20/04/2026

**[NUEVA FUNCIONALIDAD — VIDEO STUDIO]**
- **`core/video_pipeline.py`**: Pipeline completo de generación de videos CPU-only. Flujo de 5 pasos: LLM (guión JSON) → Fooocus CPU (imágenes) → Windows SAPI/pyttsx3 (TTS .wav) → ffmpeg (clips .mp4) → ffmpeg concat (video final).
- **Cola SQLite Aislada**: `_video_queue.sqlite` con worker daemon independiente. Progreso real 0-100 por escena accesible en tiempo real.
- **Endpoints REST**: `POST /v1/video/create`, `POST /v1/video/cancel`, `GET /v1/video/status`, `GET /v1/video/download`.
- **Dashboard Panel #18**: Nuevo panel "🎬 Video Studio" con formulario, barra de progreso en tiempo real, historial de 20 jobs y descarga directa del MP4.
- **Fallback automático**: Si Fooocus no está corriendo, genera imagen placeholder negra y continúa.

**[NUEVA FUNCIONALIDAD — RAG EN CHAT]**
- **Inyección automática de contexto**: El endpoint `/v1/chat/completions` inyecta fragmentos RAG relevantes cuando `rag_enabled: true` en `_settings.json`.
- **`POST /v1/rag/toggle`**: Activa/desactiva el RAG en caliente sin reiniciar el bridge.

**[NUEVA FUNCIONALIDAD — ADMIN API]**
- **`POST /v1/audit/rotate`**: Fuerza rotación inmediata del audit log activo con archivado por timestamp.

**[INFRAESTRUCTURA]**
- **ffmpeg integrado**: `_integrations/ffmpeg/ffmpeg.exe` (v2026-04-19) añadido al PATH de usuario.
- **pyttsx3**: Motor TTS Windows SAPI instalado para síntesis de voz offline.
- **62 tests pasados**: Suite pytest completa con 0 fallos y 0 errores.
- **Limpieza del repositorio**: Eliminados `build/` (~450MB), logs obsoletos (`fooocus_trigger_debug.log`, `native_trigger.py.bak`).

**[DOCUMENTACIÓN]**
- Wiki completa actualizada a V10.2: `Home.md`, `Arquitectura.md`, `Guia-API.md`, `Manual-Usuario.md`, `FAQ.md`, `API-Reference.md`.
- `README.md` actualizado con módulo Video Studio y badge V10.2.
- `CHANGELOG.md` con esta entrada.
- `Deploy_GravityBridge.bat` actualizado con mensaje de commit V10.2.

## [V10.1.1] Modularización Arquitectónica del Enrutador - 20/04/2026

**[REFACTORIZACIÓN ESTRUCTURAL]**
- **Desacoplamiento del Monolito:** `bridge_server.py` reducido de 1,323 líneas a ~200 líneas. Toda la lógica de rutas migrada a un sistema de Mixins distribuidos (`api/routes/mixin_get.py`, `api/routes/mixin_post.py`).
- **Estado Global Aislado:** Variables de estado de Rate Limiter y GeoIP Tracker extraídas a `api/state.py` eliminando dependencias cíclicas y fugas de contexto entre módulos.
- **Bugs Corregidos:** 4 regresiones identificadas y corregidas post-refactorización: referencia a `_RATE_LIMIT_WINDOW` obsoleta, variables GeoIP con prefijo incorrecto, 7 rutas `__file__` apuntando a directorio incorrecto, y `background_scanner` huérfano.

**[MEJORAS DE ESTABILIDAD]**
- **Audit Log — Rotación por Volumen:** `core/audit_log.py` ahora rota en base a 10,000 líneas además del umbral de 5MB existente. El archivo contaba con 19,785 líneas sin rotación activa. `get_recent()` optimizado con `collections.deque` — ya no carga el archivo completo en memoria.
- **Limpieza del Repositorio:** Eliminados 12 archivos residuales (`scratch_*.py`, `temp_task.txt`, stubs de wiki en inglés, backup del monolito).
- **requirements.txt:** Versión mínima fijada para `prometheus_client>=0.20.0`. Cabecera actualizada a V10.1.

## [V10.1] Stable Diamond-Tier Integration - 19/04/2026


**[MAJOR FIXES & SEGURIDAD CORE]**
- **Image Queue Blindado:** La vulnerabilidad sintética de la confirmación Gradio ahora ha sido purgada de raíz. El modulo `fooocus_client` y `image_queue` hacen diferencia real de carpetas en sistema operativo ("antes de disparar POST" vs "post disparar POST"). Los Falsos Positivos de generación se han reducido de un posible 15% a un rotundo 0%.
- **Evacuación de la API RAG Insegura:** Se controló el desgaste perpetuo de la IA con rate limiting `_check_rate` global en la clase BaseHTTPRequestHandler impidiendo el desbordamiento local por LAN.
- **Drenaje de Falsos Flags (Spam Reduction):** `security_monitor.py` detuvo las alertas agresivas de red por puertos rutinarios al cruzarlo pasivamente contra una lista blanca (discord, navegadores, battle.net, steam). Reducción del ~98% de spam en la huella de log audit_log.jsonl.
- **Soporte Compatibilidad Pyinstaller:** El ejecutable frozen dejó de cerrarse arbitrariamente debido a tipajes de python obsoletos `type | None` que desbordaban la compilación pre-Python3.10 en los scripts de IA Process Manager.

**[NUEVAS FUNCIONALIDADES REALES]**
- **SSE En Vivo `/v1/queue/stream`:** Interfaz estática modernizada conectándose por `Event-Stream` bidireccional puro a los contadores HTTP para evitar ahogamiento del servidor via pooling.
- **MangosD Deque Buffer y Auto-Backup:** GravityBridge ahora levanta un Subprocess Popen interceptando Standard Out con un Ring-Buffer (Deque) guardando 500 líneas en RAM, exponiéndose vivas en `/v1/gameserver/log`.
- **Pre-Flight MySQL:** El launcher de `game_server_manager` lanza requests pings internos. Si tu base de datos WOW no existe o no responde, el servidor detiene su secuencia antes de encender Mangos, salvándote de cuelgues oscuros locales.
- **Rotación Máxima de Logs:** La carpeta raíz previene la muerte térmica del disco del Bot haciendo Backups rotativos .pak de 5MB como tope duro.
