# Política de Seguridad — Gravity AI Bridge

## Versiones Soportadas

| Versión | Soporte de Seguridad |
|---------|---------------------|
| 8.0.x   | ✅ Soporte activo    |
| 7.x     | ⚠️ Solo críticos     |
| < 7.0   | ❌ Sin soporte       |

## Reportar una Vulnerabilidad

**No reportes vulnerabilidades de seguridad en Issues públicos.**

### Proceso de Reporte

1. Describe la vulnerabilidad en detalle con pasos de reproducción.
2. Incluye la versión afectada y sistema operativo.
3. Indica el impacto potencial (confidencialidad, integridad, disponibilidad).
4. Envía el reporte como **Issue privado** en GitHub o mediante mensaje directo en [twitch.tv/darckrovert](https://twitch.tv/darckrovert).

### Tiempos de Respuesta

- **Acuse de recibo**: 48 horas.
- **Evaluación inicial**: 5 días hábiles.
- **Parche en versión soportada**: 30 días (crítico: 7 días).

## Consideraciones de Seguridad del Proyecto

### API Keys
- Las API Keys se almacenan cifradas con **DPAPI** (Windows) o en archivo `.keystore` con permisos 600 (Linux/macOS).
- **Nunca** se loggean en texto plano. El logger sanitiza cualquier token con patrón `sk-`/`key-`.
- Usa `/keys del` para eliminar claves del almacén cifrado.

### Bridge Server
- Por defecto solo escucha en `localhost` (configura `server.host` en `config.yaml` para exponer al exterior).
- Rate Limiting activo por IP y API Key.
- CORS restrictivo en producción; permisivo solo en desarrollo.

### Audit Log
- El archivo `_audit_log.jsonl` es **append-only** y no contiene contenido de mensajes, solo métricas.
- Elimina con precaución — es la única fuente de verdad para el seguimiento de costes.

### Recomendaciones de Despliegue
- No expongas el puerto 7860 directamente a Internet sin un proxy inverso (nginx/Caddy) con HTTPS.
- Configura `rate_limit.requests_per_minute` adecuado a tu uso en `config.yaml`.
- Revisa el audit log periódicamente para detectar uso anómalo.

---

*Gravity AI Bridge — [github.com/DarckRovert/Gravity_AI_bridge](https://github.com/DarckRovert/Gravity_AI_bridge)*
