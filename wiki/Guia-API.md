# 📖 Guía de Integración y API — Gravity AI Bridge V15.0 PRO
**Omniscient-Tier Edition** · Base URL: `http://localhost:7860`

El Bridge expone una API HTTP completamente compatible con el estándar OpenAI, además de un potente micro-kernel con más de 54 módulos especializados para orquestación inteligente (Video Studio, Overlays OBS, Monetización Pasiva, Agentes Multi-sesión y RAG). Cualquier cliente compatible con la especificación OpenAI puede conectarse al Bridge de forma inmediata.

---

## 🔐 Seguridad y Autenticación

### 1. Autenticación de Clientes Externos
Por defecto, la API no requiere autenticación en entornos locales seguros. Sin embargo, al configurar la directiva `allowed_keys` en el archivo `config.yaml`, todas las peticiones entrantes deberán proporcionar la cabecera estándar:

```http
Authorization: Bearer tu-api-key-del-bridge
```

### 2. Cifrado de Credenciales Cloud (DPAPI)
Las API keys de proveedores en la nube (OpenAI, Anthropic, Gemini, Groq, Mistral, Firecrawl) no se guardan en texto plano en la configuración. Se transmiten mediante el endpoint seguro `/v1/keys` y se encriptan utilizando la API de Protección de Datos de Windows (DPAPI). Esto asegura que únicamente la identidad del usuario de Windows que ejecuta el bridge pueda descifrarlas en tiempo de ejecución.

---

## 🧠 Endpoints Compatibles OpenAI

### 1. `POST /v1/chat/completions`
El endpoint principal de inferencia. Es totalmente transparente para librerías oficiales de OpenAI en Python, Node.js, LangChain, Continue.dev o Aider.

#### Características Especiales del Bridge:
- **Auto-selección Inteligente (`gravity-bridge-auto`):** Si solicitas este modelo virtual, el bridge consultará periódicamente el `provider_manager` y enrutará la petición al modelo local más rápido y saludable en Ollama/LM Studio. Si todos fallan o la carga es extrema, conmuta automáticamente a un proveedor cloud de respaldo en menos de 30 segundos (Watchdog activo).
- **Inyección de Personalidad (data_guardian):** Si la petición no incluye un system prompt, el micro-kernel carga de forma transparente las reglas de personalidad y directrices críticas configuradas en `_knowledge.json`.
- **RAG Vectorial Transparente:** Si la inyección RAG está habilitada en `_settings.json`, el bridge extrae la última consulta del usuario, ejecuta una búsqueda semántica de alta velocidad en `_rag_index` (usando el motor vectorial local) e introduce el fragmento recuperado como contexto en el System Prompt al vuelo, sin coste adicional.
- **Reasoning Stripper:** Procesa de forma interactiva el streaming SSE y remueve por completo los bloques `<think>...</think>` que generan los modelos de razonamiento (como DeepSeek-R1) antes de enviárselos al cliente final, logrando una interfaz limpia.

#### Request en Streaming (Por defecto en IDEs y chats interactivos):
```json
{
  "model": "gravity-bridge-auto",
  "messages": [
    {"role": "user", "content": "¿Cómo optimizo mi configuración de GPU en AMD ROCm?"}
  ],
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 2048
}
```

#### Respuesta SSE (Server-Sent Events):
```http
data: {"id":"chatcmpl-g1h3n5","object":"chat.completion.chunk","model":"qwen2.5-coder:32b","choices":[{"index":0,"delta":{"content":"Para"},"finish_reason":null}]}

data: {"id":"chatcmpl-g1h3n5","object":"chat.completion.chunk","model":"qwen2.5-coder:32b","choices":[{"index":0,"delta":{"content":" optimizar"},"finish_reason":null}]}

data: [DONE]
```

---

## 🪐 Conciencia Sistémica: `POST /v1/gravity/chat`

El endpoint `/v1/gravity/chat` es la joya de la corona del bridge en su versión **V15.0 PRO**. A diferencia de una petición de chat convencional, este endpoint otorga al modelo **acceso directo y conciencia de todo el sistema operativo e infraestructura del bridge**.

