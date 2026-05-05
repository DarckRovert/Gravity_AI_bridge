<div align="center">
  <img src="https://img.shields.io/badge/GRAVITY_AI-BRIDGE-fff?style=for-the-badge&logo=python&color=07090e" alt="Gravity AI Bridge"/>
  <br><br>

  [![Autor](https://img.shields.io/badge/Author-DarckRovert-818cf8.svg?style=flat-square)](https://github.com/DarckRovert)
  [![Licencia](https://img.shields.io/badge/License-Proprietary-red.svg?style=flat-square)](LICENSE)
  [![Arquitectura](https://img.shields.io/badge/Architecture-Omniscient--Tier-c69c6d.svg?style=flat-square)]()
  [![Release](https://img.shields.io/badge/Release-V12.2-6366f1.svg?style=flat-square)]()
  [![Twitch](https://img.shields.io/badge/Twitch-DarckRovert-9146ff.svg?style=flat-square&logo=twitch)](https://twitch.tv/darckrovert)

  <p align="center">
    <i><strong>Megainteligencia Asíncrona "Local-First" de Grado Corporativo Omniscient-Tier.</strong><br>
    Orquestador universal de LLMs, pipelines multimedia, Game Servers, HITL y scraping web.<br>
    Arquitectura sin dependencias masivas · Zero-Cloud · Control total en 1 PC.</i>
  </p>
</div>

<br>

> [!CAUTION]
> Este es un ecosistema cerrado **Omniscient-Tier Local-First**. No es open-source público.
> Core Operacional Privado de **[DarckRovert](https://github.com/DarckRovert)** — uso estrictamente no comercial.

---

## 🌌 Filosofía y Problema que Resuelve

En el desarrollo tradicional, orquestar clústeres de IA locales (Ollama, LM Studio), motores de difusión (Fooocus), servidores C++ (MangosD/WoW) y pipelines CI/CD desde una sola máquina resulta en colisiones de hardware, puertos huérfanos, OOM en VRAM y latencias de segundos.

**Gravity AI Bridge V12.2** elimina todos estos problemas con Python nativo puro y un frontend React/Vite de alta respuesta. Su filosofía:

- **Zero Dependencias Masivas**: Latencia interna en microsegundos, payload de memoria insignificante.
- **Conciencia Dinámica del Host**: Auto-diagnóstico de RAM y VRAM, ajuste dinámico de `num_ctx` de Ollama en tiempo real según estrés térmico.
- **Local-First**: Sin enviar datos a la nube salvo APIs cloud explícitamente configuradas.
- **Omniscient-Tier Control**: Dashboard SPA (React) unificado con observabilidad total en tiempo real.

---

## 🏛 Módulos del Ecosistema V12.2

### 🧠 Multi-Agent Orchestrator (`core/multi_agent.py`)
- Dispara peticiones REST concurrentes a múltiples modelos/APIs en paralelo.
- **Voting Consensuado / Paralelo / Debate**: 2, 3 o 5 modelos votan la respuesta óptima o debaten un resultado mediante controles de UI nativos.
- **Reasoning Stripper**: Filtra tokens `<think>` de modelos como DeepSeek-R1 via Regex antes de mostrarlos.
- **Agent Routing**: Selección dinámica de modelo/proveedor según `--role` (auditor, planner, coder, researcher, executor).

### 🖥️ Dashboard V12.2 React SPA (`frontend/dist`)
Panel de control unificado con 25 componentes orquestados en tiempo real:

| Panel | Función |
|---|---|
| 💬 Chat Auditor | LLM chat con streaming SSE, plantillas y soporte multi-rol |
| 🏠 Mission Control | KPIs en vivo: tokens, queue, costos, modelos activos |
| 🎨 Vision Studio | UI iframe de Fooocus integrado |
| 🖼️ Image Queue | Cola Fooocus con SSE stream de progreso |
| 🎬 Video Studio | Generación de videos CPU-only con narración TTS |
| 🎨 Image Lab | Generación via Pollinations.ai con historial |
| 🚀 Deploy | Pipeline FabricaWeb → Netlify |
| ⚔️ Game Servers | Control MangosD WoW (start/stop/log/players/backup) |
| 🤖 Multi-Agent | Comparación/voting multi-modelo simultáneo |
| 🖥️ Hardware | Perfil GPU/VRAM/NPU/CPU en tiempo real |
| 💰 Monetización | Hub de ingresos: AdSense, Afiliados CPA, Multi-idioma, Social Uploads |
| 💰 Cost Center | Costos por proveedor, límites diarios, breakdown |
| ⚡ Watchdog | Engine Watchdog: lock/unlock de modelo |
| 💾 Sessions | Sesiones persistentes + workers activos con selector de role |
| 📚 RAG | Estado del índice RAG, activar/desactivar inyección en chat |
| 🔌 MCP Servers | Adaptadores MCP: tools, resources, estado de conexión |
| 🛠️ Tools | Code Runner, Web Search, Git, Grep |
| ⚡ Tools Pro | Versión avanzada con terminal reactiva |
| 🕷️ Firecrawl | Scraping de URLs en Markdown (Firecrawl API o fallback HTML) |
| 🛡️ HITL Approval | Intercepción y aprobación humana de tools de alto riesgo |
| 📡 System Status | Estado completo de backends, latencias, modelos |
| 🔒 Security | Monitor de procesos, puertos, integridad de archivos |
| 📋 Audit Log | Historial de peticiones con rotación automática |
| ⚙️ Configuración | API keys, modelo activo, links rápidos |

### 🔄 Multi-Session Bridge V12.2 PRO (`core/session_runner.py`)
- `CapacityWake` + `SessionSpawner`: hasta 32 subprocesos de agente aislados simultáneos.
- Spawn vía UI con selector de **rol** (auditor/planner/coder/researcher/executor).
- Kill de workers activos con estado PID en tiempo real.
- Endpoints: `POST /v1/sessions/spawn`, `POST /v1/sessions/kill`, `GET /v1/sessions/active`.

### 🛡️ HITL — Human in the Loop (`core/hitl_manager.py`)
- Intercepta tools de alto riesgo: `code_runner`, `shell_exec`, `file_write`, `deploy`, `git_push`, etc.
- Cola thread-safe con timeout de 120s y auto-rechazo.
- Aprobación/rechazo desde el Dashboard en tiempo real con badge de alerta en el sidebar.
- Bypass en modo background (permisos absolutos).

### 🕷️ Firecrawl Scraper (`core/firecrawl_scraper.py`)
- Modo premium: Firecrawl API → Markdown limpio y estructurado.
- Modo fallback: `urllib` nativo sin dependencias externas → texto plano desde HTML.
- Configurable via `firecrawl_api_key` en `config.yaml`.

### 🔌 MCP Adapter (`core/mcp_adapter.py`)
- Protocolo JSON-RPC stdio para servidores MCP externos.
- Auto-reconexión, `list_tools`, `list_resources`, `read_resource`.
- Registro global de adaptadores accesible desde el Dashboard.

### 🎬 Video Studio (Cinematic & Monetization) V12.2 PRO
Pipeline de 5 pasos orquestado en daemon con **Motor de Animación Inteligente (MAI)**:
1. **LLM (Ollama)** → guión JSON estructurado con N escenas y auto-título.
2. **Fooocus (CPU/GPU)** → imagen base cinematográfica 16:9/9:16.
3. **MAI Engine (L0/L1/L2)** → Anima la imagen generada:
   - *L1 (Procedural)*: `kenburns`, `parallax`, `shake` ultra-rápidos vía FFmpeg.
   - *L2 (AI Video)*: Transformación a video vía `ComfyUI` (LTX-Video/SVD) por WebSocket.
4. **Windows SAPI/pyttsx3** → narración TTS offline sincronizada vía `atempo`.
5. **ffmpeg concat** → video final ensamblado y servido vía streaming.

**Reproductor Web Integrado**: Stream de video nativo y panel de exportación a redes (Shorts, Reels, Facebook).

### 💸 Autonomous Monetization Factory
Sistema pasivo integrado en el pipeline de renderizado que multiplica los ingresos orgánicos.
- **Language Cloner**: Traduce guiones (LLM) y genera audio en EN/PT/FR/DE recomponiendo videos con los assets ya renderizados. (Multiplica el CPM orgánico sin gastar GPU).
- **Affiliate Manager**: Banco de 20+ programas CPA categorizados por nicho. Inyecta CTAs dinámicos en las descripciones de YouTube.
- **Social Distribution**: Auto-publicación simultánea a **TikTok** y **Instagram Reels** para viralizar contenido corto (Shorts de 58s).
- **Revenue Tracker**: Dashboard estadístico que proyecta ingresos basados en vistas, CTR y retención por categoría (Finanzas, Historia, etc.).

### 🎨 Image Queue / Fooocus (`core/image_queue.py`)
- Bypass nativo del WebSocket Gradio con validación real de output.
- SSE stream en `/v1/queue/stream` — sin polling, flujo puro de eventos.
- Diferenciación real de imágenes generadas vs. pre-existentes (0% falsos positivos).

### 🕹️ Game Server Manager (`core/game_server_manager.py`)
- Subproceso MangosD con Ring-Buffer Deque de 500 líneas en RAM.
- Pre-flight MySQL antes de arrancar (evita corrupción de Character-Files).
- Auto-backup `mysqldump` en cierre, historial de jugadores, exposición WAN.

### 🧠 RAG (`rag/`)
- Indexación de documentos locales en `_rag_index/`.
- Inyección automática en `/v1/chat/completions` cuando `rag_enabled: true`.
- Toggle en caliente via `POST /v1/rag/toggle`.

### 🔐 Security Monitor (`core/security_monitor.py`)
- Whitelist dinámica (Discord, Chrome, BattleNet, Steam) → 98% menos spam en logs.
- GeoIP tracker de IPs externas con cache.
- Anti-DDoS local: bloqueo por IP tras 120 peticiones en ventana.
- Rotación de audit log en >5MB o >10,000 líneas.

### 💰 Cost Tracker + Rate Limiter
- Contabiliza tokens entrada/salida por proveedor en `_cost_log.json`.
- Límite diario configurable; HTTP 429 al superarlo.
- Rate limiter por IP en ventana de tiempo.

### ⚙️ Engine Watchdog (`core/engine_watchdog.py`)
- Monitorea el mejor proveedor disponible.
- Lock/unlock de modelo para fijar en modo manual.
- Compatible con perfil de hardware (VRAM, CPU cores, RAM).

---

## 🚀 Instalación

### Requisitos
- Windows 10 1809+ (64-bit) o Windows 11
- Python 3.10+ en PATH
- Ollama, LM Studio, o cualquier backend OpenAI-compatible

### Instalación desde Fuente
```bash
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
python bridge_server.py
```

Dashboard disponible en: `http://localhost:7860`

### Instalación con Installer (Windows)
Descargar `Gravity_AI_Bridge_V12.2_Setup.exe` desde [Releases](https://github.com/DarckRovert/Gravity_AI_bridge/releases) y ejecutar como administrador.

---

## ⚙️ Configuración Inicial

```yaml
# config.yaml — campos clave
server:
  port: 7860

# Firecrawl API (opcional — sin key usa fallback HTML)
firecrawl_api_key: ""

# Agent Routing
agent_routing:
  auditor:
    provider: ollama
    model: deepseek-r1:8b
  planner:
    provider: lm_studio
    model: llama-3.1-8b
```

---

## 🔐 Seguridad

Ver [`SECURITY.md`](SECURITY.md) para política de vulnerabilidades y reporte responsable.

---

## 📖 Documentación

| Documento | Contenido |
|---|---|
| [Wiki Principal](./wiki/Home.md) | Índice general |
| [Arquitectura](./wiki/Arquitectura.md) | Diagrama de módulos y flujos |
| [Guía API](./wiki/Guia-API.md) | Todos los endpoints REST |
| [Manual Usuario](./wiki/Manual-Usuario.md) | Guía paso a paso |
| [FAQ](./wiki/FAQ.md) | Preguntas frecuentes |
| [CHANGELOG](./CHANGELOG.md) | Historial de versiones |
| [CONTRIBUTING](./CONTRIBUTING.md) | Cómo contribuir |

---

> [!NOTE]
> Ecosistema local privado V12.2 PRO Omniscient-Tier.
> [**📖 WIKI CORPORATIVA**](./wiki/Home.md) | [📜 CONTRIBUCIÓN](./CONTRIBUTING.md) | [🔒 SEGURIDAD](./SECURITY.md)

<br>

<div align="center">
  <sub><i>© 2026 DarckRovert · Gravity AI Bridge — All architectural assets belong to their proprietary author.</i></sub>
</div>
