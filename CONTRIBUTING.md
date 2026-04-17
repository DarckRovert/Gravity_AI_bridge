# Guía de Contribución — Gravity AI Bridge V10.0

Gravity AI Bridge es un proyecto de código abierto activo. Cualquier contribución técnica es bienvenida, siempre que cumpla con los estándares establecidos a continuación.

---

## Antes de Empezar

1. **Lee el código** — Antes de añadir algo, entiende cómo funciona el módulo que vas a modificar. La [Arquitectura](wiki/Arquitectura.md) es el punto de partida.
2. **Busca issues existentes** — Tu idea o bug puede ya estar reportado o en progreso.
3. **Abre un issue primero** — Para cambios grandes (nuevos módulos, refactorizaciones), discútelo en un issue antes de escribir código.

---

## Configuración del Entorno

```bash
# 1. Fork del repositorio en GitHub, luego:
git clone https://github.com/TU_USUARIO/Gravity_AI_bridge.git
cd Gravity_AI_bridge

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Verificar que el bridge arranca
python bridge_server.py
# → http://localhost:7860 debe estar disponible

# 4. Crear una rama descriptiva
git checkout -b feat/nombre-descriptivo
# Ejemplos de nombres:
#   fix/watchdog-null-pointer
#   feat/panel-resource-monitor
#   docs/guia-api-ejemplos-curl
#   refactor/provider-manager-scan
```

---

## Estándares de Código

### Python
- **Type hints obligatorios** en todas las funciones y métodos públicos
- **PEP 8** — líneas máximo 100 caracteres, docstrings en módulos y clases
- **Sin `any` implícito** — los tipos deben ser explícitos. Usa `Optional[T]` en lugar de `T = None` sin tipo
- **Excepciones específicas** — nunca `except: pass`. Mínimo `except Exception as e: log.warning(...)`
- **Sin imports globales de dependencias opcionales** sin guard:
  ```python
  try:
      import psutil
      _PSUTIL_OK = True
  except ImportError:
      psutil = None
      _PSUTIL_OK = False
  ```

### Web Dashboard (`web/dashboard.html`)
- **Vanilla JavaScript y Vanilla CSS únicamente** — sin frameworks externos
- Toda nueva función fetch debe seguir el patrón `async function fetchXxx()` con `try/catch`
- Toda nueva sección de UI necesita su `nav-item` en el sidebar y su `panel-xxx` como `<div id="panel-xxx" class="panel">`
- El panel debe llamar a su función de carga en `switchTab()` y en `refreshAll()`

### Shell / BAT
- Todos los pasos deben tener su étiqueta `echo [N/X] Descripción...`
- Cada paso crítico debe verificar `%errorlevel%` y mostrar mensajes de error en español

### WoW Lua (addons asociados)
- **Lua 5.0 estricto** — prohibido `#tabla`, `math.huge`, `table.unpack` y cualquier función de Lua 5.1+
- Sigue la TOC version presente en el archivo `.toc` del addon — nunca asumir la versión

---

## Proceso de Pull Request

### 1. Checklist antes de abrir el PR

- [ ] El código sigue los estándares técnicos de este documento
- [ ] **Si añades un endpoint nuevo** → está registrado en `do_GET` o `do_POST` y tiene su panel/widget en el Dashboard
- [ ] **Si añades un módulo nuevo** → está importado y arrancado en `run_server()` si es un servicio background
- [ ] Los mensajes de log usan el logger existente (`from core.logger import log`) — no `print()` en producción
- [ ] Si el cambio afecta la API → actualizaste `wiki/Guia-API.md`
- [ ] Si el cambio añade funcionalidad visible → actualizaste `wiki/Manual-Usuario.md`
- [ ] El commit message sigue la convención semántica (ver abajo)
- [ ] Has corrido el bridge y verificado que el Dashboard carga sin errores de consola

### 2. Convención de Commits

```
tipo(scope): descripción corta en imperativo

Tipos válidos:
  feat      → Nueva funcionalidad
  fix       → Corrección de bug
  docs      → Solo documentación
  refactor  → Refactorización sin cambio de comportamiento
  perf      → Mejora de rendimiento
  test      → Añadir o corregir tests
  build     → Scripts de build, installer, dependencias
  chore     → Mantenimiento, .gitignore, CI

Ejemplos:
  feat(dashboard): añadir panel de Resource Monitor con CPU/RAM en tiempo real
  fix(watchdog): corregir null pointer cuando no hay ningún proveedor activo
  docs(api): añadir ejemplos curl para /v1/agent/compare
  build(installer): añadir paso 0 para generar el .ico automáticamente
```

### 3. Qué esperar tras abrir el PR

- **Revisión en 48-72 horas** (tiempo estimado)
- Si hay correcciones solicitadas, aplícalas en la misma rama — no abras un PR nuevo
- Los PRs con conflictos de merge no resueltos no serán mergeados
- Los PRs sin descripción ni checklist completo pueden ser cerrados sin revisión

---

## Reporte de Bugs

Usa la plantilla de **Bug Report** en los issues de GitHub. Incluye obligatoriamente:

1. **Versión exacta** del Bridge (visibls en el título del CHANGELOG)
2. **Sistema Operativo y versión** — Windows 10 1803, Windows 11 23H2, etc.
3. **Proveedor de IA** activo al momento del error — Ollama, LM Studio, Anthropic, etc.
4. **Log relevante** — fragmento de `_audit_log.jsonl` o del output de la terminal
5. **Pasos exactos para reproducir** — tan detallados que otra persona pueda reproducirlo en 5 minutos

Sin esta información el issue puede ser cerrado por falta de datos.

---

## Sugerencias de Funcionalidades

Usa la plantilla de **Feature Request**. Describe:
- El problema que resuelve (no la solución en sí)
- Cómo encaja con la arquitectura Local-First existente
- Si rompe compatibilidad con versiones anteriores o la API pública

---

## Estructura de Módulos — Dónde Añadir Qué

| Tipo de cambio | Archivo(s) a modificar |
|:---|:---|
| Nuevo proveedor de IA | `providers/local/` o `providers/cloud/` + `provider_manager.py` |
| Nuevo endpoint GET | `bridge_server.py` → `do_GET routes` + handler `_serve_xxx()` |
| Nuevo endpoint POST | `bridge_server.py` → `do_POST routes` + handler `_handle_xxx()` |
| Nuevo panel del Dashboard | `web/dashboard.html` → nav item + panel HTML + función JS + `switchTab()` + `refreshAll()` |
| Nuevo módulo background | `core/nuevo_modulo.py` + import + `nuevo_modulo.start()` en `run_server()` |
| Nueva herramienta del agente | `tools/nueva_tool.py` + actualizar panel Tools en el Dashboard |
| Nueva dependencia | `requirements.txt` + sección **Dependencies** en `CHANGELOG.md` |

---

*Al contribuir, aceptas que tu código quedará bajo la [Licencia MIT](LICENSE) del proyecto.*

**Autor:** [DarckRovert](https://github.com/DarckRovert) · [twitch.tv/darckrovert](https://twitch.tv/darckrovert)
