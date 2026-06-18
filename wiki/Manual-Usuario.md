# 📖 Manual de Usuario — Gravity AI Bridge V16.0 PRO

Guía paso a paso para operar el Dashboard y todos los módulos del ecosistema.

---

## 🚀 Inicio Rápido

### 1. Arrancar el sistema

```bat
cd F:\Gravity_AI_bridge
gravity.bat
```

O directamente:

```bash
python bridge_server.py
```

El servidor arrancará en `http://localhost:7860`. El Dashboard React SPA se sirve automáticamente desde `frontend/dist`.

### 2. Primer acceso

1. Abre `http://localhost:7860` en Chrome/Edge.
2. Ve a **⚙️ Configuración** (sidebar).
3. Introduce tu API Key del proveedor de LLM preferido (Ollama local no requiere key).
4. El sistema auto-detecta el hardware e inicializa el Turbo KV-Cache si detecta Ollama.

---

## 💬 Chat Auditor (`/chat`)

El panel de chat principal con soporte multi-rol y streaming SSE.

| Control | Descripción |
|---|---|
| **Selector de Modelo** | Elige el LLM activo (Ollama, OpenAI, Anthropic, etc.) |
| **Selector de Rol** | `auditor` · `planner` · `coder` · `researcher` · `executor` |
| **Plantillas** | Prompts predefinidos para tareas recurrentes |
| **RAG Toggle** | Inyecta contexto de tu base de conocimiento local |
| **Streaming SSE** | Los tokens aparecen en tiempo real sin esperar respuesta completa |

**Tip:** Si tu mensaje contiene una URL, el sistema la raspa automáticamente (Firecrawl/urllib) e inyecta el contenido en el contexto.

---

## 🎬 Video Studio (`/video`) — Motor Cinematic V2.0 PBR

El módulo más potente del ecosistema. Produce videoclips musicales y videos de YouTube de calidad Hollywood desde una GPU integrada.

### Flujo de creación de un videoclip musical

1. **Tipo de Job**: Selecciona `music` en el formulario.
2. **Audio Track**: Sube o especifica la ruta de tu archivo MP3/WAV.
3. **Estilo Visual**: Elige entre `biomechanic_v13` (Odisea Espacial), `julia_v13` (Fractal), `quantum_v13` (Túnel Cuántico).
4. **Resolución**: `1280x720` para YouTube, `1080x1920` para Shorts.
5. **FPS**: 24 para cinematográfico, 30 para social media.
6. Haz clic en **▶ Generar Video**.

### Indicadores del motor durante el render

| Log | Significado |
|---|---|
| `[AISceneGen] Intentando flux-realism...` | Descargando imagen de Pollinations (90s) |
| `[AISceneGen] Rotando a flux...` | Primer modelo falló, reintentando |
| `[AISceneGen] Usando nebulosa fractal FBM` | Fallback procedural activo |
| `[GLSL V13] Compilando shaders...` | Motor OpenGL inicializando |
| `[RemotionEngine] Renderizado exitoso.` | Short 9:16 generado |

### Shorts automáticos

Al finalizar el video principal, el pipeline genera automáticamente **4 Shorts de 58 segundos** en vertical (9:16) con:
- Subtítulos karaoke interactivos (Whisper ASR palabra por palabra)
- Tipografía Montserrat/Inter con glow neón `#00f0ff`
- VHS Scanlines y letterbox cinematográfico

Los Shorts se guardan en `_videos/` con sufijo `_short_partN.mp4`.

---

## 🤖 Multi-Agent (`/multiagent`)

Compara múltiples LLMs en paralelo sobre la misma pregunta.

1. Introduce el prompt en el campo superior.
2. Selecciona **2, 3 o 5 modelos** del selector.
3. Elige el modo:
   - **Paralelo**: Todas las respuestas side-by-side.
   - **Voting**: Los modelos votan la mejor respuesta.
   - **Debate**: Los modelos argumentan entre sí.
4. Haz clic en **⚡ Comparar**.

---

## 🛡️ HITL — Human in the Loop (`/hitl`)

Intercepta acciones de alto riesgo del agente antes de ejecutarlas.

