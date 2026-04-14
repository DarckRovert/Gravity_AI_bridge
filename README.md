# Gravity AI Bridge V9.3.1 PRO [Diamond-Tier Edition] 🌐

[![Versión](https://img.shields.io/badge/Versión-9.3.1_PRO-4f46e5.svg)](CHANGELOG.md)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-22c55e.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![DarckRovert](https://img.shields.io/badge/Desarrollado_por-DarckRovert-7c3aed.svg)](https://twitch.tv/darckrovert)
[![GitHub](https://img.shields.io/badge/GitHub-DarckRovert-181717.svg)](https://github.com/DarckRovert)

> **El puente de IA más avanzado para uso local y cloud**, con arquitectura Omni-Tier, enrutamiento dinámico por latencia, interfaz de línea de comandos premium, MCP, RAG híbrido, auditoría de código adversarial, Dashboard Web SPA y generación de imágenes via Fooocus CPU.

---

## ✨ Características Principales

| Categoría | Funcionalidad |
|-----------|--------------|
| 🔌 **Local** | Ollama · LM Studio · vLLM · KoboldCPP · Jan AI · Lemonade |
| ☁️ **Cloud** | OpenAI · Anthropic · Google Gemini · Groq · Cohere |
| 🧠 **Enrutamiento** | Dinámico por latencia TTFT + especialización de tareas |
| 🛡️ **Seguridad** | API Keys cifradas DPAPI · Rate Limiting · Audit Log inmutable |
| 📡 **Observabilidad** | Dashboard SPA V9.3.1 · Prometheus `/metrics` · Streaming SSE |
| 🎨 **Visión** | Fooocus CPU mode · Vision Studio UI · JuggernautXL SDXL |
| 🔬 **RAG** | Embeddings CPU/ONNX · BM25 + vectorial · PDFs |
| 🤖 **MCP** | Model Context Protocol · Herramientas externas stdio |
| 🔍 **Verificación** | VerificationAgent adversarial antes de cada cambio |
| 💻 **CLI** | 20+ comandos · Sesiones · Branches · Export MD/HTML |
| ⚡ **Cache** | SQLite WAL · Hash-aware reasoning · TTL configurable |

---

## 🚀 Instalación Rápida

### Requisito previo para generación de imágenes (AMD GPU)
Si usas una GPU AMD (Radeon 780M / RX series), instala el runtime HIP:
```
AMD-Software-PRO-Edition-26.Q1-Win11-For-HIP.exe
```
Disponible en [amd.com/en/support](https://www.amd.com/en/support). Reinicia Windows tras instalar.

### Opción A — Instalador TUI interactivo (recomendado)
```cmd
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge
launchers\INSTALAR.bat
```

### Opción B — Instalación manual
```cmd
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge
pip install -r requirements.txt
python bridge_server.py
```

---

## ▶️ Cómo Usar

### Flujo normal (recomendado)

Abre **un solo archivo** para arrancar todo el ecosistema:
```
launchers\INICIAR_TODO.bat
```
Esto levanta automáticamente:
1. Bridge Server + Dashboard Web (puerto 7860)
2. Motor Fooocus modo CPU (API imágenes, puerto 7861)
3. Vision Studio UI (interfaz de imágenes, puerto 7862)

### Launchers disponibles en `launchers\`

| Archivo | Función |
|---------|---------|
| `INICIAR_TODO.bat` ⭐ | **Arranque completo** — uso diario |
| `INICIAR_SERVIDOR.bat` | Solo Bridge Server + Dashboard (`localhost:7860`) |
| `GRAVITY_VISION_PRO.bat` | Arranca todo el Ecosistema Visión independiente |
| `INICIAR_AUDITOR.bat` | Solo CLI de terminal |
| `INSTALAR.bat` | Instalador TUI |
| `DESINSTALAR.bat` | Desinstalador |
| `Deploy_GravityBridge.bat` | Sync a GitHub |
| `MODO_FANTASMA.vbs` | Auditor sin ventana |

---

## 💻 Uso del CLI

```cmd
gravity                              # Modo interactivo
gravity "explica esta función"       # Pregunta directa
gravity --server                     # Iniciar bridge server
gravity --status                     # Estado de todos los motores
gravity --install                    # Lanzar instalador TUI
```

### Comandos del Auditor

| Comando | Descripción |
|---------|-------------|
| `/help` | Lista todos los comandos |
| `/model` | Cambiar motor/modelo activo |
| `/mode` | Cambiar modo: production / development / Omni-Audit |
| `/providers` | Estado real-time de todos los backends |
| `/keys set\|list\|del` | Gestión de API Keys cifradas |
| `/search <query>` | Búsqueda web inyectada como contexto |
| `/rag <query>` | Búsqueda en índice local de documentos |
| `/index <ruta>` | Indexar archivos/carpetas al RAG |
| `/verify <archivo>` | Auditar código con VerificationAgent |
| `/plan <tarea>` | Modo planificación antes de codificar |
| `/mcp <ruta>` | Conectar servidor MCP externo |
| `/save [nombre]` | Guardar sesión actual |
| `/load <nombre>` | Cargar sesión guardada |
| `/sessions` | Listar todas las sesiones |
| `/cost` | Desglose de costes por modelo |
| `/branch <nombre>` | Fork de la sesión actual |
| `/export md` | Exportar sesión a Markdown |
| `/clear` | Limpiar contexto |
| `!aprende <texto>` | Persiste una regla en el knowledge base |
| `/exit` | Salir limpiamente |

---

## 🌐 Dashboard Web — `localhost:7860`

Accede tras ejecutar `INICIAR_SERVIDOR.bat` o `INICIAR_TODO.bat`:

- **💬 Chat** — Chat en tiempo real con streaming y renderizado Markdown
- **📡 Status** — Estado de proveedores con latencia en vivo y gráfica RTO
- **🎨 Vision Studio** — iFrame integrado del Fooocus Studio + galería de imágenes generadas
- **📋 Audit Log** — Historial de inferencias con tokens, coste y latencia
- **⚙️ Configuración** — Gestión de API Keys directamente desde el browser

---

## 🎨 Generación de Imágenes (Vision Studio)

Arquitectura de dos capas unificadas en CPU:

```
Vision Studio UI (7862) ──→ fooocus_client.py ──→ Fooocus API (7861)
         ↑                                                    ↓
  Interfaz Gradio                                   Ryzen 7 8700G (CPU/fp32)
  (Prompt, Aspect Ratio,                            JuggernautXL SDXL
   Performance, Styles)                             Output → /outputs/
```

**Generación CPU-safe:** El modo CPU previene crashes de DirectML. Espera 60-90 segundos para inicialización del motor, luego las generaciones toman entre 3 a 8 minutos.

---

## 📊 API Compatible OpenAI

```bash
POST http://localhost:7860/v1/chat/completions    # Chat con streaming
GET  http://localhost:7860/v1/models              # Modelos disponibles
GET  http://localhost:7860/v1/status              # Estado del sistema
GET  http://localhost:7860/v1/audit               # Audit Log JSON
GET  http://localhost:7860/v1/images              # Imágenes generadas
GET  http://localhost:7860/metrics                # Métricas Prometheus
```

---

## 📁 Estructura del Proyecto

```
Gravity_AI_bridge/
├── launchers/             ← Todos los scripts de arranque
│   ├── INICIAR_TODO.bat   ← Arranque completo (recomendado)
│   ├── INICIAR_SERVIDOR.bat
│   ├── GRAVITY_VISION_PRO.bat
│   ├── INICIAR_AUDITOR.bat
│   ├── INSTALAR.bat
│   ├── DESINSTALAR.bat
│   ├── Deploy_GravityBridge.bat
│   └── MODO_FANTASMA.vbs
├── core/                  ← Módulos de infraestructura (22 módulos)
├── providers/             ← Plugins de proveedores IA
├── tools/                 ← Herramientas del agente + Vision Studio
│   ├── fooocus_client.py  ← Cliente Fooocus HTTP Bridge
│   └── fooocus_studio_ui.py ← Interfaz Gradio de generación
├── web/dashboard.html     ← SPA Dashboard V9.3.1 PRO
├── rag/                   ← Motor RAG híbrido
├── wiki/                  ← Documentación técnica detallada
├── ask_deepseek.py        ← CLI principal (Auditor Senior)
├── bridge_server.py       ← Servidor HTTP OpenAI-compatible
├── dashboard.py           ← Servidor del Dashboard SPA
├── health_check.py        ← Herramienta de diagnóstico
├── INSTALAR.py            ← Instalador TUI premium
├── gravity.bat            ← Comando global 'gravity'
└── config.yaml            ← Configuración principal
```

---

## 🛠️ Requisitos del Sistema

| Componente | Mínimo | Recomendado |
|-----------|--------|-------------|
| Python | 3.10 | 3.11+ |
| RAM | 8 GB | 16 GB+ |
| OS | Windows 10 | Windows 11 |
| Motor IA | LM Studio / Ollama | LM Studio (activo en tu sistema) |
| CPU solamente | Ollama (CPU) | Fooocus (CPU --all-in-fp32) |
| AMD GPU / iGPU | LM Studio / Ollama | Fooocus (CPU --all-in-fp32) |

---

## 🌐 Integración con IDEs

```
Base URL: http://localhost:7860/v1
API Key:  gravity-local
Modelo:   gravity-bridge-auto
```

Archivos de configuración incluidos:
- `.continue/config.json` — Continue.dev
- `.vscode/settings.json` — VS Code

---

## 📖 Documentación Completa

| Documento | Descripción |
|-----------|-------------|
| [Arquitectura](wiki/Arquitectura.md) | Diagrama y decisiones de diseño |
| [Guía de API](wiki/Guia_API.md) | Referencia completa de endpoints |
| [Manual de Usuario](wiki/Manual_Usuario.md) | Tutorial paso a paso |
| [FAQ](wiki/FAQ.md) | Preguntas frecuentes |

---

## 🤝 Contribuir

Lee [CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) · [SECURITY.md](SECURITY.md)

---

## 📜 Licencia

Distribuido bajo la **Licencia MIT** (2026). Ver [LICENSE](LICENSE) para detalles.

---

<div align="center">

Desarrollado con ❤️ por **DarckRovert**

[![Twitch](https://img.shields.io/badge/Twitch-darckrovert-9146FF?logo=twitch)](https://twitch.tv/darckrovert)
[![GitHub](https://img.shields.io/badge/GitHub-DarckRovert-181717?logo=github)](https://github.com/DarckRovert)

*Gravity AI Bridge — Orquestando la inteligencia local y cloud.*

</div>
