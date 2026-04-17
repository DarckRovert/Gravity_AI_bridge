# FAQ — Gravity AI Bridge V10.0

---

### ¿Qué es Gravity AI Bridge?
Es un proxy OpenAI-compatible que enruta tus peticiones de IA hacia el mejor modelo disponible en tu hardware local o en la nube, con un Dashboard web para controlar todo desde el navegador.

---

### ¿Necesito una GPU para usarlo?
No. Funciona con CPU, iGPU y GPU dedicada. El Hardware Monitor detecta tu configuración y calcula el contexto óptimo. Con CPU sola el rendimiento será más lento, pero funcional.

---

### ¿Mis datos se envían a internet?
Solo si configuras un proveedor cloud (Anthropic, OpenAI, etc.) y tienes su API key configurada. Con proveedores locales (Ollama, LM Studio, Kobold) todo se procesa en tu máquina.

---

### ¿Qué motores de IA soporta?
**Local:** LM Studio, Ollama, KoboldCPP, Jan AI, Lemonade.
**Cloud:** Anthropic Claude, OpenAI, Google Gemini, Groq.
El Auto-Switch selecciona el mejor disponible automáticamente.

---

### ¿Por qué el Cost Center siempre muestra $0.0000?
Porque estás usando proveedores locales, que son gratuitos. El Cost Center solo registra costes de proveedores cloud (Anthropic, OpenAI, etc.) cuando tienen una API key configurada.

---

### ¿Cómo funciona el Engine Watchdog?
El Watchdog corre cada 30 segundos y verifica qué proveedor responde más rápido. Si el activo falla, hace auto-switch al siguiente. Puedes bloquearlo en un modelo específico desde el CLI o hacer Unlock desde el Dashboard.

---

### ¿El RAG envía documentos a la nube?
No. El motor RAG usa embeddings locales (sentence-transformers). Los documentos se indexan y consultan 100% en tu máquina.

---

### ¿Cómo guardo una conversación?
Desde la terminal del Bridge, escribe `/guardar nombre`. La sesión queda en `_saves/nombre.json` y aparece en el panel Sessions del Dashboard.

---

### ¿Qué es MCP?
Model Context Protocol es un estándar que permite al Bridge conectarse a servidores externos que exponen herramientas (sistemas de archivos, bases de datos, APIs). Compatible con Continue.dev y Claude Desktop.

---

### ¿El instalador .exe requiere Python instalado?
No. El ejecutable empaquetado con PyInstaller incluye todo lo necesario. El usuario final solo necesita Windows 10/11 x64.

---

### ¿Por qué falla el Build del instalador?
Causas comunes:
1. PyInstaller no está instalado → `pip install pyinstaller`
2. Sin acceso a PyPI → usar `--trusted-host pypi.org` (ya incluido en el script)
3. Inno Setup 6 no instalado → descargar en https://jrsoftware.org/isdl.php

---

### ¿Cómo configuro el servidor de juego WoW?
Ver la guía completa en [Game Server Guide](Game-Server-Guide.md).

---

### ¿Puedo usar Gravity AI Bridge desde otro dispositivo en la red?
Sí. El servidor escucha en `0.0.0.0:7860`. Accede desde otro dispositivo con `http://IP_DEL_HOST:7860`. Para acceso desde internet, usa el panel Game Servers → Exponer WAN (o configura tu router manualmente para el puerto 7860).

---

### ¿Cómo actualizo a una versión nueva?
```bash
git pull origin main
pip install -r requirements.txt
```
Si es usuario del instalador, descarga y ejecuta el nuevo `Setup.exe`.

---

### ¿Dónde reporto bugs?
[https://github.com/DarckRovert/Gravity_AI_bridge/issues](https://github.com/DarckRovert/Gravity_AI_bridge/issues)