Las tools interceptadas incluyen: `code_runner`, `shell_exec`, `file_write`, `deploy`, `git_push`.

Cuando el agente intenta ejecutar una de estas tools:
1. Aparece una **alerta roja** en el badge del sidebar.
2. Ve a `/hitl` para ver la solicitud pendiente.
3. Revisa el detalle: herramienta, argumentos y contexto.
4. Haz clic en ✅ **Aprobar** o ❌ **Rechazar**.
5. El agente recibe tu decisión y continúa/aborta.

> **Timeout**: Si no respondes en 120 segundos, la acción es rechazada automáticamente.

---

## 📚 RAG — Retrieval Augmented Generation (`/rag`)

Enriquece las respuestas del LLM con tu base de conocimiento local.

1. Coloca documentos (`.txt`, `.md`, `.pdf`) en la carpeta `_rag_index/`.
2. Haz clic en **🔄 Re-indexar** para procesar los documentos.
3. Activa el toggle **RAG Enabled** en el panel.
4. Todos los mensajes del Chat Auditor incluirán automáticamente el contexto relevante.

---

## 👤 Aletheia V2V Studio (`/v2v`)

Motor de VTuber en tiempo real con FasterLivePortrait.

1. **Generar Avatar Base**: Selecciona un preset y haz clic en "Generar Avatar SD-Turbo" (se ejecuta una sola vez por sesión).
2. **Activar Webcam**: El sistema captura tu rostro.
3. **Drive Live**: LivePortrait ONNX transfiere parpadeos, rotación y labial a tu avatar a 30-60 FPS.

---

## ⚔️ Game Server Manager (`/gameserver`)

Control del servidor WoW MangosD.

| Botón | Acción |
|---|---|
| ▶ Start | Verifica MySQL pre-flight y arranca MangosD |
| ⏹ Stop | Detiene el servidor y ejecuta `mysqldump` auto-backup |
| 📋 Log | Stream de los últimos 500 lines del ring-buffer |
| 👥 Players | Lista de personajes conectados en tiempo real |

---

## 📹 OBS Studio Controller (`/obs`)

Control total de OBS vía WebSocket v5.

1. Asegúrate de que OBS esté corriendo con WebSocket habilitado (puerto 4455).
2. El Bridge se conecta automáticamente al arrancar.
3. Desde el panel puedes: cambiar escenas, silenciar fuentes, iniciar/detener streaming.

### Gravity Spark — Overlays AI

1. En el chat del panel OBS, describe el overlay deseado.
2. El LLM genera el HTML/JS autocontenido.
3. El sistema lo inyecta directamente como Browser Source en OBS.
4. Puedes modificarlo en caliente: "hazlo más grande", "cambia el color a azul".

---

## 🔒 Security Monitor (`/security`)

- **Security Score**: Puntuación 0-100 del estado de seguridad del sistema.
- **Procesos**: Lista de procesos activos con PID. Botón Kill para eliminar procesos sospechosos.
- **Puertos**: Mapa de puertos abiertos con servicio identificado.
- **Anti-DDoS**: Bloqueo automático de IPs con más de 120 requests en ventana.

---

## 🕷️ Firecrawl (`/firecrawl`)

Extrae el contenido de cualquier URL como Markdown limpio.

1. Introduce la URL en el campo de texto.
2. Haz clic en **🕷️ Raspar**.
3. El resultado aparece en el visor Markdown con badge indicando si usó la API de Firecrawl o el fallback HTTP nativo.
4. Copia el resultado con un clic para usarlo en el Chat Auditor.

---

## ⚙️ Configuración (`/config`)

| Campo | Descripción |
|---|---|
| **Base URL** | Endpoint del backend LLM (ej: `http://localhost:11434`) |
| **Model Name** | Nombre del modelo activo (ej: `llama3.2:latest`) |
| **API Key** | Cifrada con DPAPI y guardada en `_keystore.bin` |
| **Daily Budget** | Límite de gasto diario en USD (HTTP 429 al superarlo) |
| **RAG Enabled** | Toggle de inyección de contexto RAG en el chat |
