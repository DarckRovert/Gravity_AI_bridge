# Gravity AI Bridge 🌉🤖 — Auditor Senior V2.0

Este proyecto es un conector avanzado (bridge) diseñado para que tu asistente de IA principal pueda delegar tareas de auditoría técnica a modelos locales respaldados por **Ollama** (específicamente `deepseek-r1:8b`).

La versión 2.0 transforma el bridge en un **Auditor Senior Virtual** con memoria persistente, reglas de aprendizaje y una interfaz de terminal premium.

## ✨ Novedades de la V2.0
- **Personalidad Senior:** El Auditor ahora tiene un System Prompt riguroso que se inyecta automáticamente.
- **Memoria de Aprendizaje:** Usa el comando `!aprende` para que el Auditor nunca olvide tus preferencias técnicas.
- **Interfaz "Rich":** Resaltado de sintaxis, rendering de Markdown y tablas de estado en la terminal.
- **Sistema de Pre-vuelo:** Un script de `health_check.py` verifica que Ollama y el modelo estén listos antes de empezar.
- **Modo Interactivo:** Soporte para leer archivos locales y mantener un hilo conversacional.

## 🚀 Instalación Rápida
1. Asegúrate de tener [Ollama](https://ollama.com/) corriendo y el modelo descargado:
   ```bash
   ollama pull deepseek-r1:8b
   ```
2. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

## 🛠️ Uso

### Iniciar el Auditor (Windows)
Simplemente haz doble clic en `INICIAR_AUDITOR.bat`. Este archivo:
1. Verifica que tengas Python e instalado `rich`.
2. Ejecuta un diagnóstico de conexión con Ollama.
3. Inicia la consola del Auditor.

### Comandos del Chat
Dentro de la consola del Auditor, puedes usar:
- `/leer <ruta>`: Carga un archivo de código y pide al Auditor que lo analice.
- `!aprende <regla>`: Guarda una regla (ej: "Usa PascalCase para clases") en la memoria permanente (`_knowledge.json`).
- `!reglas`: Muestra todas las reglas que el Auditor ha aprendido.
- `!olvida`: Borra la memoria de largo plazo.
- `!limpiar`: Reinicia el historial de la conversación actual.
- `salir`: Cierra la sesión de forma segura.

## 📁 Estructura del Proyecto
- `ask_deepseek.py`: El cerebro y motor del Auditor (V2.0 Refactorizada).
- `health_check.py`: Script de diagnóstico de sistema.
- `INICIAR_AUDITOR.bat`: Lanzador automático con controles de seguridad.
- `_knowledge.json`: Almacén de tus reglas personalizadas.
- `_history.json`: Memoria de corto plazo de la sesión.

---
**Gravity AI Bridge** — Elevando la calidad de tu código localmente. 💻🔥
