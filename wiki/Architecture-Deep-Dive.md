# 🏗️ Omni-Tier Architecture (Deep Dive) / Arquitectura Omni-Tier

Gravity AI V7.1 is a hybrid orchestrator that decouples the **interface** from the **inference engine**, allowing transparent multi-hardware orchestration.

Gravity AI V7.1 es un orquestador híbrido que desacopla la **interfaz** del **motor de inferencia**, permitiendo una orquestación multi-hardware transparente.

---

## 📡 Data Flow / Flujo de Datos

### [EN] Process
1. **Interceptor**: IDEs (Cursor/Aider) send requests to `localhost:7860/v1`.
2. **Omni-Audit Guard**: Requests are enriched with technical reasoning and prompt security checks.
3. **Provider Manager**: Selects the fastest engine (Ollama, LM Studio, or VLLM).
4. **Hardware Offloading**:
   - **LLM**: Executes on the GPU (Radeon 780M / NVIDIA).
   - **Embeddings (RAG)**: Offloaded to the **NPU (Ryzen AI)** via ONNX Runtime.
   - **Control**: CPU manages memory and orchestration.

### [ES] Proceso
1. **Interceptor**: IDEs (Cursor/Aider) envían peticiones a `localhost:7860/v1`.
2. **Omni-Audit Guard**: Las peticiones se enriquecen con razonamiento técnico y seguridad de prompt.
3. **Provider Manager**: Selecciona el motor más rápido (Ollama, LM Studio o VLLM).
4. **Hardware Offloading**:
   - **LLM**: Se ejecuta en la GPU (Radeon 780M / NVIDIA).
   - **Embeddings (RAG)**: Se descargan al **NPU (Ryzen AI)** mediante ONNX Runtime.
   - **Control**: El CPU gestiona la memoria y la orquestación.

---

## ⚛ Telemetry V7.1 / Telemetría V7.1

The `hardware_profiler.py` performs real-time scans of:
- **Shared/Dedicated VRAM**: Detects iGPU or dGPU.
- **Optimal Context**: Calculates `num_ctx` to avoid Out of Memory (OOM) errors.
- **NPU Accelerator**: Detects Windows PnP devices compatible with XDNA.

---

## ⚖️ Intellectual Property / Propiedad Intelectual
This project is owned by **DarckRovert**. Licensed under **PolyForm Non-Commercial 1.0.0**.

Este proyecto es propiedad de **DarckRovert**. Bajo Licencia **PolyForm No-Comercial 1.0.0**.

*Official Support:* [twitch.tv/darckrovert](https://www.twitch.tv/darckrovert)
