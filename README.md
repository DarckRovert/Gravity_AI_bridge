# Gravity AI Bridge V9.0 PRO [Diamond-Tier Edition] 🌐

[![Versión](https://img.shields.io/badge/Versión-9.0_PRO-4f46e5.svg)](CHANGELOG.md)
[![Licencia: PolyForm Non-Commercial 1.0.0](https://img.shields.io/badge/Licencia-PolyForm_NC-22c55e.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![DarckRovert](https://img.shields.io/badge/Desarrollado_por-DarckRovert-7c3aed.svg)](https://twitch.tv/darckrovert)
[![GitHub](https://img.shields.io/badge/GitHub-DarckRovert-181717.svg)](https://github.com/DarckRovert)

> **El puente de IA más avanzado para uso local y cloud**, con arquitectura Omni-Tier, enrutamiento dinámico por latencia, interfaz de línea de comandos premium, MCP, RAG híbrido, auditoría de código adversarial y dashboard web interactivo. Comparable y superior en funcionalidades a herramientas como Claude Code, Aider y Continue.

---

## ✨ Características Principales

| Categoría | Funcionalidad |
|-----------|--------------|
| 🔌 **Local** | Ollama · LM Studio · vLLM · KoboldCPP · Jan AI · Lemonade |
| ☁️ **Cloud** | OpenAI · Anthropic · Google Gemini · Groq · Cohere · AWS |
| 🧠 **Enrutamiento** | Dinámico por latencia TTFT + especialización de tareas |
| 🛡️ **Seguridad** | API Keys cifradas DPAPI · Rate Limiting · Audit Log inmutable |
| 📡 **Observabilidad** | Dashboard SPA · Prometheus `/metrics` · Streaming SSE |
| 🔬 **RAG** | Embeddings NPU/GPU/CPU · BM25 + vectorial · PDFs |
| 🤖 **MCP** | Model Context Protocol · Herramientas externas stdio |
| 🔍 **Verificación** | VerificationAgent adversarial antes de cada cambio |
| 💻 **CLI** | 20+ comandos · Sesiones · Branches · Export MD/HTML |
| ⚡ **Cache** | SQLite WAL · Hash-aware reasoning · TTL configurable |

---

## 🚀 Instalación Rápida

### Opción A — Instalador TUI interactivo (recomendado)
```cmd
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge
INSTALAR.bat
```
El instalador detecta automáticamente tu hardware, motores de IA locales, configura el modelo óptimo, registra el comando `gravity` en tu PATH y crea un acceso directo en el Escritorio.

### Opción B — Instalación manual
```cmd
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge
pip install -r requirements.txt
python bridge_server.py
```

---

## 💻 Uso del CLI

```cmd
# Modo interactivo con onboarding
gravity

# Pregunta directa desde terminal
gravity "explica la arquitectura de este proyecto"

# Comandos especiales
gravity --server      # Iniciar bridge server
gravity --status      # Estado de todos los motores
gravity --install     # Lanzar instalador TUI
gravity --help        # Ayuda rápida
```

### Comandos del Auditor (dentro del CLI)

| Comando | Descripción |
|---------|-------------|
| `/help` | Lista todos los comandos |
| `/model` | Cambiar motor/modelo activo |
| `/mode` | Cambiar modo: production / development / Omni-Audit |
| `/providers` | Estado real-time de todos los backends |
| `/keys set \|list\|del` | Gestión de API Keys cifradas |
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
| `/export` | Exportar sesión a HTML |
| `/clear` | Limpiar contexto |
| `!aprende <texto>` | Persiste una regla en el knowledge base |
| `/exit` | Salir limpiamente |

---

## 🌐 Integración con IDEs

Configura **Cursor, VS Code (Continue), Aider, OpenWebUI** con:

```
Base URL: http://localhost:7860/v1
API Key:  gravity-local
Modelo:   gravity-bridge-auto
```

### Archivos de configuración incluidos
- `.continue/config.json` — Continue.dev
- `aider.conf.yml` — Aider CLI
- `.vscode/settings.json` — VS Code

---

## 🖥️ Dashboard Web

Accede al dashboard interactivo en `http://localhost:7860` tras iniciar el servidor:

- **Chat en tiempo real** con streaming y renderizado Markdown
- **Estado de proveedores** con latencia en vivo
- **Audit Log** con tokens, costes y latencia por llamada
- **Configuración** de API Keys directamente desde el browser

---

## 📊 API Compatible OpenAI

El bridge expone una API 100% compatible con el protocolo OpenAI:

```bash
# Chat Completions
POST http://localhost:7860/v1/chat/completions

# Modelos disponibles
GET http://localhost:7860/v1/models

# Estado del sistema
GET http://localhost:7860/v1/status

# Audit Log JSON
GET http://localhost:7860/v1/audit

# Métricas Prometheus
GET http://localhost:7860/metrics
```

---

## 📁 Estructura del Proyecto

```
Gravity_AI_bridge/
├── ask_deepseek.py        ← CLI principal (Auditor Senior)
├── bridge_server.py       ← Servidor HTTP OpenAI-compatible
├── dashboard.py           ← Dashboard SPA Web interactivo
├── INSTALAR.py            ← Instalador TUI premium
├── gravity.bat            ← Comando global 'gravity'
├── core/                  ← Módulos de infraestructura
│   ├── config_manager.py  ← YAML config + migración
│   ├── audit_log.py       ← Audit log JSONL inmutable
│   ├── metrics.py         ← Prometheus metrics
│   ├── rate_limiter.py    ← Rate limiting por IP/Key
│   ├── mcp_adapter.py     ← Adaptador MCP (stdio)
│   └── verification_agent.py ← Auditoría adversarial
├── providers/             ← Plugins de proveedores
├── rag/                   ← Motor RAG híbrido
├── tools/                 ← Herramientas del agente
├── wiki/                  ← Documentación técnica detallada
└── config.yaml            ← Configuración principal
```

---

## 🤖 Orquestación de Agentes (AI-to-AI)

Gravity AI Bridge permite que otros asistentes de IA (como Antigravity, Claude o agentes de Cursor) se sincronicen con el repositorio local. 

Para habilitar la orquestación automática, copia el archivo de ejemplo en la raíz de tu proyecto:
```cmd
cp F:\Gravity_AI_bridge\.antigravityrules.example .antigravityrules
```
Esto permitirá que cualquier agente lea las reglas de este proyecto, sepa dónde está el Bridge y use automáticamente sus herramientas de auditoría y conocimiento persistente.

---

## 🛠️ Requisitos del Sistema

- **Python** 3.10 o superior
- **Sistema Operativo**: Windows 10/11, Linux, macOS
- **Motor de IA**: **Requerido** (Local: Ollama/LM Studio -o- Cloud: OpenAI/Anthropic/Groq)
- **RAM mínima**: 8 GB (Recomendado 16 GB+)
- **GPU**: Recomendada para modelos locales (NVIDIA 8GB+ VRAM), no necesaria para Cloud.

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

Lee [CONTRIBUTING.md](CONTRIBUTING.md) para las guías de contribución.  
Revisa el [Código de Conducta](CODE_OF_CONDUCT.md) antes de abrir un issue.  
Para vulnerabilidades de seguridad, consulta [SECURITY.md](SECURITY.md).

---

## 📜 Licencia

Distribuido bajo la **Licencia PolyForm Non-Commercial 1.0.0** (2026). Ver [LICENSE](LICENSE) para detalles.

---

<div align="center">

Desarrollado con ❤️ por **DarckRovert**

[![Twitch](https://img.shields.io/badge/Twitch-darckrovert-9146FF?logo=twitch)](https://twitch.tv/darckrovert)
[![GitHub](https://img.shields.io/badge/GitHub-DarckRovert-181717?logo=github)](https://github.com/DarckRovert)

*Gravity AI Bridge — Orquestando la inteligencia local y cloud.*

</div>
