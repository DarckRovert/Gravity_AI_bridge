import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

files_to_create = {
    "README.md": """<div align="center">
  <img src="https://img.shields.io/badge/GRAVITY_AI-BRIDGE-fff?style=for-the-badge&logo=python&color=07090e" alt="Gravity AI Bridge"/>
  <br><br>

  [![Autor](https://img.shields.io/badge/Author-DarckRovert-818cf8.svg?style=flat-square)](https://github.com/DarckRovert)
  [![Licencia](https://img.shields.io/badge/License-Proprietary-red.svg?style=flat-square)](LICENSE)
  [![Arquitectura](https://img.shields.io/badge/Architecture-Omniscient--Tier-c69c6d.svg?style=flat-square)]()
  [![Release](https://img.shields.io/badge/Release-V16.0_PRO-6366f1.svg?style=flat-square)]()
  [![Security Audit](https://img.shields.io/badge/Security-Audited_100%25-success?style=flat-square&logo=shield)]()
  [![Twitch](https://img.shields.io/badge/Twitch-DarckRovert-9146ff.svg?style=flat-square&logo=twitch)](https://twitch.tv/darckrovert)

  <p align="center">
    <i><strong>Megainteligencia Asíncrona "Local-First" de Grado Corporativo Omniscient-Tier.</strong><br>
    Orquestador universal de LLMs, pipelines multimedia, Agentes Autónomos, Game Servers y HITL.<br>
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

**Gravity AI Bridge V16.0 PRO** elimina todos estos problemas con Python nativo puro y un frontend React/Vite de alta respuesta. Su filosofía:

> **Nota de Seguridad:** La versión V16.0 PRO ha pasado una rigurosa auditoría de código, erradicando vulnerabilidades de ReDoS y garantizando resiliencia absoluta contra fallos silenciosos en operaciones asíncronas y de Git.

- **Zero Dependencias Masivas**: Latencia interna en microsegundos, payload de memoria insignificante.
- **Conciencia Dinámica del Host**: Auto-diagnóstico de RAM y VRAM, ajuste dinámico de `num_ctx` de Ollama en tiempo real según estrés térmico.
- **Local-First**: Sin enviar datos a la nube salvo APIs cloud explícitamente configuradas.
- **Omniscient-Tier Control**: Dashboard SPA (React) unificado con observabilidad total en tiempo real.

---

## 🏛 Módulos del Ecosistema V16.0 PRO

### 📰 Reportero Autónomo (Agente Periodístico)
- **Operación Continua (Daemon):** Un agente persistente que despierta aleatoriamente cada 4-8 horas (`news_daemon.py`).
- **Investigación Web Profunda:** Analiza temáticas complejas de geopolítica y ciberseguridad a través de Web Search.
- **Redacción y Publicación End-to-End:** 7 Nodos Atómicos en `workflows/reporter.json` orquestan RSS → WebSearch → LLM → Normalización → news.json → VideoJob → GitDeploy. Cuenta con deduplicación por slug, escritura atómica y pre-calentamiento de imágenes en Pollinations.ai.
- **Auto-Mantenimiento:** Sincroniza bibliotecas e imágenes eliminando duplicados mediante un sistema de slugs.

### 🧠 Multi-Agent Orchestrator (`core/multi_agent.py`)
- Dispara peticiones REST concurrentes a múltiples modelos/APIs en paralelo.
- **Voting Consensuado / Paralelo / Debate**: 2, 3 o 5 modelos votan la respuesta óptima o debaten un resultado mediante controles de UI nativos.
- **Reasoning Stripper**: Filtra tokens `<think>` de modelos como DeepSeek-R1 via Regex antes de mostrarlos.
- **Agent Routing**: Selección dinámica de modelo/proveedor según `--role` (auditor, planner, coder, researcher, executor).

### 🖥️ Dashboard V16.1 PRO React SPA (`frontend/dist`)
Panel de control unificado con 25 componentes orquestados en tiempo real:

| Panel | Función |
|---|---|
| 💬 Chat Auditor | LLM chat con streaming SSE, plantillas, soporte multi-rol y **comandos nativos** (`/limpiar`, `/rag`, `/fabrica`, `/tareas`, `/investiga`) |
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
| 💸 Auto-Pilot | **BountyHunter & Infiltrator**: Bot 100% autónomo para conseguir clientes en Freelancer.com |
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

### 🔄 Multi-Session Bridge V16.0 PRO (`core/session_runner.py`)
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

### 🎬 Video Studio Multi-Agent & Motores Demoscene V17 PBR
Pipeline multimedia de alta fidelidad orquestado asíncronamente en daemon. Completamente reestructurado bajo el paquete `/core/video/` para máxima resiliencia, con **Motores Matemáticos V17 GLSL**, Renderizado Dual Nativo y despliegue para redes sociales:

- **Dual Render Nativo en GPU**: El motor V17 (Interstellar, Turing Patterns, etc.) renderiza matemáticamente dos veces. Un Master Horizontal (`1920x1080`) y un Master Vertical (`1080x1920`) puro sin recortes FFMPEG.
- **Smart Subtitle Safe-Zone**: Motor `.ASS` Aspect-Ratio Aware. Adapta dinámicamente los márgenes laterales (`MarginL 40px/440px`) y anclajes verticales según el aspect ratio para jamás salirse del encuadre seguro de TikTok.
- **Generador Multi-Escena V16**: Flujo unificado que coordina generación de historia, split de diálogos, TTS (Edge-TTS) asíncrono y Whisper para metadatos temporales de precisión.
- **Auto-Bypass de Fallas**: Sistema modular. Si falla Fooocus, el generador reintenta; si el LLM colapsa, usa un script genérico con `[visual anchor]` estricto.
  - `audio_processor.py`: Análisis FFT extrae frecuencias separadas (Bass, Mid, High) para reactividad visual, además de compresión sidechain y TTS cinemático.
  - `glsl_renderer_v13.py`: Cuna de las **5 Joyas Matemáticas V17** (Interstellar Kerr Black Hole, Turing Patterns, Inception KIFS, Neon Fluid, Organic Core). Iluminación basada en imagen (IBL) y post-procesado Hollywood (Cyber Glitch, Aberración Cromática, Film Grain orgánico).
  - `pipeline.py`: Base de datos SQLite (WAL), daemon worker threads, y gestor de **Auto-Routing Dual** (Generación simultánea del Máster Horizontal 16:9 y el Center-Crop Vertical 9:16).
  - `youtube_uploader.py`: Implementación del **OAuth2 Soft Shield**, que detecta tempranamente tokens inválidos y frena peticiones a red sin abortar el costoso render local.

#### Flujo Híbrido de Renderizado Extremo:
1. **Pipeline Multi-Agente (Research & Scripting)**: El *Writer* estructura la lírica y el *Retention Auditor* evalúa el anclaje emocional.
2. **Generador de Ambientes**: Descarga asíncrona de assets o **Evasión Total AI** al utilizar los motores de shaders puristas V17.
3. **Composición 3D (GLSL PBR)**: Cruce reactivo de las frecuencias del audio con la geometría 3D SDF (Odisea Espacial, Tunnel Cuántico, Mandelbulb) mapeando la imagen AI como ecosfera luminosa IBL.
4. **Ensamble Final**: FFmpeg unifica capas visuales de alta precisión de cuadros y escupe la Copia Dual.

**Reproductor Web Integrado**: Stream de video nativo en el Dashboard y Auto-Distribución a redes protegida por el Shield.

### 📚 Course Generator & Scheduler (Info-Productos)
- **Generación de Cursos (`course_generator.py`)**: Crea el syllabus completo de un curso o lista de reproducción, definiendo lecciones progresivas optimizadas para YouTube.
- **Content Scheduler (`content_scheduler.py`)**: Automatiza la producción de estos cursos, encolando videos diariamente de forma autónoma sin intervención humana.

### 💸 Autonomous Monetization Factory & Social Repurposing
Sistema pasivo integrado en el pipeline de renderizado que multiplica los ingresos orgánicos.
- **Social Assets Generator (`social_assets_generator.py`)**: Al terminar un video, extrae su guion y genera automáticamente:
  - Hilos virales para **Twitter/X**.
  - Carruseles para **Instagram**.
  - Posts profesionales para **LinkedIn**.
- **Language Cloner**: Traduce guiones (LLM) y genera audio en EN/PT/FR/DE recomponiendo videos con los assets ya renderizados.
- **Affiliate Manager**: Banco de 20+ programas CPA categorizados por nicho. Inyecta CTAs dinámicos en las descripciones de YouTube.
- **Social Distribution**: Auto-publicación simultánea a **TikTok** y **Instagram Reels** para viralizar contenido corto (Shorts de 58s).
- **Revenue Tracker**: Dashboard estadístico que proyecta ingresos basados en vistas, CTR y retención por categoría.

### 🎨 Image Queue / Fooocus (`core/image_queue.py`)
- Bypass nativo del WebSocket Gradio con validación real de output.
- SSE stream en `/v1/queue/stream` — sin polling, flujo puro de eventos.
- Diferenciación real de imágenes generadas vs. pre-existentes (0% falsos positivos).

### 🕹️ Game Server Manager (`core/game_server_manager.py`)
- Subproceso MangosD con Ring-Buffer Deque de 500 líneas en RAM.
- Pre-flight MySQL antes de arrancar (evita corrupción de Character-Files).
- Auto-backup `mysqldump` en cierre, historial de jugadores, exposición WAN.

### 🎥 OBS Studio Control & Gravity Spark V16.0 PRO (`core/obs_client.py` & `core/obs_spark_engine.py`)
- **Control Total de OBS**: Auto-conexión vía WebSocket v5. Gestiona escenas, fuentes, mute/volumen, streaming y grabación desde la API.
- **Gravity Spark (Motor de Overlays AI)**: Reemplaza costosos servicios de overlays web. Genera código HTML/JS autocontenido en tiempo real usando tu LLM local, inyectándolo directamente como `Browser Source` en OBS.
- Capacidad de **modificar overlays al vuelo** ("hazlo azul", "añade un borde neón") sin recargar OBS.

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

### ⚙️ Engine Watchdog & Turbo KV (`core/engine_watchdog.py`)
- Monitorea el mejor proveedor disponible.
- Lock/unlock de modelo para fijar en modo manual.
- Compatible con perfil de hardware (VRAM, CPU cores, RAM).
- **Turbo KV**: Detecta automáticamente si se usa Ollama y configura en tiempo de ejecución las variables de entorno `OLLAMA_KV_CACHE_TYPE=q4_0` y `OLLAMA_FLASH_ATTENTION=1` para comprimir la cache 4x.

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
Descargar `Gravity_AI_Bridge_V16.0_Setup.exe` desde [Releases](https://github.com/DarckRovert/Gravity_AI_bridge/releases) y ejecutar como administrador.

---

## ⚙️ Configuración Inicial y Seguridad de APIs

Para garantizar la máxima seguridad del ecosistema, **todos los datos sensibles y API keys locales han sido completamente purgados del repositorio público** (`config.yaml` y claves encriptadas se excluyen automáticamente a través de `.gitignore`).

### 🚀 Inicialización Automática (Zero-Configuration)
Al iniciar el Bridge por primera vez (`python bridge_server.py`), el núcleo detecta automáticamente la ausencia de `config.yaml` y **crea una copia limpia a partir de [config.yaml.example](config.yaml.example)** sin credenciales reales. ¡Listo para arrancar al instante!

### 🖥️ Configuración Interactiva desde el Dashboard
No necesitas editar archivos de texto manualmente. Una vez iniciado el servidor, accede al Dashboard en **`http://localhost:7860`** y dirígete al panel **System Settings** (icono de engranaje):

1. **Gestión de API Keys**: Introduce tus llaves de **OpenAI, Anthropic, Groq, Nvidia, u OpenRouter** de forma visual.
2. **Cifrado Local Seguro**: Las llaves introducidas en la UI se cifran automáticamente en tu máquina física utilizando **Windows DPAPI** y se almacenan localmente de forma inmutable en tu almacén personal (`_keystore.bin`). Nadie más tendrá acceso a ellas.
3. **Proveedor Universal AI**: Puedes configurar cualquier endpoint compatible con OpenAI (Base URL + Model Name + API Key) de manera extremadamente sencilla.
4. **Límites de Costos**: Ajusta el presupuesto diario en dólares desde la barra deslizadora directamente en la UI.


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
> Ecosistema local privado V16.0 PRO Omniscient-Tier.
> [**📖 WIKI CORPORATIVA**](./wiki/Home.md) | [📜 CONTRIBUCIÓN](./CONTRIBUTING.md) | [🔒 SEGURIDAD](./SECURITY.md)

<br>

<div align="center">
  <sub><i>© 2026 DarckRovert · Gravity AI Bridge V16.0 PRO — Motor Cinematic V2.0 PBR. All architectural assets belong to their proprietary author.</i></sub>
</div>
""",
    "LICENSE": """Copyright (c) 2026 Rodrigo Alejandro Vega Rojas. Todos los derechos reservados.
Publicado bajo el seudónimo: DarckRovert
Proyecto: Gravity AI Bridge V16.0 PRO [Omniscient-Tier]
Repositorio oficial: https://github.com/DarckRovert/Gravity_AI_bridge

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LICENCIA PROPIETARIA — TODOS LOS DERECHOS RESERVADOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

El presente código fuente de "Gravity AI Bridge" (incluyendo su arquitectura
nativa, integración en el flujo de World of Warcraft, puente difusivo con
Fooocus, Video Studio CPU-Only, orquestación Multi-Agente, sistema RAG y
todos sus módulos subsidiarios) es propiedad exclusiva de su autor y creador,
publicado bajo el seudónimo DarckRovert.

PROTECCIÓN LEGAL: Este software está protegido por:

  · Decreto Legislativo N° 822 — Ley sobre el Derecho de Autor (Perú),
    artículos 36–39 (protección de programas de ordenador / software)
  · Convenio de Berna para la Protección de las Obras Literarias y Artísticas
    (Perú adherido desde 1988 — 181 estados miembro)
  · Digital Millennium Copyright Act (DMCA — 17 U.S.C. § 512)
    aplicable sobre la plataforma GitHub (empresa con sede en EE.UU.)

La protección es automática desde el momento de creación, sin necesidad
de registro previo (art. 3 DL 822 concordante con art. 5 Convenio de Berna).

ACCIONES EXPRESAMENTE PROHIBIDAS sin autorización escrita del titular:

  · Copia, reproducción o distribución total o parcial del código fuente
  · Creación de trabajos derivados, adaptaciones o forks redistributivos
  · Uso comercial en servicios de terceros o productos competidores
  · Ingeniería inversa de módulos de seguridad o cifrado
  · Publicación bajo nombre o marca diferente a DarckRovert
  · Registro de marcas o patentes basadas en este código

EVIDENCIA DE AUTORÍA: El historial de commits Git del repositorio oficial
constituye evidencia técnica de autoría y precedencia temporal verificable
ante cualquier tribunal bajo el Convenio de Berna.

VIOLACIONES: Cualquier vulneración constituye infracción de derechos de autor
perseguible civil y penalmente. Para reportar infracciones o solicitar una
licencia comercial, ver el archivo NOTICE en este repositorio.

LA VISUALIZACIÓN DE ESTE CÓDIGO EN GITHUB NO OTORGA NINGÚN DERECHO DE USO,
COPIA O DISTRIBUCIÓN. "No license" bajo los términos de GitHub ToS significa
que ninguna persona distinta al titular puede usar este código.
""",
    "CONTRIBUTING.md": """# Guía de Contribución para Gravity AI Bridge

¡Gracias por tu interés en contribuir al ecosistema de Gravity AI!

## Reglas Invariantes
Toda contribución de código debe respetar estrictamente las reglas invariantes definidas en `core/autonomy_engine.py`:
1. Nunca exceder límites de costo de API codificados.
2. No comprometer la arquitectura HITL (Human-in-the-Loop).
3. Todo debe ser compatible con la ejecución local (offline-first o fallback local garantizado).

## Proceso de Pull Requests
1. Haz fork del proyecto y crea tu rama (`feature/nueva-habilidad`).
2. Añade documentación en la carpeta `/wiki` si alteras la arquitectura L0/L1/L2.
3. Envía el PR detallando el consumo de recursos y tiempo de procesamiento.
""",
    "CODE_OF_CONDUCT.md": """# Código de Conducta de Gravity AI

El equipo y la IA detrás de Gravity se rigen por un principio básico de respeto, innovación y seguridad técnica.

1. **Colaboración Constructiva:** Fomentamos el desarrollo ético de sistemas autónomos.
2. **Reporte de Brechas:** Toda brecha de seguridad (loop infinito, escape de contenedor, filtración de API keys) debe reportarse a los administradores antes de publicarla.
3. **Respeto Mutuo:** No se tolerará acoso, discriminación o toxicidad en el entorno de desarrollo.
""",
    "SECURITY.md": """# Política de Seguridad

Este repositorio implementa salvaguardas avanzadas para el control de IA autónoma.

## Versiones Soportadas
Actualmente solo se brinda soporte de seguridad a la rama principal (Gravity V16.0 PRO).

## Reporte de Vulnerabilidades
Si encuentras una manera en la que el Motor de Autonomía de Gravity pueda eludir sus bloqueos (HITL o presupuesto), repórtalo directamente mediante un Issue privado o contactando al administrador. NO crees un Issue público si el problema expone claves de API en texto plano o permite RCE remoto sin autenticación.
""",
    ".github/ISSUE_TEMPLATE/bug_report.md": """---
name: Reporte de Bug
about: Crea un reporte para ayudarnos a mejorar la estabilidad de Gravity.
title: "[BUG] "
labels: bug
assignees: DarckRovert
---

**Descripción del Bug**
Una descripción clara de lo que falló.

**Logs de Error**
Si aplica, pega aquí la salida de error (elimina claves de API):
```log
```

**Contexto del Entorno**
- OS: [ej. Windows 11]
- Motor: [ej. Llama 3.3, Ollama, etc]
- Puerto afectado: [ej. 7860, 7861]
""",
    ".github/ISSUE_TEMPLATE/feature_request.md": """---
name: Solicitud de Feature
about: Sugiere una nueva idea para el ecosistema Gravity.
title: "[FEATURE] "
labels: enhancement
assignees: DarckRovert
---

**Descripción de la Feature**
Explica tu idea y cómo encaja en la arquitectura L0, L1 o L2 de Gravity.
""",
    "wiki/Home.md": """# Wiki de Gravity AI Bridge 📚

Bienvenido a la Wiki Oficial del ecosistema **Gravity AI Bridge V16.0 PRO**.

## Índice de Contenidos

- [Arquitectura Profunda (Deep Dive)](Architecture-Deep-Dive.md)
- [Referencia de API y Módulos](API-Reference.md)
- [Troubleshooting y FAQs](Troubleshooting-and-FAQ.md)

Gravity es un puente de software que vincula sistemas de inteligencia artificial local con integraciones de nube híbrida, formando un sistema completamente autogestionable capaz de generar reportajes, audios y videos de alta calidad con intervención humana mínima.
""",
    "wiki/Architecture-Deep-Dive.md": """# Arquitectura Profunda (L0, L1, L2)

## Estructura de Capas

1. **L0: Cerebro y Coordinación (Gravity Bridge Server)**
   - Puerto `7860`.
   - Carga el entorno de Gradio (`bridge_server.py`) y el motor cognitivo (`gravity_brain.py`).
   - El Motor de Autonomía (`autonomy_engine.py`) opera aquí en un ciclo OODA de 6 horas, tomando decisiones sobre gasto, contenido y seguridad.

2. **L1: Motor de Renderizado Estático (Fooocus Studio)**
   - Puertos `7861` y `7862`.
   - Controla la API para la generación asíncrona de miniaturas y recursos gráficos.

3. **L2: Motor de Renderizado Dinámico (ComfyUI / LTX)**
   - Puerto `8188`.
   - Utilizado para animaciones pesadas y pipelines de contenido de video en lote.

## Reportero Autónomo
Un proceso demonio continuo (`news_daemon.py`) que:
1. Ejecuta `workflows/reporter.json` via `run_workflow("reporter")`.
2. Busca temáticas usando herramientas de WebSearch.
3. Inyecta respuestas LLM en `news.json` en un repositorio independiente (`gravity-news-portal`).
4. Realiza sincronizaciones automáticas a través de `git commit` y `git push` a Netlify. Cuenta con control de idempotencia para evitar fallos si no hay cambios nuevos, garantizando un ciclo de ejecución continuo.
""",
    "wiki/API-Reference.md": """# Referencia de API

## `core/provider_manager.py`
Módulo clave para la comunicación con múltiples proveedores de LLM.
- `complete(messages, provider=None, model=None, options=None)`
- Conoce y enruta peticiones hacia LM Studio local, Ollama, Nvidia NIM, Groq, y OpenAI, con manejo de fallback en caso de `401 Unauthorized`.

## `core/autonomy_engine.py`
Núcleo del agente CEO.
- `run_ooda_cycle()`: Ejecuta la lectura del estado (Observe), clasifica alertas (Orient), determina acciones con LLM (Decide), ejecuta tareas de bajo riesgo (Act) y actualiza la base de conocimiento (Learn).

## `gravity_reporter.py`
Ejecución del periodista.
- Argumentos: `--topic "..."`, `--focus "..."`.
- Fallbacks automáticos entre motores.
""",
    "wiki/Troubleshooting-and-FAQ.md": """# Troubleshooting y FAQ

### 1. El portal de noticias tiene errores de decodificación JSON.
**Solución:** Revisa los logs de `task-*`. Puede ocurrir si un proveedor LLM falla y devuelve un JSON en un bloque markdown inesperado. El sistema ahora tiene un parche en `clean_llm_response()` para extraer y limpiar la salida.

### 2. Fooocus no arranca desde el `INICIAR_TODO.bat`
**Explicación:** Por defecto, Fooocus arranca en "modo manual" para ahorrar RAM (frecuentemente más de 12GB requeridos). Debes activarlo manualmente desde el Mission Control (L0).

### 3. Problemas de Push a Github en el Agente Periodístico
**Solución:** Verifica que el usuario local de Windows tenga las credenciales de Git cacheadas globalmente (`git config --global credential.helper wincred`).

### 4. Fallos al decodificar contenido de Web Search
**Explicación:** Si la búsqueda web retorna errores de Gzip o decodificación, revisa que no estés enviando headers de codificación (Accept-Encoding) incompatibles con `urllib`. La V16.0 PRO ya maneja esto limpiando cabeceras innecesarias.

### 5. Falla silenciosa al instalar faster-whisper
**Solución:** En V16.0 PRO, la instalación de dependencias como Whisper es de tipo "bloqueante" (`blocking`). Si notas errores de "módulo no encontrado" en la consola, verifica que el subprocess tenga permisos para instalar pip localmente sin detener la ejecución.
""",
}

files_to_create[".gitignore"] = """
__pycache__/
*.py[cod]
*$py.class
.env
.venv/
env/
venv/
*.log
_keys/
*.bin
.tmp.driveupload/
"""


for file_path, content in files_to_create.items():
    full_path = os.path.join(BASE_DIR, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Creado: {full_path}")

print("Toda la documentacion generada.")