### Mecánica de Funcionamiento:
1. **Inyección de Contexto del Sistema (System Context):** El bridge invoca a `gravity_brain.py` para construir un Prompt dinámico masivo que describe en tiempo real:
   - Estado del hardware (GPU activa, VRAM libre, procesador, temperatura).
   - Cola de reproducción y estado de publicación del Content Scheduler.
   - Estado de la conexión a OBS Studio y overlays inyectados.
   - Workers asíncronos y sub-sesiones activas en background.
   - Estado y latencia de los motores locales (Ollama/LM Studio/Fooocus).
2. **Scraping Web Automático y Silencioso:** Si el prompt del usuario contiene una URL (ej. `"Analiza https://news.ycombinator.com y dime qué opinas"`), el bridge detecta el enlace, invoca asíncronamente el extractor premium de Firecrawl (o el parser estático de fallback), convierte el contenido web a Markdown limpio y lo inyecta directamente al prompt antes de enviarlo al LLM.
3. **Ejecución Heurística de Comandos:** Si el LLM detecta que el usuario le pide una acción de control (ej. `"Detén el servidor de WoW"`, `"Cambia la escena de OBS a 'En Vivo'"` o `"Genera un short sobre agujeros negros"`), la API de chat no solo responde con texto, sino que **ejecuta la llamada a la API nativa correspondiente de forma interna y devuelve el feedback visual al chat**.

```bash
curl -X POST http://localhost:7860/v1/gravity/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Scrapea https://example.com e inyecta un overlay en OBS con el título"}],
    "stream": false
  }'
```

---

## 💾 Workers Asíncronos: `/v1/sessions/spawn`

Para tareas intensivas de desarrollo, auditoría y análisis en paralelo, el Bridge V15.0 PRO implementa un orquestador multi-sesión basado en `session_runner.py`.

### Spawnear una Sub-Sesión Aislada:
Este comando levanta una instancia independiente del agente CLI (`ask_deepseek.py --session`) que ejecuta tareas de fondo, liberando de carga el hilo del servidor web principal. Puedes asignar un rol específico para condicionar su comportamiento y reglas de seguridad Zero-Trust.

```bash
curl -X POST http://localhost:7860/v1/sessions/spawn \
  -H "Content-Type: application/json" \
  -d {
    "session_id": "auditoria-modulo-core",
    "role": "auditor"
  }
```
*Roles válidos:* `auditor` (lectura rigurosa), `planner` (diseño), `coder` (modificación controlada), `researcher` (búsqueda intensiva) y `executor` (ejecución de comandos).

### Terminar un Worker Activo:
Si un worker se degrada o excede el tiempo de ejecución seguro, puedes forzar su finalización inmediata.
```bash
curl -X POST http://localhost:7860/v1/sessions/kill \
  -H "Content-Type: application/json" \
  -d '{"pid": 15420}'
```

---

## 🎬 Suite de Video Automático & Animaciones MAI (L0/L1/L2)

El módulo de Video Studio automatiza por completo la producción de infoproductos y contenido audiovisual mediante síntesis TTS local y orquestación ffmpeg.

### 1. `POST /v1/video/create`
Inicia un pipeline que genera guiones a través del LLM, crea prompts de imagen, los encola secuencialmente en Fooocus, sintetiza el audio narrativo mediante voces locales SAPI5 y compila el video final con transiciones, subtítulos sincronizados y animaciones.

```json
{
  "topic": "La Crisis de los Misiles en Cuba en 3 minutos",
  "n_scenes": 6,
  "voice_id": "Microsoft Helena Desktop",
  "voice_speed": 145,
  "animation_effect": "parallax",
  "animation_level": 2,
  "subtitles": true
}
```

