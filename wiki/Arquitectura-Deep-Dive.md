# 🏛️ Arquitectura y Flujo de Datos

**Gravity AI Bridge V16.2 PRO** está estructurado sobre un ecosistema de Daemons asíncronos en Python puro y un frontend SPA React en Vite.

## 1. El Orquestador Autónomo (`provider_manager.py`)
Es el corazón de Gravity. No importa si tienes LM Studio, Ollama, Jan AI o Claude; el orquestador los evalúa a todos simultáneamente mediante hilos asíncronos de bajo costo (con un timeout estricto de 8.0 segundos).
- **Enrutamiento por Heurística**: Si envías una tarea de `código`, el motor buscará activamente el nombre `coder` o `qwen` en tus modelos locales antes de asignar la carga de trabajo.

## 2. Bloqueos Asíncronos (Thread-Safety)
Para hardware unificado (APUs AMD, GPUs discretas con VRAM apretada), Gravity implementa `threading.RLock()` a nivel de clase en `NativeLlamaProvider`.
Esto significa que si invocas un debate entre 5 agentes en la pestaña "Multi-Agent", los 5 agentes solicitarán un modelo. Gravity pondrá en pausa a 4 de ellos, dejará generar al primero, y así sucesivamente sin saturar la VRAM.

## 3. Gestor de Memoria Turbo
Gravity inspecciona el tiempo transcurrido desde el último uso de cada motor (`last_used`). Si supera los 300 segundos, lo elimina activamente de la RAM e invoca el Recolector de Basura de Python (`gc.collect()`) para recuperar el 100% de la capacidad operativa del equipo.
