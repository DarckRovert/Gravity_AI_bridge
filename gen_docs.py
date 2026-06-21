import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

files_to_create = {
    "README.md": """# Gravity AI Bridge V16.0 PRO 🌌

![Gravity Shield](https://img.shields.io/badge/Gravity-Diamond_Tier-00BFFF?style=for-the-badge&logo=ai)
![Security Audit](https://img.shields.io/badge/Security-Audited_100%25-success?style=for-the-badge&logo=shield)
![Status](https://img.shields.io/badge/Status-Autonomo_Activo-4CAF50?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

Gravity AI Bridge es el núcleo de un ecosistema autónomo y de alto rendimiento. Actúa como el cerebro central (L0) que orquesta modelos de lenguaje locales (LM Studio, Ollama) y en la nube (Nvidia NIM, Groq, OpenAI), además de coordinar motores de generación visual (Fooocus L1) y motores de video avanzados (LTX Video L2).

> **Nota de Seguridad:** La versión V16.0 PRO ha pasado una rigurosa auditoría de código, erradicando vulnerabilidades de ReDoS y garantizando resiliencia absoluta contra fallos silenciosos en operaciones asíncronas y de Git.

## 🔥 Características Principales

- **Arquitectura Multinivel (L0, L1, L2):** Escalabilidad desde lógica de texto hasta renderizado de video 4K en paralelo.
- **Motor de Autonomía (OODA Loop):** Ciclos de retroalimentación autónomos (Observe, Orient, Decide, Act, Learn) que permiten a la IA autogestionar su presupuesto, seguridad y generación de contenido.
- **Reportero Autónomo:** Generación continua de artículos periodísticos subidos de forma automática a Netlify mediante Git.
- **Sincronización Transversal:** Interfaz WebSocket V2V para comunicación en vivo y panel de control web unificado.
- **Security Monitor & HITL:** Supervisión en tiempo real con intervención humana obligatoria (Human-in-the-Loop) para acciones de alto riesgo y control de presupuesto API.

## 🚀 Arranque Rápido

1. Asegúrate de tener Python 3.10+ y los requisitos instalados.
2. Ejecuta el archivo maestro desde PowerShell o CMD:
   ```bash
   .\\launchers\\INICIAR_TODO.bat
   ```
3. El dashboard principal se abrirá en `http://localhost:7860`.
4. El Agente Periodístico se iniciará de forma silenciosa en segundo plano.

## 📚 Documentación

Revisa la carpeta `/wiki` para entender a fondo la arquitectura, el modelo de datos y cómo extender los módulos del sistema.
""",

    "LICENSE": """MIT License

Copyright (c) 2026 DarckRovert

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",

    "CONTRIBUTING.md": """# Guía de Contribución para Gravity AI Bridge

¡Gracias por tu interés en contribuir al ecosistema de Gravity AI!

## Reglas Invariantes
Toda contribución de código debe respetar estrictamente las reglas invariantes definidas en `core/autonomy_engine.py`:
1. Nunca exceder límites de costo de API codificados.
2. No comprometer la arquitectura HITL (Human-in-the-Loop).
3. Todo debe ser compatible con la ejecución local (offline-first o fallback local garantizado).

## Proceso de Pull Requests
1. Haz fork del proyecto y crea tu rama (`feature/nueva-habilidad`).
2. Añade documentación en la carpeta `/wiki` si alteras la arquitectura L0/L1/L2.
3. Envía el PR detallando el consumo de recursos y tiempo de procesamiento.
""",

    "CODE_OF_CONDUCT.md": """# Código de Conducta de Gravity AI

El equipo y la IA detrás de Gravity se rigen por un principio básico de respeto, innovación y seguridad técnica.

1. **Colaboración Constructiva:** Fomentamos el desarrollo ético de sistemas autónomos.
2. **Reporte de Brechas:** Toda brecha de seguridad (loop infinito, escape de contenedor, filtración de API keys) debe reportarse a los administradores antes de publicarla.
3. **Respeto Mutuo:** No se tolerará acoso, discriminación o toxicidad en el entorno de desarrollo.
""",

    "SECURITY.md": """# Política de Seguridad

Este repositorio implementa salvaguardas avanzadas para el control de IA autónoma.

## Versiones Soportadas
Actualmente solo se brinda soporte de seguridad a la rama principal (Gravity V16.0 PRO).

## Reporte de Vulnerabilidades
Si encuentras una manera en la que el Motor de Autonomía de Gravity pueda eludir sus bloqueos (HITL o presupuesto), repórtalo directamente mediante un Issue privado o contactando al administrador. NO crees un Issue público si el problema expone claves de API en texto plano o permite RCE remoto sin autenticación.
""",

    ".github/ISSUE_TEMPLATE/bug_report.md": """---
name: Reporte de Bug
about: Crea un reporte para ayudarnos a mejorar la estabilidad de Gravity.
title: "[BUG] "
labels: bug
assignees: DarckRovert
---

**Descripción del Bug**
Una descripción clara de lo que falló.

**Logs de Error**
Si aplica, pega aquí la salida de error (elimina claves de API):
```log
```

**Contexto del Entorno**
- OS: [ej. Windows 11]
- Motor: [ej. Llama 3.3, Ollama, etc]
- Puerto afectado: [ej. 7860, 7861]
""",

    ".github/ISSUE_TEMPLATE/feature_request.md": """---
name: Solicitud de Feature
about: Sugiere una nueva idea para el ecosistema Gravity.
title: "[FEATURE] "
labels: enhancement
assignees: DarckRovert
---

**Descripción de la Feature**
Explica tu idea y cómo encaja en la arquitectura L0, L1 o L2 de Gravity.
""",

    "wiki/Home.md": """# Wiki de Gravity AI Bridge 📚

Bienvenido a la Wiki Oficial del ecosistema **Gravity AI Bridge V16.0 PRO**.

## Índice de Contenidos

- [Arquitectura Profunda (Deep Dive)](Architecture-Deep-Dive.md)
- [Referencia de API y Módulos](API-Reference.md)
- [Troubleshooting y FAQs](Troubleshooting-and-FAQ.md)

Gravity es un puente de software que vincula sistemas de inteligencia artificial local con integraciones de nube híbrida, formando un sistema completamente autogestionable capaz de generar reportajes, audios y videos de alta calidad con intervención humana mínima.
""",

    "wiki/Architecture-Deep-Dive.md": """# Arquitectura Profunda (L0, L1, L2)

## Estructura de Capas

1. **L0: Cerebro y Coordinación (Gravity Bridge Server)**
   - Puerto `7860`.
   - Carga el entorno de Gradio (`bridge_server.py`) y el motor cognitivo (`gravity_brain.py`).
   - El Motor de Autonomía (`autonomy_engine.py`) opera aquí en un ciclo OODA de 6 horas, tomando decisiones sobre gasto, contenido y seguridad.

2. **L1: Motor de Renderizado Estático (Fooocus Studio)**
   - Puertos `7861` y `7862`.
   - Controla la API para la generación asíncrona de miniaturas y recursos gráficos.

3. **L2: Motor de Renderizado Dinámico (ComfyUI / LTX)**
   - Puerto `8188`.
   - Utilizado para animaciones pesadas y pipelines de contenido de video en lote.

## Reportero Autónomo
Un proceso demonio continuo (`news_daemon.py`) que:
1. Utiliza `gravity_reporter.py`.
2. Busca temáticas usando herramientas de WebSearch.
3. Inyecta respuestas LLM en `news.json` en un repositorio independiente (`gravity-news-portal`).
4. Realiza sincronizaciones automáticas a través de `git commit` y `git push` a Netlify. Cuenta con control de idempotencia para evitar fallos si no hay cambios nuevos, garantizando un ciclo de ejecución continuo.
""",

    "wiki/API-Reference.md": """# Referencia de API

## `core/provider_manager.py`
Módulo clave para la comunicación con múltiples proveedores de LLM.
- `complete(messages, provider=None, model=None, options=None)`
- Conoce y enruta peticiones hacia LM Studio local, Ollama, Nvidia NIM, Groq, y OpenAI, con manejo de fallback en caso de `401 Unauthorized`.

## `core/autonomy_engine.py`
Núcleo del agente CEO.
- `run_ooda_cycle()`: Ejecuta la lectura del estado (Observe), clasifica alertas (Orient), determina acciones con LLM (Decide), ejecuta tareas de bajo riesgo (Act) y actualiza la base de conocimiento (Learn).

## `gravity_reporter.py`
Ejecución del periodista.
- Argumentos: `--topic "..."`, `--focus "..."`.
- Fallbacks automáticos entre motores.
""",

    "wiki/Troubleshooting-and-FAQ.md": """# Troubleshooting y FAQ

### 1. El portal de noticias tiene errores de decodificación JSON.
**Solución:** Revisa los logs de `task-*`. Puede ocurrir si un proveedor LLM falla y devuelve un JSON en un bloque markdown inesperado. El sistema ahora tiene un parche en `clean_llm_response()` para extraer y limpiar la salida.

### 2. Fooocus no arranca desde el `INICIAR_TODO.bat`
**Explicación:** Por defecto, Fooocus arranca en "modo manual" para ahorrar RAM (frecuentemente más de 12GB requeridos). Debes activarlo manualmente desde el Mission Control (L0).

### 3. Problemas de Push a Github en el Agente Periodístico
**Solución:** Verifica que el usuario local de Windows tenga las credenciales de Git cacheadas globalmente (`git config --global credential.helper wincred`).

### 4. Fallos al decodificar contenido de Web Search
**Explicación:** Si la búsqueda web retorna errores de Gzip o decodificación, revisa que no estés enviando headers de codificación (Accept-Encoding) incompatibles con `urllib`. La V16.0 PRO ya maneja esto limpiando cabeceras innecesarias.

### 5. Falla silenciosa al instalar faster-whisper
**Solución:** En V16.0 PRO, la instalación de dependencias como Whisper es de tipo "bloqueante" (`blocking`). Si notas errores de "módulo no encontrado" en la consola, verifica que el subprocess tenga permisos para instalar pip localmente sin detener la ejecución.
"""
}

# Add standard .gitignore
files_to_create[".gitignore"] = """
__pycache__/
*.py[cod]
*$py.class
.env
.venv/
env/
venv/
*.log
_keys/
*.bin
"""

for file_path, content in files_to_create.items():
    full_path = os.path.join(BASE_DIR, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Creado: {full_path}")

print("Toda la documentacion generada.")