#### Parámetro Crítico `animation_effect`:
- `"auto"` **(Tier L0):** Animaciones dinámicas básicas adaptadas heurísticamente por escena.
- `"kenburns"` / `"parallax"` / `"shake"` **(Tier L1):** Movimientos clásicos cinematográficos, zoom 2D o paneos de cámara mediante matriz de transformación de ffmpeg.
- `"comfyui_l2_i2v"` **(Tier L2 - Premium):** Exporta los fotogramas iniciales al cliente local de ComfyUI y utiliza Stable Video Diffusion (SVD) o AnimateDiff para generar una interpolación de video fotorrealista basada en la imagen (requiere hardware dedicado y ComfyUI activo).

---

## 💰 Suite de Monetización Pasiva Autónoma

El micro-kernel V15.0 PRO incluye un ecosistema de automatización financiera diseñado para alimentar canales de contenido automatizado en piloto automático.

```
┌────────────────────────┐      ┌─────────────────────────┐      ┌────────────────────────┐
│   Content Scheduler    ├─────►│  Video Creation Engine  ├─────►│  affiliate_manager     │
│   (niches.json queue)  │      │  (Synthesis + Video)    │      │  (Inject CPA/Links)    │
└────────────────────────┘      └─────────────────────────┘      └───────────┬────────────┘
                                                                             │
                                                                             ▼
┌────────────────────────┐      ┌─────────────────────────┐      ┌────────────────────────┐
│  language_cloner       │◄─────┤   Social Distribution   │◄─────┤   YouTube Content API  │
│  (Clones to EN/FR/PT)  │      │   (TikTok Headless API) │      │   (OAuth2 Headless)    │
└────────────────────────┘      └─────────────────────────┘      └────────────────────────┘
```

### Endpoints Clave para la Integración Financiera:

#### 1. Ingesta y Priorización de Enlaces CPA (`POST /v1/affiliates/program/add`)
Registra productos de afiliación comercial en un nicho específico. El `affiliate_manager` seleccionará dinámicamente el mejor producto basado en el tema del video generado y construirá llamadas a la acción (CTAs) persuasivas para insertarlas en la descripción de las publicaciones de YouTube y TikTok.
```json
{
  "niche_id": "desarrollo_software",
  "program": {
    "product_name": "Hosting Premium Descuento 70%",
    "affiliate_link": "https://host.com/gravity-ref",
    "payout_usd": 15.0,
    "cta_template": "👉 Optimiza tu servidor web hoy con un 70% de descuento usando este enlace: {link}"
  }
}
```

#### 2. Multiplicador de CPM: Clonador de Idiomas (`POST /v1/language/clone`)
Para maximizar los retornos de inversión en canales angloparlantes o europeos con altos CPMs, este endpoint toma un video completamente procesado (Job ID), traduce de forma asíncrona sus guiones cinematográficos y genera audios narrativos clonando la entonación en inglés, portugués o francés. **Logra un 300% de alcance internacional con un 0% de renderizado visual extra**.
```bash
curl -X POST http://localhost:7860/v1/language/clone \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 42,
    "languages": ["en", "pt"]
  }'
```

#### 3. Distribución Directa a Redes (`POST /v1/social/distribute`)
Envía de forma Headless y programática un video corto procesado a la cola de publicación nativa de TikTok Content API v2 e Instagram Reels API.
```json
{
  "job_id": 42
}
```

---

## 📽️ Control de OBS Studio y Overlays Spark AI

La API del micro-kernel permite un control bidireccional absoluto de tus directos o grabaciones mediante WebSocket v5.

### 1. Control de Escenas y Mezclador de Audio:
- **POST `/v1/obs/scene/switch`:** Cambia de escena en caliente (`{"scene_name": "Escena Juego"}`).
- **POST `/v1/obs/audio/volume`:** Modifica el volumen de micrófonos o capturadoras (`{"input_name": "Mic", "volume_db": -6.5}`).
- **POST `/v1/obs/stream/toggle`:** Arranca o detiene la transmisión a Twitch/YouTube.

