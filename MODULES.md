# 📦 Gravity Module Map / Mapa de Módulos V7.1

Understand the project's internal structure and file responsibilities.
Entiende la estructura interna del proyecto y las responsabilidades de los archivos.

---

## 🏗️ Core Architecture / Arquitectura Central

### [EN] Files
- `bridge_server.py`: The heart. OpenAI-compatible API server.
- `hardware_profiler.py`: Hardware discovery (CPU/GPU/NPU).
- `key_manager.py`: Secure API key encryption (DPAPI).
- `model_selector.py`: Logic for choosing the best provider.

### [ES] Archivos
- `bridge_server.py`: El corazón. Servidor API compatible con OpenAI.
- `hardware_profiler.py`: Descubrimiento de hardware (CPU/GPU/NPU).
- `key_manager.py`: Cifrado seguro de llaves API (DPAPI).
- `model_selector.py`: Lógica para elegir el mejor proveedor.

---

## 📦 Search & RAG / Búsqueda y RAG

### [EN] Engine
- `rag/retriever.py`: Semantic search and NPU acceleration (XDNA).
- `rag/chunker.py`: Intelligent code splitting.

### [ES] Motor
- `rag/retriever.py`: Búsqueda semántica y aceleración NPU (XDNA).
- `rag/chunker.py`: Fragmentación inteligente de código.

---

## ⚖️ Intellectual Property / Propiedad Intelectual
This project is owned by **DarckRovert**. Licensed under **PolyForm Non-Commercial 1.0.0**.

Este proyecto es propiedad de **DarckRovert**. Bajo Licencia **PolyForm No-Comercial 1.0.0**.

*Official Support:* [twitch.tv/darckrovert](https://www.twitch.tv/darckrovert)
