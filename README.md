# GRAVITY AI BRIDGE V4.2 — GOD TIER ⚡
*Un componente élite del Séquito del Terror.*

**Gravity AI Bridge** es tu "puente" perimetral para enlazar tus modelos locales de Inteligencia Artificial pesada (DeepSeek-R1, Ollama, LM Studio, etc.) con herramientas de nivel Enterprise como *Visual Studio Code*, *Cursor*, *Aider* o la consola propia de Auditoría.

![Gravity Logo](media__1775204686339.png)

## 🎯 Arquitectura de Alto Nivel
Con una reescritura desde cero a Python Puro, Gravity detecta tus motores de IA locales a una velocidad vertiginosa (**1.7s**), determina el más sano e infiere el tráfico sin tocar internet.

### ✨ Features de la Versión God-Tier:
* **Autoconfiguración Zero-Touch**: Escaneo de puertos asincrónico agresivo; encuentra y se ata a tu IA local más rápida sin soltarla.
* **Escritura y Manejo Dinámico IDE**: Configura automáticamente el `config.yaml` de VS Code Continue y clona perfiles de *Aider* y *Cursor IDE*.
* **Comandos en Crudo (CMD)**: Desde cualquier consola escribe `gravity "Revisar mi archivo.js"` y el Agente se abrirá por ti.
* **Soporte Streaming Real-Time**: Consume tus respuestas palabra por palabra para que sientas un output veloz, evadiendo la latencia clásica de localhost.
* **Manejo Contextual Avanzado**: Inyéctale código desde enlaces HTTP, repositorios de git local enteros, o manuales TXT con los comandos nativos de la CLI de Auditoría.

## 🚀 Instalación y Despliegue Inmediato
Descarga todo el proyecto y dentro corre:
1. Haz doble clic en **`INSTALAR.bat`**. 
   - Modificará variables para añadir el comando `gravity`.
   - Elegirá automáticamente el motor neurálgico detectado en tu PC (Ej. `deepseek-r1:32b`).
   - Magnetizará el ícono Auditor.
2. Todo tuyo. Presiona el botón del escritorio.

## 🥷 El Arsenal: Inyección e Inteligencia
Una vez que abras tu Agente (o usando el comando global `gravity`), cuentas con el siguiente nivel de control:

| Comando | Acción Exacta |
|---|---|
| `!integrar <herramienta>` | Regenera configuraciones de VS Code, Cursor o Aider por nombre o `!integrar todo`. *(Refiere a [MANUAL_IDE.md](MANUAL_IDE.md))* |
| `/leer <archivo.js>` | Anexa a la memoria central el archivo completo que elijas para un Fix rápido. |
| `/leer-git` | Trae y lee de manera instantánea todos los archivos sin guardar y Diffs puros que tengas modificados en la carpeta. |
| `/leer-url <www>` | Descarga una página web plana o log y sométela a la bestia. |
| `!aprende <regla>` | Obliga al modelo a respetar una norma (ej: `!aprende Siempre código ES6`). |
| `!guardar <nombre>` | Guarda la conversación actual en una instantánea llamada "<nombre>". |
| `!saves` | Lista todas las instantáneas (snapshots).  Escribe tu snapshot para cargar ese contexto. |
| `!comprimir` | Si llenaste los 128k/8k tokens, presiona aquí y el modelo resumirá su cabeza y borrará la basura reteniendo la sabiduría. |
| `!version` o `!info` | Revela el estado topológico y conexión actual de Hardware. |

### 👻 Modo Fantasma
Si deseas que tu IDE como Visual Studio Code envíe sus *Copilots* al servidor Gravity AI sin tener una terminal negra molestando en el fondo, haz doble clic en **`MODO_FANTASMA.vbs`**. Todo sucederá silenciosamente y el historial se grabará en `bridge.log`.

*(Para cancelar esta instalación a nivel Enterprise que tocó el sistema y tu PATH, simplemente ejecuta `DESINSTALAR.bat`).*

---

## 📚 Documentación Oficial y Workflows

Consulta los siguientes documentos para dominar al máximo el puente de Inteligencia Artificial:

* **[Manual de Integración IDE](MANUAL_IDE.md):** Instrucciones visuales para vincular Cursor IDE, Aider y VS Code Continue.
* **[Preguntas Frecuentes (FAQ)](FAQ.md):** Troubleshooting sobre puertos bloqueados y dudas existenciales del sistema.
* **[Manual de Delegación Táctica](.agents/workflows/delegar.md):** ¿Cómo decirle a otras inteligencias que aprovechen tu sistema Gravity usando comandos y tuberías? *(Revisar carpeta `.agents/workflows`).*
