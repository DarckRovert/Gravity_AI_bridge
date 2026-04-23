# Changelog — Gravity AI Bridge

Registro maestro de evolución de la arquitectura del ecosistema Gravity AI Bridge.

---

## [V10.4] Diamond-Tier — Multi-Session, HITL & Firecrawl · 23/04/2026

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

### Dashboard V10.4 — UI/UX Diamond Tier
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

## [V10.3] Ultra Evolution Panel & Interactive Tools · 21/04/2026

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

## [V10.2] Video Studio + RAG en Chat + Admin API · 20/04/2026

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
- Wiki completa actualizada a V10.2.
- `README.md` con módulo Video Studio y badge V10.2.

---

## [V10.1.1] Modularización Arquitectónica del Enrutador · 20/04/2026

### Refactorización Estructural
- `bridge_server.py` reducido de 1,323 → ~200 líneas. Lógica migrada a Mixins (`api/routes/mixin_get.py`, `api/routes/mixin_post.py`).
- Estado global aislado en `api/state.py`. Eliminadas dependencias cíclicas.
- 4 regresiones corregidas post-refactorización.

### Estabilidad
- Audit Log: rotación por 10,000 líneas además del umbral 5MB.
- Limpieza: 12 archivos residuales eliminados.
- `requirements.txt` con versiones mínimas fijadas.

---

## [V10.1] Stable Diamond-Tier Integration · 19/04/2026

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
