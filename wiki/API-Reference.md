# Referencia de API (Gravity AI Bridge)

Esta referencia técnica está orientada a desarrolladores que desean integrar extensiones u otras aplicaciones con la arquitectura **Gravity V16.5**.

## Endpoints Nativos

El `bridge_server.py` expone un micro-servidor local que procesa interacciones asíncronas con agentes, subagentes y la base de datos de historial (`gravity_brain.db`).

### 1. `POST /api/chat`
Envía un prompt a la inteligencia principal (o sub-enjambre) para su ejecución autónoma.
- **Payload:** `{"message": "string", "session_id": "string", "bg_mode": bool}`
- **Respuesta:** Event-stream de texto o JSON con el estatus de la tarea.
- **Seguridad:** Sujeto a la intercepción del `HITLManager`.

### 2. `GET /api/status`
Recupera el estado en tiempo real del motor (Idle, Thinking, Wait-for-User, Executing Tool).
- **Respuesta:** `{"status": "string", "active_tasks": int}`

### 3. `POST /api/hitl/approve`
Punto de entrada de validación desde el Frontend para liberar una herramienta suspendida por el *AgentShield*.
- **Payload:** `{"approval_id": "string", "decision": "approve|reject"}`
- **Respuesta:** `200 OK`

## Módulo de Herramientas (`core/tools_engine.py`)

Las herramientas expuestas al LLM están limitadas y protegidas por un esquema dinámico de permisos (*Ring 0*).

| Herramienta | Descripción | Protección (AgentShield) |
|-------------|-------------|-------------------------|
| `view_file` | Lee un archivo desde disco. | **Bloqueada** para `.env`. Purga Unicode oculta (Zero-Width). |
| `replace_file_content` | Reemplaza cadenas de texto. | **Bloqueada** para archivos de configuración, `.env` y el directorio `core/`. |
| `run_command` / `shell_exec`| Ejecuta comandos en PowerShell. | **HITL Obligatorio** - Espera aprobación asíncrona del admin. |
| `code_runner` | Ejecuta un script temporal. | **AST Sandbox** - Libre autonomía pero sin acceso de escritura o red. |
| `grep_search` | Búsqueda por palabra clave. | Validada por `_safe_path` (Bloqueo en `.env`). |

---
*Nota: Si estás creando un `hook` custom en `.agents/hooks/`, tu código correrá en un entorno no bloqueado por AST, por ello Gravity AI valida la firma criptográfica antes de cargar el módulo en el servidor.*
