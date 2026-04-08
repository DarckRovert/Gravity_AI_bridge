# Manual de Usuario — Gravity AI Bridge V8.0 PRO

## Índice

1. [Instalación](#1-instalación)
2. [Primer Arranque](#2-primer-arranque)
3. [Uso del CLI](#3-uso-del-cli)
4. [Dashboard Web](#4-dashboard-web)
5. [Gestión de API Keys](#5-gestión-de-api-keys)
6. [Sistema RAG](#6-sistema-rag)
7. [Verificación de Código](#7-verificación-de-código)
8. [MCP — Herramientas Externas](#8-mcp--herramientas-externas)
9. [Sesiones](#9-sesiones)
10. [Bridge Server](#10-bridge-server)
11. [Integración con IDEs](#11-integración-con-ides)
12. [Atajos y Tips](#12-atajos-y-tips)

---

## 1. Instalación

### Con motor de IA local (recomendado)

**Paso 1**: Instala [Ollama](https://ollama.ai):
```cmd
winget install Ollama.Ollama
ollama pull deepseek-r1:14b
```

**Paso 2**: Instala Gravity AI Bridge:
```cmd
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge
INSTALAR.bat
```

El instalador hará todo automáticamente. Al terminar, el comando `gravity` estará disponible en toda tu terminal.

### Sin motor local (solo cloud)

Sigue el instalador y configura tu API Key cuando te lo pida. Soporta OpenAI, Anthropic, Google Gemini, Groq y más.

---

## 2. Primer Arranque

La primera vez que ejecutes `gravity`, aparecerá el wizard de bienvenida:

```
⚡ GRAVITY AI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Bienvenido a Gravity AI Bridge V8.0 PRO
Primera ejecución detectada. Configuración inicial.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Motores locales detectados: Ollama

┌─ Comandos esenciales ─────────────────────┐
│ /help    Lista todos los comandos          │
│ /model   Cambiar motor o modelo activo     │
│ /keys    Configurar API Keys               │
└───────────────────────────────────────────┘

  Presiona ENTER para iniciar...
```

---

## 3. Uso del CLI

### Modo Interactivo
```cmd
gravity
```
Abre el Auditor Senior con banner completo mostrando GPU, modelo activo y estadísticas.

### Modo Pipe (para scripts)
```cmd
gravity "explica este error: AttributeError: module has no attribute X"
cat error.log | gravity "analiza este log"
```

### Comandos Esenciales

#### Cambiar modelo
```
Gravity> /model
  [0] ollama (5 modelos)
  [1] lmstudio (3 modelos)
  [A] Automático
Selección: 0
  [0] deepseek-r1:14b
  [1] qwen2.5:32b
Selecciona modelo: 0
✓ Forzado a ollama → deepseek-r1:14b
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
│ Proveedor │ Cat.  │ Latencia │ Modelos │Estado│
│ ollama    │ LOCAL │  124ms   │    5    │ONLINE│
│ openai    │ CLOUD │    -     │    0    │OFFLIN│
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
→ El modelo investigará y proveerá un plan detallado antes de codificar.
```

---

## 4. Dashboard Web

Inicia el bridge y accede a `http://localhost:7860`:

```cmd
gravity --server
# o
INICIAR_SERVIDOR.bat
```

### Pestañas disponibles:

**💬 Chat**: Chat en tiempo real con streaming. Acepta Markdown. Accesos rápidos a comandos frecuentes.

**📡 Estado**: Estado de todos los backends con latencia en vivo. Se actualiza cada 15 segundos.

**📋 Audit Log**: Historial de las últimas 100 inferencias con tokens, latencia y coste.

**⚙️ Configuración**: Gestión de API Keys directamente desde el browser.

---

## 5. Gestión de API Keys

### Desde el CLI
```
# Listar keys configuradas
Gravity> /keys list

# Añadir una key
Gravity> /keys set openai
API Key para openai: ****

# Eliminar una key
Gravity> /keys del openai
```

### Desde el Dashboard Web
1. Ve a la pestaña **⚙️ Configuración**.
2. Escribe el nombre del proveedor (`openai`, `anthropic`, `groq`, etc.).
3. Pega tu API Key.
4. Haz clic en **Guardar Key Cifrada**.

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

## 6. Sistema RAG

### Indexar documentos
```
# Indexar un archivo
Gravity> /index F:\proyecto\main.py

# Indexar una carpeta completa
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
Cuando tu mensaje contiene frases como "busca en mi código", "del contexto" o "en mi código", el RAG inyecta automáticamente los fragmentos más relevantes como contexto.

---

## 7. Verificación de Código

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

## 8. MCP — Herramientas Externas

```
Gravity> /mcp C:\ruta\mcp-git\server.py

Conectando con servidor MCP: C:\ruta\mcp-git\server.py...
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

## 9. Sesiones

```
# Guardar sesión actual
Gravity> /save revision-api-jwt

# Listar sesiones
Gravity> /sessions
┌─────────────────────┬────────┬──────────────────┐
│ Nombre              │ Tamaño │ Modificado       │
│ revision-api-jwt    │ 12 KB  │ 2026-04-08 21:00 │
└─────────────────────┴────────┴──────────────────┘

# Cargar sesión
Gravity> /load revision-api-jwt
✓ Sesión cargada. (24 mensajes)

# Fork de sesión
Gravity> /branch alternativa
✓ Fork creado: alternativa

# Exportar a Markdown
Gravity> /export md
✓ Markdown exportado: F:\Gravity_AI_bridge\session_20260408_210000.md
```

---

## 10. Bridge Server

```cmd
# Iniciar (modo ventana visible)
INICIAR_SERVIDOR.bat

# Iniciar en modo fantasma (segundo plano, sin ventana)
MODO_FANTASMA.vbs
```

### Información al arrancar:
```
Dashboard Web:  http://localhost:7860/
API Endpoint:   http://localhost:7860/v1/chat/completions
Métricas:       http://localhost:7860/metrics
Estado:         http://localhost:7860/v1/status
```

---

## 11. Integración con IDEs

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

### Aider
Usa el archivo `aider.conf.yml` incluido o ejecuta:
```cmd
aider --openai-api-base http://localhost:7860/v1 --openai-api-key gravity-local
```

---

## 12. Atajos y Tips

| Tip | Descripción |
|-----|-------------|
| `!aprende <regla>` | Persiste una regla permanente al sistema (se añade al system prompt) |
| `gravity --status` | Ver estado de todos los motores sin entrar al CLI |
| `gravity --dashboard` | Abrir el dashboard directamente en el browser |
| `Ctrl+C` dentro del CLI | No cierra — escribe `/exit` para salir correctamente |
| Banner solo al inicio | El banner no se redibuja en cada respuesta para no saturar la pantalla |
| Cache automático | Las respuestas idénticas se cachean 24h en SQLite WAL |
| Sliding Window | El contexto se recorta automáticamente al superar 128k tokens |

---

*Gravity AI Bridge — [github.com/DarckRovert/Gravity_AI_bridge](https://github.com/DarckRovert/Gravity_AI_bridge)*  
*Stream en vivo: [twitch.tv/darckrovert](https://twitch.tv/darckrovert)*
