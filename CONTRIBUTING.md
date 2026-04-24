# Contribuir a Gravity AI Bridge

Gravity AI Bridge es un ecosistema privado **Omniscient-Tier** de DarckRovert. Las contribuciones externas son limitadas pero bienvenidas bajo las siguientes condiciones.

---

## Código de Conducta

Este proyecto se rige por el [Código de Conducta](CODE_OF_CONDUCT.md). Al participar, aceptas cumplirlo.

---

## ¿Cómo Contribuir?

### 1. Reportar Bugs
1. Verifica que el bug no esté ya reportado en [Issues](https://github.com/DarckRovert/Gravity_AI_bridge/issues).
2. Usa la plantilla `.github/ISSUE_TEMPLATE/bug_report.md`.
3. Incluye: versión del bridge, OS, pasos para reproducir, logs relevantes.

### 2. Solicitar Features
1. Usa la plantilla `.github/ISSUE_TEMPLATE/feature_request.md`.
2. Explica el caso de uso y el valor que agrega al ecosistema.
3. Las features que amplíen el core local-first tienen prioridad.

### 3. Pull Requests

**Antes de hacer un PR:**
- Discute el cambio en un Issue primero.
- Asegúrate de que el cambio no rompe la filosofía Local-First.

**Proceso:**
```bash
# 1. Fork del repositorio
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge

# 2. Crear rama con nombre descriptivo
git checkout -b feat/nombre-de-la-feature

# 3. Instalar dependencias de desarrollo
pip install -r requirements.txt

# 4. Hacer cambios y validar sintaxis
python -m py_compile ruta/del/modulo.py

# 5. Ejecutar tests
cd tests && python -m pytest -v

# 6. Commit
git add .
git commit -m "feat: descripción concisa del cambio"

# 7. Push y abrir PR
git push origin feat/nombre-de-la-feature
```

---

## Estándares de Código

### Python
- **Tipo explícito en todo**: `Dict[str, Any]`, `List[str]`, `Optional[str]`. Prohibido `Any` sin justificar.
- **Sin dependencias externas masivas**: Si tu contribución requiere Flask, FastAPI, o cualquier framework pesado, será rechazada. Usar stdlib.
- **Docstrings obligatorios** en clases y funciones públicas.
- **Encoding UTF-8** explícito en todos los `open()`.

### JavaScript (Dashboard)
- Vanilla JS puro. Sin React, Vue, Angular.
- `async/await` sobre `.then()`.
- Siempre usar `esc()` para escapar contenido dinámico en el HTML.

### Commits
Usar [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` — Nueva funcionalidad
- `fix:` — Corrección de bug
- `docs:` — Solo documentación
- `refactor:` — Refactorización sin cambios funcionales
- `perf:` — Mejora de rendimiento
- `test:` — Tests

---

## Estructura del Proyecto

```
Gravity_AI_bridge/
├── bridge_server.py        # Entry point HTTP server
├── ask_deepseek.py         # CLI de agente IA (--role, --session)
├── config.yaml             # Configuración general
├── api/
│   ├── routes/
│   │   ├── mixin_get.py    # Todos los endpoints GET
│   │   └── mixin_post.py   # Todos los endpoints POST
│   └── state.py            # Estado global (rate limit, geoip)
├── core/                   # Módulos del ecosistema
│   ├── firecrawl_scraper.py
│   ├── hitl_manager.py
│   ├── session_runner.py
│   ├── mcp_adapter.py
│   ├── video_pipeline.py
│   └── ...
├── tools/                  # Herramientas standalone
├── rag/                    # Motor RAG
├── web/
│   └── dashboard.html      # Dashboard SPA completo
├── wiki/                   # Documentación extendida
└── installer/              # Scripts de instalación
```

---

## Qué NO Aceptaremos

- Cambios que introduzcan dependencias de cloud como requesito obligatorio.
- Modificaciones a la lógica de cifrado DPAPI de keys sin revisión de seguridad.
- Cambios en el Dashboard que rompan compatibilidad con navegadores modernos sin alternativa.
- PRs sin tests para módulos del `core/`.
- Código con `any` implícito en Python (sin tipado explícito).

---

## Contacto

- **GitHub Issues**: Para bugs y features.
- **Twitch**: [twitch.tv/darckrovert](https://twitch.tv/darckrovert) — Para discusiones sobre la arquitectura.
- **GitHub**: [github.com/DarckRovert](https://github.com/DarckRovert)

---

<div align="center">
  <sub><i>© 2026 DarckRovert · Gravity AI Bridge</i></sub>
</div>
