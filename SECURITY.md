# Política de Seguridad — Gravity AI Bridge

## Versiones Soportadas

| Versión | Estado | Soporte de Seguridad |
|---|---|---|
| V12.2 PRO Omniscient | ✅ Actual | Activo — recibe parches |
| V12.2 PRO Omniscient | ⚠️ Legacy | Solo vulnerabilidades críticas |
| V12.2 PRO | ❌ EOL | Sin soporte |
| V10.x | ❌ EOL | Sin soporte |

---

## Reportar una Vulnerabilidad

**NO abrir un Issue público para vulnerabilidades de seguridad.**

Reportar de forma privada:
1. **GitHub Private Advisory**: [Security Advisories](https://github.com/DarckRovert/Gravity_AI_bridge/security/advisories/new)
2. **Contacto directo**: [Twitch DarckRovert](https://twitch.tv/darckrovert)

### Información a Incluir
- Descripción clara de la vulnerabilidad
- Pasos para reproducir (PoC si aplica)
- Versión afectada
- Impacto estimado

**Tiempo de respuesta objetivo**: 48-72 horas para acuse de recibo, 7-14 días para evaluación.

---

## Modelo de Seguridad de Gravity AI Bridge

### 1. Autenticación y API Keys
- Las API keys (OpenAI, Anthropic, Firecrawl, etc.) se cifran con **DPAPI de Windows** via `core/key_manager.py`.
- Nunca se almacenan en texto plano en disco.
- `config.yaml` NO debe contener keys reales en repositorios públicos.

### 2. Anti-DDoS Local
- Rate limiting por IP: máximo 120 peticiones por ventana de tiempo configurable.
- Bloqueo inmediato vía HTTP 429 sin procesar el cuerpo de la petición.
- Implementado directamente en `BaseHTTPRequestHandler` (pre-parse).

### 3. HITL — Human in the Loop
Las siguientes tools requieren aprobación explícita del operador humano antes de ejecutarse:
- `code_runner`, `shell_exec`, `file_write`, `file_delete`
- `deploy`, `git_push`, `git_commit`
- `send_email`, `send_request`, `database_write`

El agente queda bloqueado 120 segundos esperando aprobación. Timeout → auto-rechazo.
**Excepción**: Modo background con permisos absolutos (requiere habilitación explícita).

### 4. Audit Log
- Todas las peticiones `/v1/chat/completions` y acciones de agente se registran en `_audit_log.jsonl`.
- Rotación automática al superar 5MB o 10,000 líneas.
- Los backups se mantienen como `.bak` con timestamp (máximo 3 backups rotativos).

### 5. Security Monitor (`core/security_monitor.py`)
- Whitelist dinámica de procesos benignos (Discord, Chrome, BattleNet, Steam, Spotify, etc.).
- Alertas CRITICAL/WARNING/INFO por proceso anómalo, puerto inesperado o modificación de archivo del sistema.
- GeoIP tracker de IPs externas con cache.
- Score de seguridad base 100 visible en el Dashboard.

### 6. Integridad del Servidor
- Pre-flight MySQL antes de arrancar MangosD (evita corrupción de Character-Files WoW).
- WAL Checkpoint de SQLite al arrancar (evita fuga de gigabytes en `.wal`).
- Validación de rutas con `..` (path traversal) en todos los endpoints de archivos estáticos.

### 7. Network Exposure
- Por defecto el servidor escucha en `0.0.0.0:7860`.
- **Recomendación**: En producción, proteger el puerto con firewall o proxy reverso (nginx/Caddy) con autenticación básica.
- El endpoint `/registro` (WoW account creation) solo debe estar accesible desde LAN.

---

## Vulnerabilidades Conocidas Mitigadas

| ID | Descripción | Estado |
|---|---|---|
| GAB-2026-001 | Falsos positivos en Image Queue (Fooocus) | ✅ Corregido V12.2 PRO |
| GAB-2026-002 | Spam de alertas de security_monitor por apps legítimas | ✅ Corregido V12.2 PRO |
| GAB-2026-003 | Path traversal en `/static/output/` | ✅ Mitigado V10.0 |
| GAB-2026-004 | Colisión de override `switchTab` en JS del Dashboard | ✅ Corregido V12.2 PRO |

---

## Scope de Seguridad

### En Scope (reportar)
- Ejecución remota de código (RCE) via endpoints
- Escalación de privilegios local
- Exposición no autorizada de API keys almacenadas
- Bypass del sistema HITL
- Path traversal / Directory traversal
- Inyección SQL en bases SQLite

### Fuera de Scope
- Vulnerabilidades en dependencias de terceros (Ollama, LM Studio, Fooocus) — reportar directamente a sus repositorios
- Ataques que requieren acceso físico al equipo
- Vulnerabilidades en el servidor WoW (MangosD/vMaNGOS) — fuera del ámbito del bridge

---

<div align="center">
  <sub><i>© 2026 DarckRovert · Gravity AI Bridge Security Policy</i></sub>
</div>
