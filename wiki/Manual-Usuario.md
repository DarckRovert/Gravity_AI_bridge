# Manual de Usuario — Gravity AI Bridge V10.0
**Diamond-Tier Edition** · [github.com/DarckRovert/Gravity_AI_bridge](https://github.com/DarckRovert/Gravity_AI_bridge) · [twitch.tv/darckrovert](https://twitch.tv/darckrovert)

---

## ¿Qué es Gravity AI Bridge?

Gravity AI Bridge es un **servidor proxy OpenAI-compatible** que actúa como punto de entrada único para todos tus modelos de IA, tanto locales como en la nube. En lugar de configurar cada herramienta (VS Code, Aider, Cursor) para conectarse a un modelo diferente, las apuntas todas a `http://localhost:7860/v1` y Gravity hace el resto: elige automáticamente el mejor modelo disponible, monitorea el hardware, registra costes y expone todo mediante un Dashboard web de 17 paneles.

**No requiere GPU dedicada.** Funciona con CPU, iGPU AMD/Intel y cualquier GPU NVIDIA/AMD con VRAM suficiente para correr un modelo cuantizado.

---

## Instalación

### Para usuarios finales (sin Python)
1. Descarga `Gravity_AI_Bridge_V10.0_Setup.exe`
2. Ejecuta el instalador → "Siguiente" tres veces → "Instalar"
3. Marca "Iniciar Gravity AI Bridge ahora" al finalizar
4. Un icono aparecerá en la bandeja del sistema (esquina inferior derecha)
5. Doble clic en el icono → se abre el Dashboard en el navegador

### Para desarrolladores
```bash
# 1. Clonar
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge

# 2. Dependencias
pip install -r requirements.txt

# 3. Configuración inicial interactiva
python INSTALAR.py

# 4. Iniciar el servidor
python bridge_server.py

# 5. Abrir el Dashboard
# http://localhost:7860
```

### Requisitos mínimos
| Componente | Mínimo | Recomendado |
|:---|:---|:---|
| OS | Windows 10 (1809) | Windows 11 |
| Python | 3.11 | 3.12 |
| RAM | 8 GB | 32 GB |
| Almacenamiento | 500 MB | 10 GB (modelos) |
| GPU | Opcional (iGPU funciona) | 8+ GB VRAM |

---

## Primeros Pasos (5 minutos)

### Paso 1 — Instalar al menos un motor de IA local

El Bridge necesita al menos un motor activo. Las opciones más sencillas:

**Ollama** (recomendado para empezar):
```bash
# Instalar desde https://ollama.com
ollama pull qwen2.5-coder:7b    # ~4 GB, rápido en CPU
ollama serve                    # Iniciar en puerto 11434
```

**LM Studio**:
1. Descargar desde https://lmstudio.ai
2. Descargar cualquier modelo GGUF
3. Click "Start Server" (puerto 1234)

### Paso 2 — Confirmar que el Bridge detecta el motor

Abre el Dashboard → **System Status**. Verás el proveedor activo en verde con su latencia en ms.

### Paso 3 — Hacer tu primera consulta

En el panel **Chat Auditor**, escribe una pregunta y presiona `Ctrl+Enter` o click en "Enviar". La respuesta aparecerá en streaming.

---

## Guía de Cada Panel

### 💬 Chat Auditor

El panel principal. Interfaz de chat directa con el modelo activo.

**Cómo usarlo:**
- Escribe en el área de texto y presiona `Ctrl+Enter` para enviar
- El streaming muestra la respuesta token por token
- El modelo activo se muestra en la esquina inferior del sidebar

**Controles del contexto:**
- El historial completo se envía con cada mensaje (la IA recuerda la conversación)
- Para reiniciar el contexto, recarga la página o usa `/limpiar` en el CLI

**Personalidad inyectada automáticamente:**
Si no hay un system prompt en la petición, el Bridge inyecta automáticamente la personalidad definida en `_knowledge.json`. Esto es útil para dar un rol específico al modelo sin configurarlo en cada cliente.

---

### 🎨 Vision Studio

Generación de imágenes via **Fooocus** (incluido en `_integrations/Fooocus/`).

**Requisito previo:** Fooocus debe estar corriendo. El Bridge lo detecta en el puerto 7865.

**Para iniciar Fooocus:**
```bash
# Desde el panel System Status → botón "Iniciar Fooocus"
# O manualmente:
cd _integrations\Fooocus
run.bat
```

**Parámetros:**
| Campo | Descripción | Ejemplo |
|:---|:---|:---|
| Prompt | Descripción de la imagen | "A cyberpunk city at night, rain" |
| Negative | Lo que NO quieres en la imagen | "blurry, low quality, ugly" |
| Performance | Velocidad vs calidad | Speed (rápido) / Quality (mejor) |
| Estilo | Preset visual | Fooocus V2, Anime, Photorealistic |
| Tamaño | Resolución en píxeles | 1024×1024 (cuadrado) |

Las imágenes generadas se guardan en `_integrations/Fooocus/outputs/`.

---

### 🖼️ Image Queue

Cola de trabajos de generación con estado en tiempo real.

Puedes añadir trabajos a la cola desde el CLI o via API:
```bash
# Via API directa
curl -X POST http://localhost:7860/v1/queue/add \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a sunset over mountains", "performance": "Speed"}'
```

Los trabajos se procesan en orden FIFO. El panel muestra el estado de cada job: `pending`, `processing`, `done`, `failed`.

---

### 🚀 Deploy Manager

Pipeline automatizado para desplegar proyectos web a **Netlify** en un clic.

**Configurar el proyecto:**
1. En el panel Deploy → campo "Ruta del Proyecto"
2. Escribe la ruta completa de tu proyecto Next.js/Vite/React
3. Click "Guardar Ruta"

**Requisitos del entorno:**
```bash
npm install -g netlify-cli     # Instalar CLI de Netlify
netlify login                  # Autenticarse (solo primera vez)
```

**Iniciar el deploy:**
1. Click "Iniciar Deploy"
2. El log en tiempo real muestra:
   - `npm run build` compilando el proyecto
   - `netlify deploy --prod` subiendo a producción
3. Al finalizar aparece la URL del sitio desplegado

---

### ⚔️ Game Servers — vMaNGOS WoW Vanilla

Control completo de tu servidor privado de World of Warcraft (vMaNGOS).

**Controles principales:**
| Botón | Acción | Notas |
|:---|:---|:---|
| ▶ Iniciar | Arranca Mangosd + Realmd | Tarda ~15s en estar listo |
| ⏹ Detener | Para ambos procesos limpiamente | |
| 🔄 Reiniciar | Stop → espera → Start | Útil tras cambios de config |
| 📤 Exponer WAN | Configura IP pública | Requiere port forwarding en tu router |

**Crear una cuenta de jugador:**
1. Escribe el usuario y contraseña en los campos del formulario
2. Click "Registrar Cuenta"
3. La cuenta se crea automáticamente con nivel GM 0

**Enviar comandos de administrador:**
El campo "Comando de Admin" envía comandos directamente via SOAP al servidor:
```
.server info          → Estado del servidor
.account create X Y   → Crear cuenta X con contraseña Y
.account set gmlevel X Y 1   → Dar GM level 1 a la cuenta X en realm Y
.reload config        → Recargar configuración sin reiniciar
```

**Exponer a internet:**
1. Configura el port forwarding en tu router: puerto **8085** (juego) y **3724** (auth)
2. En el panel, usa el modal "Exponer WAN" e ingresa tu IP pública o dominio DDNS
3. El Bridge actualiza automáticamente `mangosd.conf` y `realmd.conf`

---

### 🤖 Multi-Agent Orchestrator

Envía el mismo prompt a múltiples modelos simultáneamente y compara sus respuestas.

**Modos de operación:**

| Modo | Comportamiento | Cuándo usarlo |
|:---|:---|:---|
| ⚡ Paralelo | Todos los modelos responden y se muestran en cards individuales | Comparar estilos y profundidad |
| 🗳️ Vote | El sistema puntúa las respuestas y declara un ganador | Obtener la "mejor" respuesta automáticamente |

**Cómo usarlo:**
1. Selecciona el modo (Paralelo o Vote)
2. Selecciona cuántos modelos usar (2-4)
3. Escribe el prompt en el área de texto
4. Click "🚀 Ejecutar"
5. Las respuestas aparecen en cards con el proveedor, modelo y tiempo de respuesta

**Nota:** Funciona mejor cuando tienes múltiples proveedores activos simultáneamente.

---

### 🖥️ Hardware Monitor

Perfil completo de tu hardware para inferencia de IA.

**Métricas mostradas:**
| Métrica | Descripción |
|:---|:---|
| GPU Primaria | Nombre, tipo (ROCm/CUDA/iGPU/Vulkan) |
| VRAM Disponible | Memoria de GPU en GB |
| RAM del Sistema | RAM total instalada |
| Contexto Óptimo | Máximo de tokens recomendado para tu hardware |
| KV-Cache | Nivel de cuantización activo (q4_0/q8_0) |
| NPU / Acelerador | Ryzen AI NPU si está disponible |

**Tabla de GPUs:**
Muestra **todas** las GPUs detectadas en el sistema, incluyendo iGPUs, con su estado de backend, VRAM y versión GFX (importante para ROCm en AMD).

**¿Qué es el Contexto Óptimo?**
Es el número máximo de tokens (palabras aproximadas) que puedes usar en una conversación sin que el modelo se quede sin memoria de GPU. El Bridge lo calcula automáticamente según tu VRAM, el tamaño estimado del modelo y la cuantización del KV-Cache.

---

### 💰 Cost Center

Monitoreo de gastos en tiempo real para proveedores cloud.

> **Nota:** Los proveedores locales (Ollama, LM Studio, etc.) son gratuitos. Este panel solo registra gastos de Anthropic, OpenAI, Gemini, Groq, etc.

**Panel principal:**
- **Sesión actual** — lo que llevas gastado desde que iniciaste el Bridge
- **Hoy (total)** — gasto acumulado del día
- **Barra de límite** — visual del % del límite diario consumido. Se vuelve roja al superarlo

**Configurar el límite diario:**
Edita `config.yaml`:
```yaml
security:
  daily_limit_usd: 5.00    # Límite en USD
```

**Tabla por proveedor:**
Muestra desglose de llamadas, tokens de entrada/salida y coste exacto por cada proveedor cloud que hayas usado en el día.

---

### ⚡ Engine Watchdog

Gestión del motor activo con auto-switch inteligente.

**Estados del motor:**
| Badge | Significado |
|:---|:---|
| 🟢 AUTO-SWITCH ACTIVO | El Watchdog elige el mejor motor disponible automáticamente |
| 🔴 MODELO BLOQUEADO (MANUAL) | Estás usando un motor específico seleccionado manualmente |

**¿Cuándo aparece LOCKED?**
Cuando desde el CLI usas un comando como `/usar lmstudio` o `/modelo qwen2.5-coder:32b`. El Bridge fija ese motor y no cambiará aunque otro sea más rápido.

**Forzar Unlock:**
Click en el botón "🔓 Forzar Unlock" para volver al modo automático. El Watchdog evaluará todos los proveedores disponibles y seleccionará el óptimo en el siguiente ciclo (máximo 30 segundos).

---

### 💾 Session Manager

Gestión de sesiones conversacionales guardadas desde el CLI.

**Guardar una sesión desde el CLI:**
```
/guardar debug-sesion-abril      → Guarda la conversación actual
/cargar debug-sesion-abril       → Restaura esa conversación
/fork rama-con-otro-contexto     → Crea una variante sin perder el original
```

**En el Dashboard:**
La tabla muestra todas las sesiones disponibles con:
- **Nombre** — identificador elegido al guardar
- **Branch** — rama de la conversación (main por defecto)
- **Turnos** — número de intercambios guardados
- **Guardado** — fecha y hora exacta

---

### 📚 RAG — Retrieval Augmented Generation

Motor de búsqueda semántica sobre tus documentos locales, sin enviar nada a la nube.

**¿Cómo funciona?**
1. Indexas documentos PDF/TXT/MD/DOCX localmente
2. El sistema genera embeddings vectoriales de cada fragmento
3. Cuando consultas con `/rag:`, el sistema encuentra los fragmentos más relevantes
4. Inyecta esos fragmentos como contexto en el prompt antes de enviarlo al modelo

**Indexar documentos desde el CLI:**
```bash
/rag indexar C:\mis-docs\manual-tecnico.pdf
/rag indexar C:\mis-docs\notas.md
```

**Consultar el índice:**
```
/rag: ¿Qué dice el manual sobre la instalación de ROCm?
```

**Panel del Dashboard:**
Muestra el estado actual del índice en tiempo real:
- Documentos indexados
- Chunks totales (fragmentos generados)
- Tamaño del índice en disco
- Estado Online/Sin Índice

---

### 🔌 MCP Servers

Integración con el **Model Context Protocol**, un estándar que permite al Bridge conectarse a servidores externos que exponen herramientas y recursos.

**Configurar un servidor MCP en `config.yaml`:**
```yaml
mcp_servers:
  filesystem:
    path: npx
    args: [-y, "@modelcontextprotocol/server-filesystem", "C:/mis-proyectos"]
  github:
    path: npx
    args: [-y, "@modelcontextprotocol/server-github"]
  brave-search:
    path: npx
    args: [-y, "@modelcontextprotocol/server-brave-search"]
```

**Servidores MCP populares:**
| Servidor | Función |
|:---|:---|
| `server-filesystem` | Leer/escribir archivos del sistema |
| `server-github` | Operaciones con repositorios GitHub |
| `server-brave-search` | Búsqueda web via Brave API |
| `server-sqlite` | Consultas a bases de datos SQLite |
| `server-postgres` | Consultas a PostgreSQL |

Reinicia el bridge tras modificar la configuración de MCP.

---

### 🛠️ Tools

**Herramientas integradas disponibles internamente en el Bridge:**

| Herramienta | Uso | Comando CLI |
|:---|:---|:---|
| 🧠 Code Runner | Ejecuta Python/Bash aislado | `/run print('hola')` |
| 📂 File Edit V2 | Edición de archivos con patch diff | Uso interno del agente |
| 🔎 Web Search | DuckDuckGo sin API key | `/buscar últimas noticias AI` |
| 🪵 Git Tool | Diff, log, commit, push | Uso interno del deploy |
| 🪟 Grep Tool | Búsqueda regex en archivos | Uso interno de auditoría |
| 🖥️ Native Trigger | Notificaciones y popups del SO | Uso interno de alertas |

---

### 📡 System Status

Vista de métricas del sistema en tiempo real:

- **Proveedores activos** — lista de todos los proveedores con latencia actual y estado
- **Modelo activo** — proveedor y modelo que se usará en la próxima petición
- **Requests totales** — contador desde el inicio del Bridge
- **Gráfico de latencia** — histórico visual de los últimos tiempos de respuesta

El gráfico se actualiza automáticamente cada 10 segundos.

---

### 🛡️ Security

Resultado del último escaneo Zero-Trust con:
- Intentos de acceso rechazados
- IPs bloqueadas por rate limiting abusivo
- Estado del firewall y configuración de seguridad

**Forzar escaneo inmediato:**
Click en "🔍 Escanear Ahora". También disponible via:
```bash
curl -X POST http://localhost:7860/v1/security/scan
```

---

### 📋 Audit Log

Historial completo e inmutable de todas las peticiones procesadas:

| Campo | Descripción |
|:---|:---|
| ID | Identificador único de la petición |
| Proveedor | Motor que procesó la petición |
| Modelo | Modelo específico usado |
| Tokens ↓ | Tokens de entrada (prompt) |
| Tokens ↑ | Tokens de salida (respuesta) |
| Coste | Coste USD (0 si es local) |
| Latencia | Tiempo total de respuesta |
| Fecha | Timestamp exacto |

Los logs se almacenan en `_audit_log.jsonl` (formato JSON Lines, compatible con cualquier procesador de logs).

---

### ⚙️ Configuración

**API Keys de proveedores cloud:**
1. Selecciona el proveedor en el dropdown
2. Pega tu API key
3. Click "Guardar" — la key se cifra inmediatamente con DPAPI (solo accesible en tu Windows)

**Proveedores disponibles para configurar API key:**
- Anthropic (Claude 3.5/3.7)
- OpenAI (GPT-4o, o1)
- Google (Gemini 2.0 Flash)
- Groq (LLaMA, Mistral ultra-rápido)
- Mistral AI

**IDE Setup:**
Configura automáticamente tus herramientas de desarrollo:
- **Continue.dev** — crea `.continue/config.yaml`
- **Aider** — crea `aider.conf.yml`
- **Cursor** — crea `_integrations/cursor.json`

O desde la terminal:
```bash
python core/ide_integrator.py todo    # Configura los tres a la vez
python core/ide_integrator.py continue
python core/ide_integrator.py aider
python core/ide_integrator.py cursor
```

---

## CLI del Bridge — Referencia Completa

Cuando ejecutas el bridge desde la terminal (`python bridge_server.py` → luego `python ask_deepseek.py` en otra ventana), tienes acceso al CLI con los siguientes comandos:

### Sesiones
| Comando | Descripción |
|:---|:---|
| `/guardar <nombre>` | Persiste el historial actual en `_saves/<nombre>.json` |
| `/cargar <nombre>` | Restaura una sesión guardada |
| `/fork <rama>` | Crea un branch sin borrar el original |
| `/sesiones` | Lista todas las sesiones disponibles |

### RAG
| Comando | Descripción |
|:---|:---|
| `/rag indexar <ruta>` | Indexa un documento |
| `/rag: <pregunta>` | Consulta el índice con contexto semántico |

### Modelo
| Comando | Descripción |
|:---|:---|
| `/usar <proveedor>` | Fija un proveedor específico (activa LOCK) |
| `/modelo <nombre>` | Fija un modelo específico |
| `/auto` | Vuelve al auto-switch |

### Búsqueda y Código
| Comando | Descripción |
|:---|:---|
| `/buscar <query>` | Web search DuckDuckGo |
| `/run <código>` | Ejecuta Python inline |
| `/leer <ruta>` | Carga el contenido de un archivo al contexto |
| `/leer-carpeta <ruta>` | Carga todos los archivos de una carpeta |

### Memoria y Conocimiento
| Comando | Descripción |
|:---|:---|
| `!aprende <regla>` | Añade una regla permanente al `_knowledge.json` |
| `!olvida <indice>` | Elimina una regla por su índice |
| `!reglas` | Lista todas las reglas activas |

---

## Preguntas Frecuentes Rápidas

**¿Necesito ejecutar el installer como administrador?**
No. El instalador sí requiere permisos elevados (para escribir en `Program Files`), pero el Bridge en modo desarrollador no los necesita.

**¿Por qué el Build falla con "Icon not found"?**
El archivo `assets/gravity_icon.ico` no existía. Desde el `build_installer.bat` actualizado se genera automáticamente. También puedes generarlo manualmente:
```bash
python make_icon.py
```

**¿Puedo usar Gravity desde otro dispositivo en la red?**
Sí. El servidor escucha en `0.0.0.0:7860`. Desde otro dispositivo en la misma red: `http://IP_DEL_HOST:7860`.

**¿Qué pasa si tengo Ollama y LM Studio al mismo tiempo?**
El Bridge detecta ambos y usa el de menor latencia. Puedes forzar uno específico con `/usar ollama` desde el CLI.

---

## Resolución de Problemas

| Problema | Causa probable | Solución |
|:---|:---|:---|
| Dashboard no carga | Puerto 7860 ocupado | `netstat -a -n -o \| findstr 7860` y matar el proceso |
| "No provider available" | Ningún motor está corriendo | Inicia Ollama, LM Studio o cualquier otro motor |
| Build falla con "Icon not found" | Falta `assets/gravity_icon.ico` | `python make_icon.py` |
| Build falla con "PyInstaller not found" | pip sin acceso a internet | `pip install pyinstaller --trusted-host pypi.org` |
| Costes siempre en $0.0000 | Solo usas proveedores locales | Normal — los locales son gratuitos |
| Watchdog en LOCKED sin querer | Se fijó un modelo manualmente | Click "Forzar Unlock" en el panel Watchdog |
| RAG muestra 0 documentos | Índice vacío | Indexa documentos con `/rag indexar <ruta>` |
| Timeout en Multi-Agent | Los modelos tardan demasiado | Reduce N_modelos a 2 o usa modelos más pequeños |
