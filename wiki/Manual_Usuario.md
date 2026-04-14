# Manual de Usuario — Gravity AI Bridge V9.1 PRO [Diamond-Tier Edition]

## Índice

1. [Instalación](#1-instalación)
2. [Primer Arranque](#2-primer-arranque)
3. [Launchers — Cómo Arrancar el Sistema](#3-launchers--cómo-arrancar-el-sistema)
4. [Dashboard Web](#4-dashboard-web)
5. [Uso del CLI](#5-uso-del-cli)
6. [Gestión de API Keys](#6-gestión-de-api-keys)
7. [Generación de Imágenes (Vision Studio)](#7-generación-de-imágenes-vision-studio)
8. [Sistema RAG](#8-sistema-rag)
9. [Verificación de Código](#9-verificación-de-código)
10. [MCP — Herramientas Externas](#10-mcp--herramientas-externas)
11. [Sesiones](#11-sesiones)
12. [Integración con IDEs](#12-integración-con-ides)
13. [Atajos y Tips](#13-atajos-y-tips)
14. [Orquestación de Agentes (AI-to-AI)](#14-orquestación-de-agentes-ai-to-ai)

---

## 1. Instalación

### Requisitos previos

**Motor de IA (obligatorio uno):**
- [LM Studio](https://lmstudio.ai) — recomendado (activo en tu sistema actualmente)
- [Ollama](https://ollama.ai) — alternativa open source

**Para generación de imágenes (AMD GPU):**
1. Descarga `AMD-Software-PRO-Edition-26.Q1-Win11-For-HIP.exe` de [amd.com/en/support](https://www.amd.com/en/support)
2. Instala como Administrador
3. **Reinicia Windows** (obligatorio para que `amdhip64.dll` quede disponible)

### Instalación del Bridge

```cmd
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge
launchers\INSTALAR.bat
```

El instalador detecta tu hardware, configura el modelo óptimo y registra el comando `gravity` en tu PATH.

---

## 2. Primer Arranque

La primera vez que ejecutes `gravity`, aparecerá el wizard de bienvenida:

```
⚡ GRAVITY AI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Bienvenido a Gravity AI Bridge V9.1 PRO [Diamond-Tier Edition]
Primera ejecución detectada. Configuración inicial.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Motores locales detectados: LM Studio

┌─ Comandos esenciales ─────────────────────┐
│ /help    Lista todos los comandos          │
│ /model   Cambiar motor o modelo activo     │
│ /keys    Configurar API Keys               │
└───────────────────────────────────────────┘

  Presiona ENTER para iniciar...
```

---

## 3. Launchers — Cómo Arrancar el Sistema

Todos los launchers están en la carpeta `launchers\`. **No hay duplicados en la raíz.**

### Para uso diario (recomendado)

Doble click en:
```
launchers\INICIAR_TODO.bat
```

Este archivo hace automáticamente:
1. Libera los puertos 7860 y 7861 si quedaron ocupados
2. Verifica si Fooocus CPU ya corre (no lo reinicia si ya está activo)
3. Arranca el Bridge Server en `http://localhost:7860`
4. Arranca Fooocus Studio en `http://127.0.0.1:7861`

### Launchers individuales

| Archivo | Puerto | Cuándo usarlo |
|---------|--------|---------------|
| `INICIAR_TODO.bat` ⭐ | 7860 + 7861 + 8188 | Uso normal diario |
| `INICIAR_SERVIDOR.bat` | 7860 | Solo chat/dashboard, sin imágenes |
| `GRAVITY_VISION_PRO.bat` | 7861 + 8188 | Solo generación de imágenes |
| `INICIAR_AUDITOR.bat` | — | Solo CLI de terminal |
| `INSTALAR.bat` | — | Primera instalación o reinstalación |
| `DESINSTALAR.bat` | — | Limpiar el sistema |
| `Deploy_GravityBridge.bat` | — | Sincronizar con GitHub |
| `MODO_FANTASMA.vbs` | — | Auditor sin ventana visible |

---

## 4. Dashboard Web

Accede a `http://localhost:7860` tras ejecutar `INICIAR_SERVIDOR.bat` o `INICIAR_TODO.bat`.

### Pestañas disponibles

**💬 Chat**
- Chat en tiempo real con streaming y renderizado Markdown.
- Accesos rápidos a comandos frecuentes (`/search`, `/verify`, `!aprende`, `/cost`).
- Historial de conversación en sesión.

**📡 System Status**
- Estado de todos los backends con latencia en tiempo real.
- Gráfica RTO de latencia de los últimos 60 segundos.
- Tabla completa de proveedores con ping y modelos disponibles.
- Se actualiza automáticamente cada 10 segundos.

**🎨 Vision Studio**
- iFrame integrado del Fooocus Studio (puerto 7861).
- Panel lateral con estado del motor Fooocus CPU.
- Galería de las últimas imágenes generadas (polling cada 5s).

**📋 Audit Log**
- Historial de las últimas 20 inferencias con tokens, latencia y coste.
- Exportación en JSONL desde el botón "Exportar JSONL".

**⚙️ Configuración**
- Gestión de API Keys directamente desde el browser (cifrado DPAPI).
- Links directos a endpoints de observabilidad.

---

## 5. Uso del CLI

### Modo Interactivo
```cmd
gravity
```

### Modo Pipe (para scripts)
```cmd
gravity "explica este error: AttributeError: module has no attribute X"
cat error.log | gravity "analiza este log"
```

### Comandos Esenciales

#### Cambiar modelo
```
Gravity> /model
  [0] LM Studio (3 modelos)
  [1] Ollama (0 modelos)
  [A] Automático
Selección: 0
  [0] google/gemma-4-e2b
  [1] deepseek-r1:14b
Selecciona modelo: 0
✓ Forzado a LM Studio → google/gemma-4-e2b
```

#### Cambiar modo de operación
```
Gravity> /mode
  [0] production   — Respuestas directas
  [1] development  — Debug verbose
  [2] Omni-Audit   — Análisis profundo zero-trust
Selecciona modo: 2
✓ Modo cambiado a Omni-Audit
```

#### Ver estado de proveedores
```
Gravity> /providers
┌──────────────────────────────────────────────┐
│ Proveedor  │ Cat.  │ Latencia │ Modelos │Estado│
│ LM Studio  │ LOCAL │  817ms   │    3    │ONLINE│
│ Ollama     │ LOCAL │ 1814ms   │    0    │OFFLIN│
└──────────────────────────────────────────────┘
```

#### Búsqueda web con contexto
```
Gravity> /search últimos modelos de Mistral AI
→ [Buscando en DuckDuckGo...]
→ Contexto web inyectado al próximo mensaje.
```

#### Planificación antes de codificar
```
Gravity> /plan refactorizar el sistema de caché para usar Redis
→ Modo Planificación Activado
```

---

## 6. Gestión de API Keys

### Desde el CLI
```
Gravity> /keys list
Gravity> /keys set openai
API Key para openai: ****
Gravity> /keys del openai
```

### Desde el Dashboard Web
1. Ve a la pestaña **⚙️ Configuración**.
2. Escribe el nombre del proveedor (`openai`, `anthropic`, etc.).
3. Pega tu API Key.
4. Haz clic en **Guardar en Bóveda**.

### Proveedores soportados

| ID | Nombre | URL |
|----|--------|-----|
| `openai` | OpenAI | platform.openai.com |
| `anthropic` | Anthropic | console.anthropic.com |
| `google` | Google Gemini | aistudio.google.com |
| `groq` | Groq | console.groq.com |
| `cohere` | Cohere | dashboard.cohere.com |
| `brave_search` | Brave Search (web) | api.search.brave.com |

---

## 7. Generación de Imágenes (Vision Studio)

### Requisito: AMD HIP SDK

La generación de imágenes requiere `amdhip64.dll` en el sistema:
1. Instala `AMD-Software-PRO-Edition-26.Q1-Win11-For-HIP.exe`
2. Reinicia Windows
3. La variable `HIP_PATH` se configurará automáticamente

### Arrancar el Studio

```
launchers\GRAVITY_VISION_PRO.bat
```

O usa `INICIAR_TODO.bat` para arrancarlo junto con todo lo demás.

### Generar una imagen

1. Abre `http://127.0.0.1:7861` (se abre automáticamente)
2. Escribe tu prompt en el campo inferior
3. Ajusta los parámetros en el panel derecho (Settings / Styles / Models / Advanced)
4. Haz clic en **Generate**
5. **⚠️ Primera vez:** ZLUDA compila los kernels de AMD. Espera **3-5 minutos sin presionar nada más**
6. La imagen aparecerá automáticamente al completarse

### Parámetros disponibles

| Parámetro | Opciones | Default |
|-----------|----------|---------|
| Performance | Quality, Speed, Lightning, Hyper-SD | Quality |
| Aspect Ratio | 1:1, 9:7, 7:9, 19:13, 7:4, 12:5 y más | 9:7 (1152x896) |
| Image Number | 1-4 | 1 |
| Output Format | png, jpeg, webp | png |
| Styles | Fooocus V2, Enhance, Sharp | V2 + Enhance |
| CFG Scale | 1.0-30.0 | 7.0 |
| Steps | 10-60 | 30 |
| Sampler | dpmpp_2m | dpmpp_2m |
| Scheduler | karras | karras |

### Ver imágenes generadas

Las imágenes aparecen automáticamente en la **galería del Dashboard Web** (`localhost:7860` → pestaña Vision Studio).

---

## 8. Sistema RAG

### Indexar documentos
```
Gravity> /index F:\proyecto\main.py
Gravity> /index F:\proyecto\src

✓ Indexación completa. (142 chunks añadidos)
```

### Buscar en el índice
```
Gravity> /rag función de autenticación JWT

Fragmento 1 (similitud 0.94) - F:\proyecto\auth.py
def verify_jwt_token(token: str) -> dict:
    ...
```

### Inyección automática
Cuando tu mensaje contiene "busca en mi código", "del contexto" o "en mi código", el RAG inyecta automáticamente los fragmentos más relevantes.

---

## 9. Verificación de Código

```
Gravity> /verify F:\proyecto\api.py

Resultado de Verificación: Score 85/100

  [INFO] Cambio masivo detectado (+5200 caracteres).
  ✓ Sin hallazgos de seguridad.
```

El VerificationAgent detecta:
- Patrones de riesgo: `os.remove`, `subprocess shell=True`, `eval()`.
- Errores de sintaxis Python/JSON/Lua.
- Cambios masivos no intencionados.

---

## 10. MCP — Herramientas Externas

```
Gravity> /mcp C:\ruta\mcp-git\server.py

Conectando con servidor MCP...
✓ Conectado. 4 herramientas disponibles:
  git_status    — Current repository status
  git_log       — Recent commits
  git_diff      — Show changes
  git_commit    — Create a commit

MCP> git_status
{"result": {"output": "M  src/main.py\n?? tests/"}}

MCP> /mcp-exit
Sesión MCP cerrada.
```

---

## 11. Sesiones

```
Gravity> /save revision-api-jwt
Gravity> /sessions
Gravity> /load revision-api-jwt
✓ Sesión cargada. (24 mensajes)
Gravity> /branch alternativa
✓ Fork creado: alternativa
Gravity> /export md
✓ Markdown exportado.
```

---

## 12. Integración con IDEs

### Cursor
En `Settings → AI → OpenAI API`:
- Base URL: `http://localhost:7860/v1`
- API Key: `gravity-local`
- Model: `gravity-bridge-auto`

### VS Code + Continue
Edita `~/.continue/config.json`:
```json
{
  "models": [{
    "title": "Gravity AI",
    "provider": "openai",
    "model": "gravity-bridge-auto",
    "apiBase": "http://localhost:7860/v1",
    "apiKey": "gravity-local"
  }]
}
```

---

## 13. Atajos y Tips

| Tip | Descripción |
|-----|-------------|
| `!aprende <regla>` | Persiste una regla permanente al sistema |
| `gravity --status` | Ver estado de todos los motores sin entrar al CLI |
| `Ctrl+C` dentro del CLI | No cierra — escribe `/exit` para salir |
| Cache automático | Respuestas idénticas cacheadas 24h en SQLite WAL |
| Sliding Window | El contexto se recorta al superar 128k tokens |
| Bridge Server previo al Studio | `INICIAR_TODO.bat` garantiza el orden correcto de arranque |
| Puerto ocupado | El launcher mata automáticamente procesos en 7860/7861 antes de arrancar |

---

## 14. Orquestación de Agentes (AI-to-AI)

Gravity AI Bridge permite que asistentes externos (Antigravity, Claude, agentes de Cursor) se conecten automáticamente al Bridge.

### Cómo habilitarlo

1. El archivo `.antigravityrules` ya existe en la raíz de `Gravity_AI_bridge`.
2. Para usar este mecanismo en otro proyecto, cópialo a su raíz:
```cmd
copy F:\Gravity_AI_bridge\.antigravityrules F:\tu_proyecto\.antigravityrules
```
3. El agente que abra esa carpeta leerá las reglas y sabrá:
   - Cómo invocar al Bridge (`ask_deepseek.py`).
   - Dónde está el conocimiento persistente (`_knowledge.json`).
   - Cómo realizar auditorías adversariales antes de sugerir código.

---

*Gravity AI Bridge — [github.com/DarckRovert/Gravity_AI_bridge](https://github.com/DarckRovert/Gravity_AI_bridge)*
*Stream en vivo: [twitch.tv/darckrovert](https://twitch.tv/darckrovert)*
