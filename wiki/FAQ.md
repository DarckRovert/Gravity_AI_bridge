# ❓ FAQ — Gravity AI Bridge V16.0 PRO

Preguntas frecuentes y troubleshooting del ecosistema.

---

## 🚀 Instalación y Arranque

**P: El servidor arranca pero el Dashboard no carga.**
> Asegúrate de haber compilado el frontend: `cd frontend && npm install && npm run build`. El servidor sirve `frontend/dist/` como SPA. Si la carpeta no existe, verás sólo la API REST en JSON.

**P: `ModuleNotFoundError: No module named 'moderngl'`**
> El Motor GLSL V13 requiere moderngl. Instálalo con: `pip install moderngl moderngl-window`. Si usas GPU integrada Intel/AMD, asegúrate de tener los drivers más recientes con soporte OpenGL 3.3.

**P: El servidor dice `Address already in use` en el puerto 7860.**
> Otro proceso ocupa el puerto. Cámbialo en `config.yaml` → `port: 7861` o termina el proceso: `netstat -ano | findstr :7860` y luego `taskkill /PID <pid> /F`.

**P: `config.yaml not found`**
> El sistema crea automáticamente `config.yaml` copiando `config.yaml.example` en el primer arranque. Si no ocurre, hazlo manualmente: `copy config.yaml.example config.yaml`.

---

## 🎬 Video Studio

**P: El video se genera pero las escenas son solo negro.**
> El Motor GLSL necesita que OpenGL 3.3 Core esté disponible. En sistemas sin GPU dedicada, verifica que los drivers estén al día. En Intel: instala el Intel Graphics Driver más reciente desde `intel.com/drivers`.

**P: `iChannel0` sampler error — el render falla en el primer frame.**
> Este bug fue corregido en V16.0. El renderer ahora bindea incondicionalmente una textura fallback 1×1 negra a `iChannel0` antes de cada frame. Si ves este error, asegúrate de estar en la versión más reciente del `glsl_renderer_v13.py`.

**P: Pollinations tarda mucho o devuelve una imagen de 1px.**
> El sistema usa un cascading de 3 modelos con timeouts de 90s, 150s y 210s. Si todos fallan (red lenta o API saturada), activa el fallback procedural: el sistema genera una nebulosa fractal FBM en Numpy automáticamente. No requiere ninguna acción manual.

**P: Los Shorts no se generan / error "Audio no encontrado".**
> Corregido en V16.0 (`pipeline.py`). El pipeline ahora valida `os.path.isfile(temp_short_src)` antes de invocar FFmpeg. Asegúrate de estar en la última versión.

**P: Los subtítulos de los Shorts usan una fuente genérica fea.**
> El renderizador headless de Remotion (Chromium) necesita acceso a internet para descargar `Montserrat` e `Inter` de Google Fonts vía `@import url(...)` en `index.css`. Si el servidor no tiene internet, las fuentes harán fallback a `sans-serif` del sistema. Puedes pre-descargar las fuentes y referenciarlas localmente.

**P: El render de Shorts falla con error de Remotion/npx.**
> Asegúrate de tener Node.js 18+ instalado y las dependencias del workspace: `cd remotion_workspace && npm install`. El primer render puede tardar por la descarga de Chromium por Puppeteer.

---

## 🧠 LLM & Modelos

**P: Las respuestas son lentas aunque tengo GPU.**
> El sistema usa Turbo KV-Cache automáticamente cuando detecta Ollama: activa `OLLAMA_KV_CACHE_TYPE=q4_0` y `OLLAMA_FLASH_ATTENTION=1`. Verifica que Ollama esté corriendo con `ollama list` y que el modelo esté descargado localmente.

**P: Veo tokens `<think>...</think>` en las respuestas.**
> El Reasoning Stripper está activo por defecto para modelos DeepSeek-R1 y similares. Si no funciona, revisa `config.yaml` → `strip_reasoning: true`.

**P: El Multi-Agent voting devuelve siempre el mismo modelo.**
> El sistema de voting requiere al menos 2 modelos distintos. Verifica que los modelos seleccionados estén disponibles en tus backends configurados (`GET /v1/status`).

---

## 🔐 Seguridad & API Keys

**P: ¿Mis API keys están seguras?**
> Sí. Las keys se cifran con **Windows DPAPI** (vinculadas a tu sesión de usuario de Windows) y se almacenan en `_keystore.bin`. Nunca se escriben en texto plano en disco ni se envían a servicios externos.

**P: Olvidé mi API key de OpenAI, ¿puedo recuperarla del keystore?**
> No. El cifrado DPAPI es unidireccional desde la perspectiva del ecosistema. Para recuperarla, introdúcela de nuevo en el Dashboard → Configuración.

**P: El Security Score es bajo (< 70).**
> El monitor penaliza por: puertos inesperados abiertos, procesos sin firma digital, tasa de requests alta desde una IP. Revisa el panel `/security` para ver el desglose.

---

## 💰 Monetización

**P: El Language Cloner genera el audio pero el video final está mal sincronizado.**
> El clonador reutiliza el video original y reemplaza solo el audio. Asegúrate de que la pista de audio clonada tenga exactamente la misma duración que el original. El módulo `audio_processor.py` usa `atempo` de FFmpeg para ajustar velocidad si hay desviación < 20%.

**P: TikTok Uploader falla con error de autenticación.**
> La API de TikTok Content v2 requiere un token de acceso renovado periódicamente. Ve a `/monetization` → Social Distribution → Reconectar TikTok para refrescar el OAuth token.

---

## 🛠️ Desarrollo y Extensión

**P: ¿Cómo añado un nuevo estilo de shader al Video Studio?**
> 1. Crea tu Fragment Shader en `glsl_renderer_v13.py` como constante de string GLSL.
> 2. Asegúrate de declarar `uniform sampler2D iChannel0` para IBL.
> 3. Regístralo en el dict `SCENE_SHADERS` del mismo archivo con un nombre de clave único.
> 4. El Dashboard lo detectará automáticamente en el selector de estilos.

**P: ¿Cómo expongo un nuevo endpoint REST?**
> Crea un handler en `api/routes/handlers/` siguiendo la estructura de `video_handler.py`. Regístralo en `api/routes/mixin_get.py` o `mixin_post.py` según el método HTTP. Los handlers heredan CORS automáticamente.

**P: ¿Puedo usar el sistema en Linux/Mac?**
> El sistema está optimizado para Windows 10/11 (Windows DPAPI, SAPI TTS, MangosD). El Motor GLSL y Remotion funcionan en Linux, pero SAPI TTS y el cifrado de keys requieren adaptaciones. No hay soporte oficial para Linux/Mac en V16.0.
