# 🔌 Referencia Oficial de API del Sistema de Ecosistema Gravity

El puente procesa y levanta sus peticiones bajo HTTP puro local (`127.0.0.1:7860`). Diseñado con candados contra Rate-Limits y limitadores de sesión para estabilidad en entornos con latencia o alto tráfico.

## 📡 Eje de Control y Telemetría del Entorno

### `GET /v1/status`
Recopila el estado binario del Puente y lista el mejor proveedor LLM encadenado a la intranet en el momento (Modelos activos, conectividad a red).
### `GET /v1/hardware`
Extrae del Profiler información fidedigna de las Tarjetas Gráficas y NPU operativas que tu AI asume. Devuelve VRAM, Cores, Threads de CPU de tu servidor.
### `GET /v1/cost`
Devuelve el `session_cost`, `daily_limit` y métricas asociadas al gasto fraccionado e incesante de Tokens IN/OUT operados a la hora.
### `GET /v1/security`
Reporta pasivamente la sanidad operativa de todo subproceso (`security_monitor.py`), descartando por Whitelist interna y auditando si los puertos de fondo sufren injección intrusista, protegiendo Windows Server y World Of Warcraft Server.

## 🧠 Núcleo de Inteligencia Artificial

### `POST /v1/agent/compare`
Motor del Multi-Agent Orchestrator. 
- Acepta parámetros de `messages`, `n_models` y `mode: vote/parallel`.
- Devuelve las percepciones fraccionadas por N inteligencias artificiales concurrentes.

### `GET /v1/rag/status`
Analizador del Retrieval-Augmented Generation (Memoria vectorizada o asociativa del proyecto). Retorna documentos cargados, chunks particionados y peso vivo (MB) listos para ingestión por el LLM en consultas complejas sobre lore o códigos de servidor WoW.
### `GET /v1/sessions`
Lista de estados. Muestra cuantos historiales de conversaciones y "State Locks" tiene el modelo salvaguardado silenciosamente en su base circular interna.

## ⚔️ Game Server (World of Warcraft) y Utilidad Difusiva

### `POST /v1/gameserver/start` y `POST /v1/gameserver/stop`
Maneja directamente los triggers ejecutables compilados del MangosD y RealmD subyacentes. Internamente llama el validador MySQL para anulación antes-del-vuelo e invoca el *AutoBackup Dump* automático del DB Characters resguardado.

### `GET /v1/gameserver/log`
Retorna bajo Event-Deque la colección en vivo (Ram Buffer, 0 discos HDD/SSD gastados) de todo lo que el motor WoW escupe para visualización rápida anti-crash.
### `POST /v1/gameserver/register`
Inyección directa de cuenta con su SRP-6a para servidores MaNGOs, saltando burocracia de consolas In-Game y permitiendo altas HTTP encriptadas.

### `GET /v1/fooocus/status` y `GET /v1/queue`
Verifican el latir del ecosistema Difusor local en puerto `7861`, y consultan las colas de procesamiento paralelos en imagen. Fooocus ahora hace auto-verificación difusora diferencial (`diff` del archivo físico Output).
### `GET /v1/queue/stream`
Flujo puro **SSE Event-Stream Server**. La base para tu FrontEnd. Devuelve métricas `text/event-stream` del progreso asíncrono temporal sin requerir Pooling constante.

## 💻 Automatiza Deploy Remoto (FabricaWeb)

### `GET /v1/fabricaweb/status` y `POST /v1/fabricaweb/deploy`
El puente funciona de Pipeline CI/CD interno. Encripta tu WebApp de front-end alojada en `_integrations` tras leer dinámicamente tu framework desde el `package.json` (`/out`, `/dist`) e incrustándolo hacia hostings de netlify mediante tokens puros o repos locales.
