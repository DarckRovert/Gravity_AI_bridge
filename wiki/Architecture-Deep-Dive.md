# 🏗️ Arquitectura Omni-Tier (Deep Dive)

Gravity AI V7.1 es un orquestador híbrido que desacopla la **interfaz** del **motor de inferencia**, permitiendo una orquestación multi-hardware transparente.

## 📡 El Flujo de Datos
1. **Interceptor**: IDEs como Cursor o Aider envían peticiones a `localhost:7860/v1`.
2. **Omni-Audit Guard**: Las peticiones se enriquecen con instrucciones de razonamiento técnico y se verifica la seguridad del prompt.
3. **Provider Manager**: Selecciona el motor más rápido (Ollama, LM Studio o VLLM).
4. **Hardware Offloading**:
   - **LLM**: Se ejecuta en la GPU (Radeon 780M / NVIDIA).
   - **Embeddings (RAG)**: Se descargan al **NPU (Ryzen AI)** mediante ONNX Runtime.
   - **Control**: El CPU gestiona la memoria y la orquestación.

## ⚛ Telemetría V7.1
El `hardware_profiler.py` realiza un escaneo en tiempo real de:
- **VRAM Compartida/Dedicada**: Detecta si eres iGPU o dGPU.
- **Contexto Óptimo**: Calcula el `num_ctx` máximo para evitar desbordamiento de memoria (OOM).
- **Acelerador NPU**: Detecta dispositivos Windows PnP compatibles con XDNA.

---
*Para ver el API completo, visita: [API Reference](API-Reference.md)*
