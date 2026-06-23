# 🔌 Referencia de la API REST

## 🗣️ Interfaz de Chat Universal
`POST /v1/chat/completions`
Formato compatible con OpenAI. Acepta `messages`, `temperature`, `max_tokens`.
Soporta `stream=True` nativamente.

## ⚡ Video Studio Pipeline
`POST /v1/video/create`
Desencadena la generación asíncrona de video MP4 o clips duales Híbridos GLSL.

## 📡 Control HITL (Human In The Loop)
- `GET /v1/hitl/pending`: Lista peticiones detenidas esperando aprobación humana.
- `POST /v1/hitl/approve`: Libera el comando retenido.
- `POST /v1/hitl/reject`: Aborta la ejecución de alto riesgo.

*(La documentación Swagger completa está embebida en el Dashboard bajo la pestaña System Status).*
