---
name: "\U0001F41E Bug Report"
about: Reportar un error técnico en Gravity AI Bridge
title: "[BUG] "
labels: bug
assignees: DarckRovert
---

## Descripción del Error

<!-- Descripción clara y concisa de lo que está fallando. -->

## Versión y Entorno

| Campo | Valor |
|:---|:---|
| Versión del Bridge | <!-- Ej: V10.0 Diamond-Tier --> |
| Sistema Operativo | <!-- Ej: Windows 11 23H2 --> |
| Python | <!-- Ej: 3.12.2 → `python --version` --> |
| Proveedor activo | <!-- Ej: Ollama, LM Studio, Anthropic --> |
| Modelo activo | <!-- Ej: qwen2.5-coder:32b --> |
| GPU | <!-- Ej: AMD RX 6800 XT 16GB ROCm / NVIDIA RTX 4090 / CPU Only --> |

## Pasos para Reproducir

1. Iniciar el bridge: `python bridge_server.py`
2. <!-- Paso 2 -->
3. <!-- Paso 3 -->
4. Ver el error

## Comportamiento Esperado

<!-- ¿Qué debería haber ocurrido? -->

## Comportamiento Real

<!-- ¿Qué ocurrió en cambio? -->

## Logs y Evidencia

<!-- Pega el fragmento relevante del output de terminal, del _audit_log.jsonl,
     o el error del Dashboard (F12 → Consola). Usa bloques de código: -->

```
Pega aquí el log
```

## ¿Ya intentaste?

- [ ] Reiniciar el bridge (`python bridge_server.py`)
- [ ] Verificar que el motor de IA está activo (Panel System Status → proveedor en verde)
- [ ] Revisar la [FAQ](https://github.com/DarckRovert/Gravity_AI_bridge/blob/main/wiki/FAQ.md)
- [ ] Buscar issues similares ya abiertos

## Información Adicional

<!-- Cualquier contexto adicional que pueda ayudar a reproducir el error. -->