### 2. Motor Gravity Spark: Overlays Dinámicos e Interactivos
En lugar de consumir overlays estáticos, el endpoint `/v1/obs/spark/generate` utiliza el LLM para autogenerar fragmentos completos de código HTML/CSS/JS adaptativo en vivo y los inyecta de forma transparente como *Browser Source* en OBS Studio en la escena que indiques.

```bash
curl -X POST http://localhost:7860/v1/obs/spark/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Crea una barra de donaciones interactiva con estética cyberpunk roja y animaciones de glitch en las fuentes",
    "scene_name": "Live Streaming",
    "width": 800,
    "height": 150,
    "x": 560,
    "y": 900
  }'
```

#### Modificación en Caliente (Hot-Swapping):
Si necesitas reajustar visualmente el overlay durante el directo, puedes enviar un prompt correctivo al mismo `overlay_id`. El bridge compila la modificación en background y actualiza el DOM del Browser Source de OBS en milisegundos sin parpadeos ni recargas.
```bash
curl -X POST http://localhost:7860/v1/obs/spark/edit \
  -H "Content-Type: application/json" \
  -d '{
    "overlay_id": "spark-bar-5420",
    "prompt": "Cambia el color de acento a amarillo fluorescente y acelera las transiciones de carga"
  }'
```

---

## 💻 Integración Práctica con Herramientas del Desarrollador

### 1. Conexión con LangChain (Python)
Cualquier framework moderno de agentes puede utilizar el bridge local como backend principal de inferencia de alto rendimiento y cero coste.

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    openai_api_base="http://localhost:7860/v1",
    openai_api_key="gravity-local",  # Arbitrario si no se configuró whitelist
    model_name="gravity-bridge-auto",
    temperature=0.2
)

response = llm.invoke("Analiza el rendimiento del recolector de basura de Python.")
print(response.content)
```

### 2. Configuración en Continue.dev (`config.json`)
Sustituye la inferencia cloud en tu entorno de desarrollo IDE por Qwen2.5-Coder o DeepSeek-R1 ejecutándose directamente en tu GPU local mediante el Bridge.

```json
{
  "models": [
    {
      "title": "Gravity Bridge V15.0 PRO",
      "provider": "openai",
      "model": "gravity-bridge-auto",
      "apiBase": "http://localhost:7860/v1",
      "apiKey": "gravity-local"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Gravity Autocomplete",
    "provider": "openai",
    "model": "gravity-bridge-auto",
    "apiBase": "http://localhost:7860/v1",
    "apiKey": "gravity-local"
  }
}
```

### 3. Ejecución Directa con Aider CLI
El bridge acelerado te permite co-programar en terminal consumiendo tus motores locales de forma gratuita y eficiente:
```bash
aider --openai-api-base http://localhost:7860/v1 --model openai/gravity-bridge-auto
```

---

## 📊 Códigos de Estado y Respuestas de Error

Todas las peticiones del Bridge devuelven códigos HTTP estándar y estructuras de error JSON autoexplicativas para facilitar el debugging en tus desarrollos:

| Código HTTP | Causa de la Respuesta | Estructura del Body |
|:---|:---|:---|
| `200` | OK — Petición procesada exitosamente | Estructura específica del endpoint |
| `400` | Bad Request — Parámetros inválidos o ausentes | `{"error": "Detalle del parámetro faltante"}` |
| `401` | Unauthorized — API key inválida o ausente | `{"error": "Acceso denegado: API key requerida"}` |
| `429` | Too Many Requests — Límite de Rate Limiting excedido | `{"error": "Too Many Requests. Límite de IP/Key superado", "retry_after": 60}` |
| `503` | Service Unavailable — Sin proveedores disponibles | `{"error": "No hay ningún motor de IA local o cloud disponible en este momento"}` |
| `500` | Internal Server Error — Excepción en el micro-kernel | `{"error": "Traceback interno del error en bridge_server.py"}` |

---

<div align="center">
  <sub><i>© 2026 DarckRovert · Gravity AI Bridge V15.0 PRO Omniscient-Tier · Centro de Desarrollo & API Nativos</i></sub>
</div>
