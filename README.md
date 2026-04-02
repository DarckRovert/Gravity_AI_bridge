# Gravity AI Bridge 🌉🤖 — Auditor Senior V2.2

Este proyecto es un conector avanzado (bridge) diseñado para que tu asistente de IA principal pueda delegar tareas de auditoría técnica a modelos locales respaldados por **Ollama** (específicamente `deepseek-r1:8b`).

La versión 2.2 transforma el bridge en una **Herramienta Global del Sistema**.

## ✨ Novedades de la V2.2
- **Despliegue Global:** Instala el comando `gravity` en tu sistema Windows y úsalo desde cualquier terminal.
- **Modo Agente Bilingüe:** Optimización de comunicación IA-a-IA en inglés técnico para máxima precisión lógica.
- **Multimodelo Dinámico:** Detecta y usa cualquier modelo de Ollama que tengas instalado (`llama3.1`, `deepseek-r1`, `mistral`, etc.).
- **Persistencia de Sesión:** El Auditor recuerda tu último modelo usado en `_settings.json`.

## 🌐 Instalación Global (Recomendado)
Para usar el poder de Gravity en **cualquier proyecto**, haz doble clic en:
👉 `INSTALL_GLOBAL.bat`

Este script:
1.  Añade la carpeta del proyecto a tu **PATH de Windows** de forma segura.
2.  Verifica dependencias (Python y Ollama).
3.  Te permite usar el comando `gravity` desde cualquier lugar.

> [!NOTE]
> Tras la instalación, reinicia tu terminal o VS Code para que el comando `gravity` responda.

## 🛠️ Uso

### Comandos Globales
Desde cualquier carpeta de tu disco duro, puedes ejecutar:
- `gravity "Analiza este código..."`
- `gravity "!modelos"` (Ver tu catálogo local)
- `gravity "!usar <nombre>"` (Cambiar de modelo predeterminado)

### Integración en Otros Proyectos
Para que Antigravity (o cualquier IA) sepa que debe usar el bridge en un proyecto nuevo, simplemente copia el archivo **`.antigravityrules`** de este repositorio a tu nueva carpeta. ¡La IA entenderá las instrucciones automáticamente!

## 📁 Estructura del Proyecto
- `gravity.bat`: Lanzador universal.
- `ask_deepseek.py`: El cerebro y motor del Auditor (V2.2).
- `health_check.py`: Diagnóstico dinámico de modelos.
- `_settings.json`: Persistencia de tus preferencias (modelo, idioma).
- `_knowledge.json`: Reglas de largo plazo inyectadas al sistema.

---
**Gravity AI Bridge** — Elevando la calidad de tu código localmente. 💻🔥
