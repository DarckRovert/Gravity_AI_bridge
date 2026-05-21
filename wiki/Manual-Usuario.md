# 🪐 Manual de Usuario — Gravity AI Bridge V15.0 PRO
**Omniscient-Tier Edition** · [github.com/DarckRovert/Gravity_AI_bridge](https://github.com/DarckRovert/Gravity_AI_bridge) · [twitch.tv/darckrovert](https://twitch.tv/darckrovert)

---

## ¿Qué es Gravity AI Bridge?

Gravity AI Bridge es un **micro-kernel de IA y orquestador multi-agente** que actúa como un proxy universal compatible con el estándar OpenAI. Centraliza la inferencia de todos tus modelos locales (Ollama, LM Studio, etc.) y proveedores en la nube (Anthropic, OpenAI, Gemini, Groq, Mistral), exponiéndolos de forma segura, robusta y optimizada mediante una interfaz interactiva de **26 paneles React SPA**.

### Capacidades Exclusivas de la Versión V15.0 PRO:
- **Real-Time VTuber Engine V4.0 (Aletheia V2V):** Motor integrado basado en `FasterLivePortrait` con aceleración ONNX que permite animar avatares en caliente para transmisiones y videos sin penalización de hardware.
- **OBS Controller & Spark Engine:** Driver WebSocket v5 de OBS Studio para gestionar transmisiones y autogenerar Overlays adaptativos interactivos (Browser Sources) codificados en caliente por IA.
- **Suite de Monetización Pasiva Autónoma:** Content Scheduler integrado con nichos de mercado, inyección automática de enlaces de afiliados CPA, traductor y clonador de guiones en múltiples idiomas (`language_cloner`) y publicación desatendida a YouTube/TikTok.
- **Workers Asíncronos Multi-Sesión:** Motor de paralelización `session_runner.py` con señalización `CapacityWake` para ejecutar múltiples agentes asíncronos interactivos en subprocesos aislados sin colisionar el bridge principal.

---

## Instalación

### Para Usuarios Finales (Sin Dependencias de Python)
1. Descarga el paquete compilado comercial: `Gravity_AI_Bridge_V15.0_Setup.exe`.
2. Ejecuta el instalador con privilegios de administrador y completa el asistente Inno Setup.
3. El programa se instalará en `C:\Program Files\Gravity AI Bridge\` y creará un acceso directo en tu escritorio.
4. Al finalizar, el Launcher silencioso (`gravity_launcher.pyw`) arrancará en segundo plano e inyectará el icono de bandeja del sistema en tu barra de tareas de Windows.
5. Haz doble clic en el icono para abrir automáticamente el Dashboard interactivo en tu navegador.

### Para Desarrolladores (Modo Código Fuente)
```bash
# 1. Clonar el repositorio
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge

# 2. Instalar el entorno virtual y dependencias de Python
pip install -r requirements.txt

# 3. Compilar el Dashboard de producción React SPA
cd frontend
npm install
npm run build
cd ..

# 4. Asistente interactivo de instalación inicial
python INSTALAR.py

# 5. Arrancar el servidor del bridge
python bridge_server.py
```

### Requisitos Recomendados del Sistema
- **Sistema Operativo:** Windows 10/11 x64 (Build 1809 o superior).
- **Procesador:** CPU de 8 núcleos acelerado o NPU AMD Ryzen AI integrado.
- **Memoria RAM:** 16 GB mínimo (32 GB recomendado para modelos grandes).
- **Almacenamiento:** Unidad SSD con al menos 10 GB de espacio libre para caché y modelos locales.
- **Aceleradora Gráfica (GPU):** NVIDIA RTX (con soporte CUDA) o AMD Radeon RX (con soporte ROCm) con 8+ GB de VRAM dedicada. Funciona en modo CPU con degradación de latencia.

---

## Primeros Pasos (En 5 Minutos)

### Paso 1 — Inicializar Motores Locales
El Bridge brilla cuando orquesta motores de inferencia local. Asegúrate de instalar y configurar al menos un backend:
- **Ollama (Recomendado):** Instálalo desde la web oficial. Ejecuta en tu terminal `ollama pull qwen2.5-coder:7b` (o el modelo de tu preferencia) y arranca el servicio (`ollama serve`). El bridge lo detectará automáticamente en el puerto `:11434`.
- **LM Studio:** Descarga cualquier modelo compatible en formato GGUF e inicia el servidor de API local en el puerto `:1234`.

### Paso 2 — Validar el Estado de Telemetría
Abre el Dashboard en `http://localhost:7860`. Ve al panel **System Status**. Verás tu proveedor local marcado en color verde brillante con sus latencias de ping y modelos disponibles.

### Paso 3 — Iniciar el Auditor de Chat
Entra al panel **Chat Auditor** (💬), escribe cualquier duda técnica y presiona `Ctrl+Enter`. El bridge enrutará de inmediato la petición usando la regla de auto-switch optimizada por hardware.

---

## Guía Completa de los 26 Paneles del Dashboard

### 1. 💬 Chat Auditor
Interfaz principal de chat interactiva con streaming SSE. Auto-inyecta personalidad del archivo `_knowledge.json` y contexto vectorial RAG si están activos. Limpia bloques de razonamiento DeepSeek en vivo.

### 2. 🏠 Mission Control
Dashboard ejecutivo central. Muestra de un vistazo las peticiones del día, consumo financiero, CPU/GPU, colas en background y alertas de seguridad.

### 3. 🎨 Vision Studio
Generación de imágenes fotorrealistas mediante el motor local Fooocus. Permite ajustar prompts, resoluciones, estilos preestablecidos y configuraciones de rendimiento.

### 4. 🖼️ Image Queue
Gestión visual e historial de la cola de generación asíncrona de imágenes de Fooocus. Muestra estados detallados de cada job.

### 5. 🎥 Video Studio
Permite encolar peticiones de generación automatizada de videos multimedia a partir de un tema libre. Controla tiempos, pistas y narración.

### 6. 🎨 Image Lab (Pollinations)
Laboratorio de generación rápida en la nube usando el motor Flux vía Pollinations.ai. Permite descargar imágenes sin consumir VRAM.

### 7. 🎦 Largometraje
Variante avanzada de Video Studio diseñada para orquestar la generación paralela de videos de largo formato estructurados en hasta 100 escenas.

### 8. 🚀 Deploy
Interfaz conectada con `deploy_manager.py` para compilar proyectos web (`npm run build`) y subirlos a producción en Netlify de forma autónoma.

### 9. ⚔️ Game Servers
Panel de control para la suite vMaNGOS de World of Warcraft. Inicia/detiene procesos, envía comandos de consola SOAP y gestiona registros SRP-6a.

### 10. 🤖 Multi-Agent
Orquestador de comparación y votación paralela. Envía un prompt a múltiples LLMs locales y cloud simultáneamente y compara sus respuestas.

### 11. 🖥️ Hardware
Muestra información detallada de tu hardware: GPUs (NVIDIA/AMD), versión GFX para ROCm, VRAM real e iGPUs secundarias, calculando el tamaño máximo de contexto soportado.

### 12. 💰 Monetización Hub
Orquestador de la suite financiera pasiva. Gestiona enlaces de afiliación CPA, traducción TTS multilingüe y subidas Headless a redes.

### 13. 💰 Cost Center Center
Monitorea los consumos financieros de la API en USD. Muestra límites diarios, balance restante de tokens y costes desagregados por modelo cloud.

### 14. ⚡ Watchdog
Muestra el estado del Engine Watchdog. Permite liberar el bloqueo manual (`model_locked`) para reactivar la resiliencia y auto-switch.

### 15. 💾 Sessions
Permite visualizar las sesiones conversacionales persistentes guardadas en disco y spawnear sub-procesos agentes aislados.

### 16. 📚 RAG (Retrieval-Augmented Generation)
Monitorea el tamaño y la salud de la base de datos vectorial local. Muestra los chunks indexados y permite habilitar la inyección en el chat.

### 17. 🔌 MCP Servers
Muestra la lista de servidores Model Context Protocol (MCP) configurados e inspecciona visualmente sus herramientas y recursos expuestos.

### 18. 🛠️ Tools
Acceso directo para ejecutar de forma controlada comandos o scripts interactivos en el sandbox local de Python/Bash.

### 19. ⚡ Tools Pro
Variante extendida del sandbox con plantillas de scripts avanzados precargados para mantenimiento del sistema y auditoría de red.

### 20. 🕷️ Firecrawl Scraper
Extractor web inteligente. Escribe una URL y extrae su contenido transformado a Markdown limpio listo para ingerir.

### 21. 🛡️ HITL Approval
Consola de Human-in-the-Loop. El usuario puede aprobar o rechazar acciones de alto riesgo pendientes solicitadas por los agentes.

### 22. 🎭 VTuber Studio (V2V)
Permite gestionar tus avatares de VTuber. Inicia el servidor `FasterLivePortrait` y configura las imágenes base y videos conductores.

### 23. 📽️ OBS Controller
Driver interactivo conectado con OBS Studio. Cambia de escenas, altera el mute y el volumen del mezclador de audio y controla grabaciones.

### 24. 📡 System Status
Métricas de rendimiento y tiempos de respuesta. Muestra un gráfico interactivo con la telemetría histórica del servidor.

### 25. 📄 Audit Log
Visor interactivo del log de auditoría inmutable guardado en `_audit_log.jsonl`. Muestra latencias y costes de cada petición.

### 26. ⚙️ Configuración
Panel maestro. Permite guardar las API keys cifradas, modificar variables globales en caliente y auto-configurar IDEs (Cursor, Continue, Aider).

---

## CLI del Bridge — Referencia del Operador

Cuando interactúes a través del CLI de auditoría interactivo (`python ask_deepseek.py`), tienes a tu disposición los siguientes comandos maestros:

- `/guardar <nombre>` — Guarda de forma persistente el contexto conversacional activo.
- `/cargar <nombre>` — Carga una sesión guardada desde disco.
- `/fork <rama>` — Clona el contexto en una nueva rama sin modificar la principal.
- `/usar <proveedor>` — Bloquea el motor activo fijándolo a un proveedor (Ollama, LM Studio).
- `/auto` — Desbloquea el motor fijado y vuelve al auto-switch inteligente.
- `/buscar <consulta>` — Dispara una búsqueda web DuckDuckGo de alta velocidad sin API key.
- `/run <código>` — Ejecuta fragmentos de código Python de forma aislada en el sandbox.
- `/rag indexar <ruta>` — Genera embeddings vectoriales locales del archivo y los inyecta al índice.
- `/rag: <consulta>` — Realiza una consulta con inyección contextual vectorial.
- `!aprende <regla>` — Escribe una regla técnica de forma permanente en `_knowledge.json`.
- `!reglas` — Lista las reglas de personalidad y desarrollo activas.

---

## Preguntas Frecuentes (FAQ)

### ¿El bridge consume recursos si no lo estoy usando?
Prácticamente cero. El hilo principal del servidor web corre sobre `ThreadingHTTPServer` de forma ultra-ligera. Los subprocesos de los motores de IA (Ollama, LM Studio) se suspenden o gestionan de acuerdo con sus configuraciones de inactividad propias.

### ¿Cómo funciona el cifrado de API Keys con DPAPI?
El Bridge utiliza el driver de seguridad del kernel de Windows (DPAPI). La clave secreta se cifra utilizando la firma criptográfica del usuario actual de Windows. Esto significa que si alguien copia tus archivos de base de datos a otra máquina o los abre desde otro usuario, las credenciales serán ilegibles.

### ¿Puedo utilizar el RAG con archivos PDF pesados?
Sí. El motor de ingesta local fragmenta los archivos en chunks lógicos de tamaño adaptativo, genera los embeddings locales de alta fidelidad y los almacena en el índice SQLite persistente en la carpeta `_rag_index/`.

---

## Resolución de Errores Comunes

- **"No provider available":** Asegúrate de que tu motor local (Ollama en el puerto `:11434` o LM Studio en `:1234`) esté corriendo correctamente. Si usas un motor en la nube, valida que tu API key esté ingresada en el panel Configuración.
- **La vista de OBS no se conecta:** Abre los ajustes de WebSocket de OBS Studio, activa el servidor en el puerto `4455`, copia la contraseña e ingrésala en la sección correspondiente de `config.yaml` o mediante el panel Configuración.
- **Imágenes generadas en negro en Video Studio:** El motor de renderizado requiere que el servidor Fooocus esté corriendo activamente en el puerto `7861`. Si no está activo, el pipeline sustituirá las imágenes por fotogramas negros con el fin de evitar un fallo catastrófico de render en ffmpeg.
- **Fallo del instalador por PyInstaller:** Ejecuta `python make_icon.py` antes de compilar para generar el recurso multi-resolución `assets/gravity_icon.ico` obligatorio para el empaquetado del ejecutable standalone.

---

<div align="center">
  <sub><i>© 2026 DarckRovert · Gravity AI Bridge V15.0 PRO Omniscient-Tier · Centro de Operaciones e Infraestructura</i></sub>
</div>
