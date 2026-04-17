## Descripción

<!-- Explica los cambios realizados y el problema que resuelven.
     Sé específico: menciona los archivos modificados y por qué. -->

## Tipo de Cambio

- [ ] `fix` — Corrección de bug (no rompe la API)
- [ ] `feat` — Nueva funcionalidad (no rompe la API)
- [ ] `feat!` — Nueva funcionalidad que rompe compatibilidad (breaking change)
- [ ] `refactor` — Refactorización sin cambio de comportamiento
- [ ] `perf` — Mejora de rendimiento
- [ ] `docs` — Solo documentación
- [ ] `build` — Build, dependencias, CI

## ¿Qué afecta este PR?

- [ ] `bridge_server.py` — endpoints o routing
- [ ] `core/` — módulos del micro-kernel
- [ ] `providers/` — plugin de proveedor
- [ ] `web/dashboard.html` — UI del Dashboard
- [ ] `tools/` — herramientas del agente
- [ ] `rag/` — motor RAG
- [ ] `installer/` — build / Inno Setup
- [ ] `wiki/` — documentación

## Cómo Verificarlo

<!-- Pasos exactos para verificar que el cambio funciona correctamente.
     Incluye qué endpoint probar, qué panel del Dashboard revisar,
     o qué comando ejecutar. -->

1. Iniciar el bridge: `python bridge_server.py`
2. <!-- Paso de verificación -->
3. <!-- Resultado esperado -->

## Checklist

- [ ] El código sigue los estándares de [CONTRIBUTING.md](../CONTRIBUTING.md)
- [ ] Si añado un endpoint nuevo → está en el routing de `do_GET`/`do_POST` y en el Dashboard
- [ ] Si añado un módulo background → está llamado en `run_server()`
- [ ] No uso `print()` en producción — uso `from core.logger import log`
- [ ] He actualizado la wiki si el cambio afecta funcionalidad visible
- [ ] He verificado que el Dashboard carga sin errores en la consola del navegador (F12)
- [ ] El commit message sigue la convención semántica (`feat:`, `fix:`, `docs:`, etc.)

## Breaking Changes

<!-- Si este PR rompe compatibilidad con versiones anteriores (API, config.yaml, etc.),
     documenta exactamente qué cambia y cómo migrar. -->

_Ninguno_ <!-- o describe el breaking change aquí -->

## Screenshots / Evidencia (si aplica)

<!-- Para cambios visuales del Dashboard, adjunta capturas de pantalla. -->
