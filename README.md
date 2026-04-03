# Gravity AI Bridge 🚀 (V4.0 God-Tier)

El **Gravity AI Bridge** ha evolucionado de un Auditor interactivo a un **ecosistema de IA completo y transparente** que auto-descubre, rankea, y enruta todos tus IDEs hacia el cluster de GPUs de tu sistema.

![Versión](https://img.shields.io/badge/Versión-4.0-cyan)
![Arquitectura](https://img.shields.io/badge/Architecture-God_Tier-magenta)
![Modelo](https://img.shields.io/badge/Model-Agnostic_Multi--Engine-yellow)

---

## 🔥 Características V4.0 (God-Tier)

*   **Auto-Descubrimiento Constante:** Nació con la habilidad de rastrear puertos. Si levantas `LM Studio` u `Ollama`, Gravity lo encuentra en < 2s, evalúa qué modelo tienes activamente residiendo en la VRAM para evitar latencias de cold-start, y te conecta al instante.
*   **Proxy Server Universal (El Bridge):** Contiene un mini-servidor (`bridge_server.py`) que engaña a cualquier editor de código del planeta (VSCode, Cursor, Aider, CodeGPT) creyendo que es la API oficial de OpenAI en `http://localhost:7860/v1`. 
*   **IDEs Auto-Configurados:** El comando `!integrar todo` escribe, inserta y acopla Gravity automáticamente dentro de los YAMLs de configuración de Continue.dev, Cursor y Aider de tu entorno.
*   **Inyección CLI Avanzada (Pipe Mode):** ¿Un error en la CMD? Simplemente tira por la tubería de sistema la instrucción: 
    `git diff | gravity "Analiza estos cambios"`
*   **Perfiles Temporales de Personalidad:** En caliente transiciona entre: `!modo coder`, `!modo revisor`, `!modo auditor`, `!modo creativo`.
*   **Compresión de Contexto Algorítmica:** Olvídate del límite de tokens. Cuando tu contexto base exceda el 85%, el Auditor pausa, procesa un resumen denso (`!comprimir`) y purga tu chat sin perder tus ideas, abriendo espacio infinito.
*   **Snapshots ("Save Games" de Memoria):** Guarda y restaura sesiones exactas para luego (`!guardar sesion_arquitectura`).

---

## 🛠️ Instalación rápida de un Toque

Olvídate de procesos manuales. Hay 10 pasos en 1 solo clic.

1. Simplemente haz doble clic sobre el script `INSTALAR.bat`.
2. Verás la secuencia visual en 10 pasos que evalúa hardware, instala dependencias, crea el icono global y configura Windows.

Y listo. Puedes llamarlo diciendo `gravity "hola"` globalmente donde sea.

---

## ⚡ Arsenal de Comandos Internos

En cualquier punto durante una sesión activa, el Auditor escucha:

| Inyección Avanzada | Acción de Sistema |
| :--- | :--- |
| `!scan` | Actualiza la tabla de mapeo de red de GPUs en caliente. |
| `/leer-carpeta <ruta>` | Analiza el source-code completo de un folder ignorando binarios. |
| `/leer-git` | Devora el `git diff HEAD` actual al instante. |
| `!guardar <nombre>` | Crea un archivo stateful inmutable de toda tu memoria. |
| `!saves` | Lista los snapshots. (`!cargar <nombre>` para revivirlos). |
| `!comprimir` | Si tu terminal pide auxilio por mucha charla, lo reseteas a bullet points sintéticos. |
| `!integrar continue` | Auto-crea el `config.yaml` perfecto dentro de `.continue/` apuntando a tu GPU. |

---

## 💻 El Gravity Bridge Server (Para IDEs)

Si te has hartado de configurar LLMs en tus extensiones de Visual Studio Code cada vez que pruebas un CLI de AI, déjaselo al Bridge.

1.  Inicia el **`INICIAR_SERVIDOR.bat`**. Éste se queda minizado en el fondo.
2.  En **Continue.dev, CodeGPT, Cursor**, la configuración global será esta para siempre:

```json
"API Base URL": "http://localhost:7860/v1",
"API Key": "gravity-local",
"Model": "gravity-bridge-auto"
```

### ¿Qué ocurre bajo el capó?
El Server expone los Endpoints `v1/models` y `v1/chat/completions`. Todo el stack local de tus editores es interceptado, procesado y enviado dinámicamente al motor (Ollama o LM Studio) que detecte que está usando la GPU en ese preciso instante ahorrándote 0.5s de latencia. Si cambias de Ollama a LM Studio, **tus editores web/IDEs no se enteran ni debes cambiar settings.** Gravity lo re-enruta sobre la marcha local.

---

## 📚 Documentación Avanzada (Deep Dives)

El conocimiento técnico exhaustivo de todo el ecosistema de IA ha sido dividido en secciones enfocadas. Haz clic en cualquiera de las guías abajo para dominar por completo Gravity V4.0.

> [!NOTE]
> **🚀 Ver [COMMANDS.md](COMMANDS.md)** para la tabla absoluta del Arsenal de Comandos secretos y pipe.

> [!NOTE]
> **📦 Módulos:** Ver [MODULES.md](MODULES.md) para documentación técnica de arquitectura del Proxy y Scanner.

> [!NOTE]
> **❓ Preguntas Frecuentes:** Ver [FAQ.md](FAQ.md) para solución de problemas (Troubleshooting) y bugs con puertos.

> [!NOTE]
> **🔗 Integración IDE:** Ver [INTEGRATION.md](INTEGRATION.md) para el super-manual de configuración en VS Code (CodeGPT), Continue.dev, Cody, Aider y Cursor.

> [!NOTE]
> **🌍 Localización:** Ver [SPANISH_LOCALIZATION.md](SPANISH_LOCALIZATION.md) para detalles del bias cognitivo del idioma.

<br>

### ⚖️ Gobernanza Open-Source
* ⚖️ [Licencia MIT](LICENSE)
* 🤝 [Código de Conducta](CODE_OF_CONDUCT.md)
* 🛠️ [Guía de Contribución](CONTRIBUTING.md)

<br>
<p align="center">
  <strong>© 2024-2026 DarckRovert (Elnazzareno) — El Séquito del Terror</strong>
</p>
