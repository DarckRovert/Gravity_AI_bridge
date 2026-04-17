# 📡 Guía de API (REST) — Gravity AI Bridge

Gravity AI Bridge expone una API RESTful asíncrona que permite tanto al Dashboard oficial como a aplicaciones de terceros interactuar con el ecosistema. Por defecto, el servidor escucha en el puerto **7860**.

## 📍 Endpoints del Sistema

| Método | Endpoint | Descripción | Parámetros Clave |
| :--- | :--- | :--- | :--- |
| **GET** | `/` | Carga el Dashboard Web interactivo. | N/A |
| **GET** | `/v1/status` | Obtiene el estado de salud del Bridge y backends activos. | N/A |
| **GET** | `/v1/audit` | Devuelve el histórico de transacciones y costes de IA. | `limit` (opcional) |
| **POST** | `/v1/chat/completions` | Enrutador de inferencia compatible con OpenAI. | `messages`, `stream`, `model` |

## 🎮 Game Server Manager (Endpoints)

| Método | Endpoint | Descripción | Cuerpo (JSON) |
| :--- | :--- | :--- | :--- |
| **GET** | `/v1/gameserver/status` | Estado de worldserver/realmd (MaNGOS). | N/A |
| **POST** | `/v1/gameserver/start` | Inicia el servidor de juego especificado. | `{"server": "wow_vanilla"}` |
| **POST** | `/v1/gameserver/stop` | Detiene el servidor de forma segura. | `{"server": "wow_vanilla"}` |
| **POST** | `/v1/gameserver/command` | Envía un comando SOAP al servidor de juego. | `{"server": "...", "command": "..."}` |
| **POST** | `/v1/gameserver/expose` | Aplica reglas de firewall y asocia IP WAN. | `{"public_address": "X.X.X.X"}` |

## 🛡️ Seguridad y Configuración

| Método | Endpoint | Descripción | Cuerpo (JSON) |
| :--- | :--- | :--- | :--- |
| **GET** | `/v1/security` | Reporte de integridad, puertos y alertas. | N/A |
| **POST** | `/v1/security/scan` | Fuerza un escaneo inmediato de procesos y archivos. | `{}` |
| **POST** | `/v1/keys` | Guarda una API Key en la bóveda cifrada (DPAPI). | `{"provider": "...", "key": "..."}` |

## 🚀 Despliegue (Deploy)

| Método | Endpoint | Descripción | Cuerpo (JSON) |
| :--- | :--- | :--- | :--- |
| **GET** | `/v1/deploy/status` | Estado del pipeline actual (building/idle/failed). | N/A |
| **POST** | `/v1/deploy` | Inicia el pipeline npm/netlify para un proyecto. | `{"project_path": "..."}` |

## 📝 Formato de Respuesta
Todas las respuestas (excepto el Dashboard HTML) se entregan en formato `application/json` con la siguiente estructura base:

```json
{
  "status": "success",
  "version": "10.0",
  "data": { ... },
  "timestamp": "2026-04-17T00:00:00Z"
}
```

---
*Referencia de API V10.0.*
