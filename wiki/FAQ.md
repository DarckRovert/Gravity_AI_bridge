# 🪐 FAQ — Gravity AI Bridge V15.0 PRO
**Omniscient-Tier Edition** · [Reportar un bug](https://github.com/DarckRovert/Gravity_AI_bridge/issues) · [twitch.tv/darckrovert](https://twitch.tv/darckrovert)

---

## 📡 Instalación, Requisitos y Hardware

### ¿Necesito instalar Python para usar Gravity AI Bridge?
**No**, si descargas el instalador comercial standalone `.exe`. El paquete empaquetado mediante PyInstaller e Inno Setup contiene un entorno autocontenido de Python preconfigurado y todas las librerías binarias necesarias.

Si eres desarrollador o deseas modificar el comportamiento del micro-kernel, puedes realizar la instalación clásica clonando el repositorio y ejecutando `pip install -r requirements.txt`.

### ¿Necesito una GPU dedicada de gama alta para ejecutar el bridge?
No. El micro-kernel está diseñado para ser ultra-eficiente:
- **Solo CPU:** Funciona perfectamente con modelos locales cuantizados pequeños (ej: `gemma3:4b` o `qwen2.5-coder:7b`) a una velocidad de inferencia moderada.
- **iGPU AMD / Intel Arc:** Detecta y aprovecha la memoria gráfica compartida para acelerar los tensores de inferencia.
- **GPU NVIDIA (CUDA) o AMD (ROCm):** Rendimiento máximo optimizado. El bridge perfila el hardware al arrancar y habilita el soporte nativo correspondiente.

### ¿El asistente `build_installer.bat` requiere privilegios de administrador?
No para el proceso de compilación (PyInstaller). Sin embargo, el archivo ejecutable resultante (`Gravity_AI_Bridge_V15.0_Setup.exe`) sí requerirá permisos de administrador para poder copiar los binarios a `C:\Program Files\` y registrar los servicios del Launcher silencioso.

---

## 🧠 Inferencia y Proveedores de IA

### ¿Qué motores locales detecta de forma automática?
El micro-kernel escanea activamente los siguientes puertos estándar al arrancar:
- **Ollama:** Puerto `:11434`
- **LM Studio:** Puerto `:1234`
- **KoboldCPP:** Puerto `:5001`
- **Jan AI:** Puerto `:1337`
- **Lemonade:** Puerto `:8000` (Optimizado para ROCm)

Si cualquiera de estos motores está en ejecución, el bridge catalogará sus modelos y los expondrá como disponibles para su consumo inmediato.

### ¿Qué proveedores en la nube soporta el bridge?
Soporta integración nativa con Anthropic, OpenAI, Google Gemini, Groq y Mistral AI. Puedes ingresar las API keys de forma interactiva en la pestaña de configuración del Dashboard. Las claves se almacenan de forma segura cifradas con DPAPI de Windows.

### ¿Cómo funciona el Engine Watchdog y el auto-switch?
El Watchdog es un daemon en segundo plano que evalúa cada 30 segundos la disponibilidad y latencia (ping) de todos los motores activos.
- Si el modelo virtual `"gravity-bridge-auto"` está seleccionado, el bridge redirige tus peticiones al motor local más rápido y saludable.
- Si el proveedor local falla de forma consecutiva o experimenta una degradación severa, el Watchdog conmuta inmediatamente a un proveedor cloud de respaldo (ej: Gemini o Claude) en menos de 30 segundos para evitar cortes.
- Si fijas manualmente un modelo (ej: `/modelo deepseek-r1:14b`), el sistema entra en estado **LOCKED** y deshabilita el auto-switch hasta que presiones "🔓 Forzar Unlock" en el Dashboard.

---

## 🎬 Video Studio & Motor de Animación MAI

### ¿Qué diferencia a los niveles del Motor de Animación Inteligente (MAI)?
El pipeline de generación de video cuenta con tres tiers de renderizado cinematográfico para dar vida a las imágenes fijas:
- **Tier L0 (Estático):** Compila las imágenes tal y como son exportadas por el generador (ideal para previsualizaciones rápidas).
- **Tier L1 (Procedural):** Aplica transformaciones matemáticas dinámicas en tiempo real mediante filtros complejos de ffmpeg (`kenburns`, `parallax`, `shake`, `vignette_drift`). Es ultra-rápido y no consume recursos de GPU.
- **Tier L2 (Generativo AI):** Exporta el fotograma inicial a tu servidor de ComfyUI e invoca workflows generativos de interpolación de fotogramas (Stable Video Diffusion / AnimateDiff) para generar clips de video fluidos.

### ¿Qué ocurre si Fooocus no está en ejecución al crear un video?
El micro-kernel de video detectará que el puerto `:7861` no responde. Para evitar un fallo catastrófico del render y la interrupción del pipeline de ffmpeg, el sistema sustituirá automáticamente las imágenes de las escenas por fotogramas negros manteniendo la narración TTS y los subtítulos sincronizados funcionales.

---

## 💰 Monetización Pasiva y Publicación Autónoma

### ¿El Content Scheduler genera y sube videos en segundo plano?
Sí. Al activar el planificador autónomo, el sistema lee periódicamente el archivo de base de datos de nichos (`niches.json`), autogenera el syllabus del curso o tema programado, produce los videos en la cola y los distribuye de forma headless a YouTube (vía OAuth2 y Content API) y TikTok (vía Content API v2).

### ¿Cómo funciona el multiplicador de CPM `language_cloner`?
Cuando un video finaliza su producción en español, puedes enviarlo a `/v1/language/clone`. El sistema traducirá los guiones cinematográficos de forma asíncrona al inglés, portugués o francés, y sintetizará la voz narradora en esos idiomas manteniendo la misma pista de video base. Esto permite atacar mercados de alto CPM de forma instantánea sin costes de renderizado visual adicionales.

### ¿Dónde se configuran los enlaces de afiliación CPA?
Mediante el panel **Monetización Hub** (o el endpoint `/v1/affiliates/program/add`). Registras tu enlace, nombre del producto y un template de llamada a la acción (CTA) asignado a un nicho comercial. El `affiliate_manager` inyectará automáticamente estos enlaces en la caja de descripción de las subidas de YouTube y TikTok correspondientes al nicho del video.

---

## 📽️ OBS Studio y Overlays Gravity Spark

### ¿Cómo vinculo el bridge con mi OBS Studio para transmisiones en vivo?
1. En OBS Studio, ve a **Herramientas > Ajustes del servidor WebSocket**. Activa el servidor en el puerto `4455` y copia la contraseña.
2. Ingresa estas credenciales en el panel de configuración del Dashboard de Gravity.
3. El bridge mantendrá un cliente WebSocket persistente que te permitirá automatizar cambios de escenas, mute de audios y control de grabaciones desde la API.

### ¿Qué hace el generador de overlays Gravity Spark?
Utiliza la inteligencia del LLM local para generar al vuelo código HTML, hojas de estilo CSS y lógica JavaScript interactiva basándose en un prompt en lenguaje natural (ej: *"Crea un widget de barra de salud cyberpunk interactiva"*). El bridge escribe el archivo en disco, inicia un servidor web estático y añade de forma automática una Browser Source en la escena activa de tu OBS Studio.

---

## 🔐 Seguridad y Privacidad

### ¿Mis API keys están seguras si subo el código a GitHub?
Sí. El bridge **nunca almacena las API keys en texto plano** en sus archivos de configuración ni base de datos. Utiliza la API de Protección de Datos de Windows (DPAPI) para cifrar los tokens a nivel de kernel utilizando tu firma de cuenta de usuario del sistema operativo. Los datos cifrados solo pueden ser leídos en tu misma máquina y bajo tu usuario.

### ¿El micro-kernel de RAG envía mis documentos a servidores externos?
No. El proceso de parsing, segmentación lógica (chunking), generación de embeddings y almacenamiento vectorial se realiza de forma **100% local** en tu equipo mediante modelos locales integrados. Tus documentos nunca salen de tu máquina.

---

<div align="center">
  <sub><i>© 2026 DarckRovert · Gravity AI Bridge V15.0 PRO Omniscient-Tier · Centro de Soporte y Preguntas Frecuentes</i></sub>
</div>
