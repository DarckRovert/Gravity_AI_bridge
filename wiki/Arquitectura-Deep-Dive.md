# 🏛️ Arquitectura y Flujo de Datos

**Gravity AI Bridge V16.2 PRO** está estructurado sobre un ecosistema de Daemons asíncronos en Python puro y un frontend SPA React en Vite.

## 1. El Orquestador Autónomo (`provider_manager.py`)
Es el corazón de Gravity. No importa si tienes LM Studio, Ollama, Jan AI o Claude; el orquestador los evalúa a todos simultáneamente mediante hilos asíncronos de bajo costo (con un timeout estricto de 8.0 segundos).
- **Enrutamiento por Heurística**: Si envías una tarea de `código`, el motor buscará activamente el nombre `coder` o `qwen` en tus modelos locales antes de asignar la carga de trabajo.

## 2. Bloqueos Asíncronos (Thread-Safety)
Para hardware unificado (APUs AMD, GPUs discretas con VRAM apretada), Gravity implementa `threading.RLock()` a nivel de clase en `NativeLlamaProvider`.
Esto significa que si invocas un debate entre 5 agentes en la pestaña "Multi-Agent", los 5 agentes solicitarán un modelo. Gravity pondrá en pausa a 4 de ellos, dejará generar al primero, y así sucesivamente sin saturar la VRAM.

## 3. Gestor de Memoria Turbo & Memory Guard (`native_provider.py`)
Gravity inspecciona activamente el hardware utilizando `psutil` y evalúa el tiempo transcurrido desde el último uso de cada modelo (`last_used`):
- **Watchdog Dinámico Adaptativo**: Si la RAM libre del sistema baja de 2.5 GB o el porcentaje de uso supera el 88%, el watchdog reduce el timeout de inactividad de las IAs locales de 300 segundos a 15 segundos, descargando agresivamente las instancias inactivas.
- **Desalojo LRU Proactivo ante Carga**: Antes de cargar un modelo GGUF local, se estima el consumo en memoria a partir de su tamaño en disco. Si no hay suficiente RAM física libre, desaloja progresivamente del pool de instancias activas el modelo menos usado recientemente (LRU), llamando a `gc.collect()` para evitar OOMs (Out Of Memory).

## 4. Enrutamiento de Tareas Multicapa
El orquestador en `provider_manager.py` da soporte prioritario a tareas altamente especializadas:
- **Visión Multimodal**: Tareas de tipo `vision` se asignan con prioridad absoluta al modelo `llava-phi-3-mini-int4.gguf`.
- **Memoria Semántica & Embeddings**: Tareas de tipo `embedding` se asignan al modelo especializado `nomic-embed-text-v1.5.f16.gguf`.
- **Chats Tradicionales**: Se aplican penalizaciones cruzadas estrictas (de hasta -250) para evitar que modelos de embeddings o de visión sean cargados accidentalmente en interfaces de chat tradicionales.

