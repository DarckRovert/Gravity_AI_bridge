# 🪐 Arquitectura Deep Dive (Gravity Bridge Total Ecosistema)

El core funcional de la versión `V10.1 Stable` se sustenta bajo múltiples hilos interactuando sin fricciones globales (Global Interpreter Locks relajados al instanciarse subprocesos puros). Esta documentación detalla los módulos internos omitidos tradicionalmente.

## Visión Genérica de Instanciación

Al ejecutar el `bridge_server.py`, en el punto de entrada principal `run_server()` sucede esta detonación sincronizada:
1. Se levanta el scan asincrono (`background_scanner`) que hace autodiscovery continuo de puertos LLM. 
2. Se inician módulos pasivos: `security_monitor`, `image_queue`, `engine_watchdog`. Todos acoplados pasivamente con `threading.Thread(daemon=True)`.
3. Se invoca **PRAGMA** SQL en el caché viejo para cortar memory links residuales.
4. El servidor `ThreadingHTTPServer` finalmente amarra el OS en el puerto `7860`.

---

## Disección Analítica de Módulos Core

### 1. Sistema Multi-Entidad (`core/multi_agent.py`)
No lidias con 1 sola inteligencia a la vez. Cuando mandas un Query hacia la ruta `POST /v1/agent/compare`:
- La librería asimila y detecta mediante el **Provider Manager** cuántas inteligencias tiene vivas alrededor del Bridge (Ej. Mistral en un puerto 11434 y Llama en el 1234).
- Desencadena las peticiones usando sub-procesos aislados. 
- Bajo modo `parallel` el bridge devuelve los N resultados juntos, permitiendo debug humano de las capacidades LLM frente a tu query. Bajo modo `vote` el puente autocomputa internamente basándose en keywords extraídas del Reasoning Mode y expulsa la evaluación unificada. 

### 2. Procesador Heurístico (`core/reasoning_stripper.py`)
Dado el nacimiento de hardware y software agnóstico en el sector "Open Source", los nuevos modelos de IA escupen un pensamiento latente interno (Tokenizado bajo tags `<think>` o `<thought>`). DeepSeek es el mayor infractor de estos outputs basura. 
El puente se adhiere en su función `process_chunk(raw_text)` para analizar en vivo via regex la cadena temporal y estipar violentamente su formato hasta dejar un string limpio inyectable al DOM HTML o al chat web del panel.

### 3. VRAM Environment Optimizer (`core/env_optimizer.py`)
Acoplado brutal a las capas del OS Host para eludir "Out of Memory Errors": 
El script mapea el `core/hardware_profiler.py` evaluando la VRAM que le reporta la CLI de `wmic`, `nvidia-smi` o `rocm-smi` instalada. Una vez la obtiene, el gestor del Bridge hace sobreescritura termal en las variables `num_ctx`, inflando o disminuyendo el tamaño de Context Window de Ollama para garantizar que la VRAM nunca haga techo (Overhead prevention).

### 4. Sistema RAG de Contexto Ampliado (`_rag_index/`)
Para nutrir de lógica particular de Game Server, scripts y documentación a la IA (Que no posee por defecto en su pesos locales), Gravity expone la ruta `v1/rag/status`. 
El módulo escanea `json` generados asimétricos con incrustaciones en la memoria subyacente. Permite a futuros sub-ensambles vectoriales localizar por proximidad trozos de manual si un operador local hace consultas.

### 5. Control de Gastos & Facturación Local (`core/cost_tracker.py`)
Incluso a Nivel Diamante Privado, la telemetría es exigente. Si algún integrador habilita Cloud LLMs, el motor captura cada Token y formula un ticket en `_cost_log.json`. Al exceder las barreras por turnos o diarias de `session_cost`, trunca de raíz las peticiones HTTP subsiguientes hacia los providers con el prefijo "Cloud" y devuelve código de Límite Alcanzado. Previene sorpresas en tarjetas y recursos.

> [!NOTE]
> Gravity AI Bridge V10.1 elimina cualquier necesidad de aplicaciones terciarias y acopla subprocesamiento en un panel web base de bajo perfil bajo un ecosistema único con coherencia unificada.
