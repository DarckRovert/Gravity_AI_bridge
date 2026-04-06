# 📡 API Reference e Integración

Gravity AI Bridge emula el comportamiento de las herramientas estándar de OpenAI para integración sin fricciones.

## 🔗 Endpoints Principales
- **Base URL**: `http://localhost:7860/v1`
- **Chat Completions**: `/chat/completions` (Compatible con Cursor, Aider, Continue).
- **Models**: `/models` (Lista los modelos expuestos por tu hardware).

## 💬 Comandos de Terminal (Modo Senior)
Puedes disparar órdenes administrativas enviando la pregunta directamente:
- `!info`: Reporte técnico de hardware y modelos activos.
- `!scan`: Fuerza el redescubrimiento de Ollama, LM Studio y VLLM.
- `!indexar [ruta]`: Agrega archivos al motor RAG de búsqueda.
- `!modo audit [on/off]`: Activa o desactiva la inyección del protocolo de seguridad.

## 🛠️ Integración con Herramientas
### Cursor (IDE)
Configura un **Custom Model** en Cursor:
1. URL: `http://localhost:7860/v1`
2. API Key: `gravity-key` (Puede ser cualquier cadena).
3. Model Name: `gravity` (El bridge mapeará esto al mejor modelo de 26B o 70B disponible).

---
*Para solucionar problemas de conexión, visita: [Troubleshooting](Troubleshooting-and-FAQ.md)*
