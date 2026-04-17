# Política de Seguridad — Gravity AI Bridge V10.0

## Versiones con Soporte de Seguridad

| Versión | Soporte activo |
|:---|:---|
| **10.x (Diamond-Tier)** | ✅ Sí — versión actual con soporte completo |
| 9.3.x | ⚠️ Solo fixes críticos hasta 2026-07-01 |
| < 9.3 | ❌ Sin soporte — actualiza a V10.0 |

---

## Reporte de Vulnerabilidades

Si descubres una vulnerabilidad de seguridad en Gravity AI Bridge, **no abras un Issue público**. Un Issue público da tiempo a actores maliciosos antes de que el fix esté disponible.

### Proceso de divulgación responsable

1. **Envía el reporte por privado:**
   - GitHub: Usa la función [Security Advisory](https://github.com/DarckRovert/Gravity_AI_bridge/security/advisories/new) del repositorio (pestaña Security → Report a vulnerability)
   - Email alternativo: Mensaje directo via [Twitch](https://twitch.tv/darckrovert)

2. **Incluye en tu reporte:**
   - Descripción del fallo con clasificación tentativa (CVSS si es posible)
   - Pasos exactos para reproducirlo
   - Versión del Bridge afectada
   - Impacto potencial (qué puede hacer un atacante)
   - Proof of Concept (script, curl command, etc.) si lo tienes

3. **Respuesta esperada:**
   - **Confirmación de recepción:** en menos de 24 horas
   - **Evaluación y clasificación:** en menos de 72 horas
   - **Fix y release:** depende de la severidad (crítico: < 7 días, alto: < 30 días)

4. **Crédito:** El descubridor será mencionado en el CHANGELOG y en el Security Advisory de GitHub, si lo desea.

---

## Modelo de Seguridad de V10.0

### DPAPI — Cifrado de credenciales

Todas las API keys de proveedores cloud se cifran usando **Windows DPAPI (Data Protection API)**. La clave de cifrado está vinculada a la identidad del usuario del sistema operativo:

- Las keys **no se almacenan en texto plano** en ningún archivo del repositorio ni en disco
- Solo el mismo usuario de Windows en el mismo equipo puede descifrar las keys
- Si se copia el proyecto a otro equipo o usuario, las keys deben re-configurarse
- Implementación: `core/key_manager.py` → función `save_key()` y `load_key()`

### Rate Limiting

El Bridge implementa control de acceso por IP y por API key:

```yaml
# config.yaml
security:
  rate_limit:
    requests_per_minute: 60     # por IP
    burst_size: 10              # ráfaga permitida
  allowed_keys: []              # vacío = sin restricción de key
```

Las IPs que superan el límite reciben `429 Too Many Requests`. El historial de bloqueos se muestra en el panel **Security** del Dashboard.

### Zero-Trust Monitor

`core/security_monitor.py` corre como hilo daemon desde el arranque del Bridge. Detecta:

- Patrones de acceso anómalos (muchos requests en poco tiempo desde la misma IP)
- Intentos de acceder a endpoints no documentados (`404` repetidos)
- Headers malformados o payloads inusualmente grandes

Las alertas se almacenan en memoria y se exponen en `GET /v1/security`.

### Audit Log

`_audit_log.jsonl` registra **cada petición** con timestamp, IP, proveedor, modelo, tokens y coste. El archivo es de solo-append — no se puede modificar retroactivamente. Útil para auditorías de uso y detección de abuso.

### Aislamiento de Procesos

Los motores de IA (Ollama, LM Studio, etc.) corren como procesos separados del Bridge. El Bridge solo se comunica con ellos via HTTP local. No hay acceso directo a la memoria ni al filesystem de los modelos desde el Bridge.

---

## Superficie de Ataque y Mitigaciones

| Vector | Riesgo | Mitigación |
|:---|:---|:---|
| Acceso no autorizado al Dashboard | Si el puerto 7860 es accesible desde internet sin auth | Configura `allowed_keys` en `config.yaml` |
| Robo de API keys cloud | Si alguien accede al sistema de archivos | DPAPI — keys cifradas con identidad del usuario |
| Inyección de prompts | Manipulación del system prompt via API | El `_knowledge.json` solo se inyecta si no hay system prompt en la petición |
| Rate limit abusivo | Uso masivo que impacte el quotas cloud | Rate limiter por IP + límite diario en USD configurable |
| Exposición de puertos WoW | Puertos 3724/8085 accesibles sin intención | El Bridge solo abre estos puertos cuando se usa explícitamente `exposeWan()` |

---

## Qué NO hace el Bridge en materia de seguridad

Para establecer expectativas realistas:

- **No cifra el tráfico HTTP** entre el cliente y el Bridge — se asume red local de confianza. Para acceso remoto seguro, usa un reverse proxy con HTTPS (Nginx, Caddy).
- **No autentica usuarios del Dashboard** — el Dashboard es accesible para cualquiera que pueda llegar al puerto 7860. Restringe el acceso a nivel de red o configura `allowed_keys`.
- **No valida el contenido de los prompts** — el Bridge enruta el contenido tal como llega. La moderación de contenido es responsabilidad del modelo de IA o del cliente.

---

*Gravity AI Bridge V10.0 — Política de Seguridad*
*Mantenido por [DarckRovert](https://github.com/DarckRovert)*
