# 📡 API Reference & Integration / Referencia e Integración

Gravity AI Bridge emulates OpenAI's standard behavior for frictionless integration. This document details the endpoints and technical commands.

Gravity AI Bridge emula el comportamiento de las herramientas estándar de OpenAI para integración sin fricciones. Este documento detalla los endpoints y comandos técnicos.

---

## 🔗 Main Endpoints / Endpoints Principales

- **Base URL**: `http://localhost:7860/v1`
- **Chat Completions**: `/chat/completions` (Compatible with Cursor, Aider, Continue).
- **Models**: `/models` (Lists the models exposed by your hardware / Lista los modelos expuestos por tu hardware).

---

## 💬 Terminal Commands / Comandos de Terminal

### [EN] Senior Mode Commands
You can trigger administrative tasks by sending the direct query:
- `!info`: Technical report on hardware and active models.
- `!scan`: Force discovery of Ollama, LM Studio, and VLLM.
- `!index [path]`: Add files to the RAG search engine.
- `!audit [on/off]`: Enable or disable the security protocol injection.

### [ES] Comandos de Modo Senior
Puedes disparar órdenes administrativas enviando la pregunta directamente:
- `!info`: Reporte técnico de hardware y modelos activos.
- `!scan`: Fuerza el redescubrimiento de Ollama, LM Studio y VLLM.
- `!indexar [ruta]`: Agrega archivos al motor RAG de búsqueda.
- `!modo audit [on/off]`: Activa o desactiva la inyección del protocolo de seguridad.

---

## 🛠️ Tool Integration / Integración con Herramientas

### Cursor (IDE)
1. Set a **Custom Model** in Cursor.
2. URL: `http://localhost:7860/v1`
3. API Key: `gravity-key` (Any string works).
4. Model Name: `gravity` (The bridge maps this to the best available 26B/70B model).

---

## ⚖️ Intellectual Property / Propiedad Intelectual
This project is owned by **DarckRovert**. Licensed under **PolyForm Non-Commercial 1.0.0**.

Este proyecto es propiedad de **DarckRovert**. Bajo Licencia **PolyForm No-Comercial 1.0.0**.

*Official Support:* [twitch.tv/darckrovert](https://www.twitch.tv/darckrovert)
