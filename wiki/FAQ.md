# FAQ — Gravity AI Bridge V10.0
**Diamond-Tier Edition** · [Reportar un bug](https://github.com/DarckRovert/Gravity_AI_bridge/issues) · [twitch.tv/darckrovert](https://twitch.tv/darckrovert)

---

## Instalación y Requisitos

### ¿Necesito instalar Python para usar Gravity AI Bridge?
**No**, si usas el instalador `.exe`. El ejecutable generado con PyInstaller incluye el intérprete Python y todas las dependencias. El usuario final solo necesita Windows 10 (1809+) x64.

Si eres desarrollador y quieres ejecutarlo desde el código fuente, sí necesitas Python 3.11+.

---

### ¿Necesito una GPU dedicada?
No. El Bridge funciona perfectamente con:
- **Solo CPU** — más lento, pero funcional con modelos pequeños (~7B cuantizados)
- **iGPU AMD/Intel** — Los modelos usan la VRAM compartida disponible
- **GPU NVIDIA** (CUDA) — Rendimiento óptimo
- **GPU AMD dedicada** (ROCm en Windows) — Requiere ROCm runtime instalado

El panel **Hardware Monitor** detecta automáticamente tu configuración y calcula el contexto óptimo para tu hardware específico.

---

### ¿Por qué falla el Build del instalador con "Icon not found"?
El archivo `assets/gravity_icon.ico` no existía. Desde la versión actual del `build_installer.bat` esto se detecta automáticamente y se genera. Si ves este error en una versión antigua, ejecuta:
```bash
python make_icon.py
```
Eso genera el `.ico` con todos los tamaños (256, 128, 64, 48, 32, 16 px) y el build continúa.

---

### ¿Por qué el build falla con "PyInstaller not found" o "No se pudo instalar"?
Causas posibles y soluciones:

| Causa | Solución |
|:---|:---|
| Sin conexión a internet | Conecta a internet o usa un mirror interno |
| Firewall corporativo bloquea PyPI | Usa `--proxy http://tu-proxy:puerto` |
| Python no está en el PATH | Reinstala Python marcando "Add to PATH" |
| Permisos insuficientes | Ejecuta la terminal como Administrador |

Instalación manual de respaldo:
```bash
pip install pyinstaller --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

---

### ¿El `build_installer.bat` necesita ejecutarse como Administrador?
**No**. El proceso de build (PyInstaller) no requiere permisos elevados. El **instalador resultante** sí necesita permisos de administrador para instalarse en `Program Files`, pero el build en sí no.

---

## Proveedores y Modelos

### ¿Qué motores de IA locales soporta?
| Motor | Puerto por defecto | Obtener |
|:---|:---|:---|
| **Ollama** | 11434 | [ollama.com](https://ollama.com) |
| **LM Studio** | 1234 | [lmstudio.ai](https://lmstudio.ai) |
| **KoboldCPP** | 5001 | [github.com/LostRuins/koboldcpp](https://github.com/LostRuins/koboldcpp) |
| **Jan AI** | 1337 | [jan.ai](https://jan.ai) |
| **Lemonade** | 8000 | AMD ROCm Edge |

El Bridge los detecta automáticamente por puerto. No es necesario configurar nada si están corriendo con el puerto por defecto.

---

### ¿Qué proveedores cloud soporta?
| Proveedor | Modelos |
|:---|:---|
| **Anthropic** | Claude 3.5 Sonnet, Claude 3.7 Opus |
| **OpenAI** | GPT-4o, GPT-4o-mini, o1, o3 |
| **Google** | Gemini 2.0 Flash, Gemini 1.5 Pro |
| **Groq** | LLaMA 3.3 70B, Mixtral (ultra-rápido) |
| **Mistral AI** | Mistral Large, Mistral Nemo |

Configura la API key en el panel Configuración del Dashboard. Las keys se cifran localmente con DPAPI de Windows.

---

### ¿Puedo tener Ollama y LM Studio corriendo al mismo tiempo?
Sí. El Bridge detecta ambos y usa el de menor latencia automáticamente. Si quieres fijar uno:
```
/usar ollama        → Fija Ollama como proveedor
/usar lmstudio      → Fija LM Studio como proveedor
/auto               → Vuelve al auto-switch
```

---

### ¿Cómo sé qué modelo está usando el Bridge?
- En el sidebar del Dashboard, esquina inferior izquierda → "Modelo Activo"
- En el panel **System Status** → campo "Proveedor / Modelo"
- En el panel **Engine Watchdog** → "Motor Activo"

---

### ¿Qué modelo es el más recomendado para empezar?
Para VRAM entre 4-8 GB:
```bash
ollama pull qwen2.5-coder:7b    # 4.7 GB · código excelente
ollama pull gemma3:4b           # 3.3 GB · muy rápido en CPU
```
Para VRAM 8-16 GB:
```bash
ollama pull qwen2.5-coder:32b   # 19 GB · el mejor para código local
ollama pull deepseek-r1:14b     # 9 GB · razonamiento profundo
```

---

## Dashboard y Funcionalidades

### ¿Por qué el Cost Center siempre muestra $0.0000?
Porque los **proveedores locales son gratuitos**. El Cost Center solo registra costes de proveedores cloud que cobran por token (Anthropic, OpenAI, Gemini, Groq, Mistral). Si solo usas Ollama o LM Studio, el coste es siempre $0.

---

### ¿Cómo funciona el Engine Watchdog?
El Watchdog es un hilo daemon que corre cada 30 segundos. Su lógica:
1. Pide al `provider_manager` un escaneo de todos los proveedores
2. Selecciona el de menor latencia que esté respondiendo correctamente
3. Si el proveedor activo falla 2 veces consecutivas, cambia al siguiente
4. Si el modelo está en modo **LOCKED**, no hace ningún cambio aunque haya algo mejor

Para volver al modo automático: panl Watchdog → botón "🔓 Forzar Unlock".

---

### ¿El RAG envía mis documentos a internet?
**No.** El motor RAG usa embeddings generados localmente con `sentence-transformers`. El proceso completo (indexado + consulta) ocurre en tu máquina. Ningún fragmento de tus documentos sale de tu equipo.

---

### ¿Cómo guardo y cargo conversaciones?
Desde el CLI del Bridge:
```
/guardar mi-analisis-de-codigo    → Guarda el historial actual
/cargar mi-analisis-de-codigo     → Restaura esa sesión
/sesiones                         → Lista todas las sesiones guardadas
/fork variante-alternativa        → Crea una rama sin borrar el original
```
Las sesiones aparecen también en el panel **Sessions** del Dashboard.

---

### ¿Qué es el Model Context Protocol (MCP)?
MCP es un estándar abierto que permite que el Bridge se conecte a servidores que exponen herramientas como:
- Lectura/escritura de archivos del sistema
- Búsqueda en repositorios GitHub
- Consultas a bases de datos (SQLite, PostgreSQL)
- Búsqueda web

Es compatible con Continue.dev, Claude Desktop y cualquier cliente que soporte MCP. Se configura en `config.yaml` bajo la clave `mcp_servers`.

---

### ¿Puedo usar el Bridge desde un IDE como VS Code?
Sí. Desde el panel **Configuración** → sección **IDE Setup**, puedes configurar automáticamente:
- **Continue.dev** — Extensión VS Code con chat y autocompletado
- **Aider** — AI pair programmer en terminal
- **Cursor** — VS Code fork con IA integrada

O desde la terminal:
```bash
python core/ide_integrator.py todo    # Configura los tres a la vez
```

---

## Red y Seguridad

### ¿Puedo acceder al Dashboard desde otro dispositivo en la red local?
Sí. El servidor escucha en `0.0.0.0:7860`, lo que significa que acepta conexiones de cualquier IP de tu red. Desde otro dispositivo usa:
```
http://IP_DE_TU_PC:7860
```
Puedes ver tu IP local con `ipconfig` en PowerShell.

---

### ¿Cómo expongo el servidor WoW a internet?
1. Configura el port forwarding en tu router para los puertos **8085** (juego) y **3724** (autenticación), apuntando a la IP local de tu PC
2. Obtén tu IP pública: busca "mi ip" en Google
3. En el Dashboard → panel **Game Servers** → botón "Exponer WAN"
4. Ingresa tu IP pública o dominio DDNS en el modal
5. El Bridge actualiza `mangosd.conf` y `realmd.conf` automáticamente

Para un servidor 24/7 estable, considera usar un VPS. Ver [Deploy Externo VPS](Deploy_Externo_VPS.md).

---

### ¿Mis API keys de cloud están seguras?
Sí. Las keys se cifran usando **DPAPI (Windows Data Protection API)**, que vincula el cifrado a tu identidad de usuario de Windows. Solo tú, en tu equipo, puedes descifrar las keys. Nunca se almacenan en texto plano en ningún archivo del proyecto.

---

### ¿El Bridge tiene autenticación para evitar que otros lo usen?
Por defecto no requiere autenticación (útil en LAN privada). Para restringir el acceso:
```yaml
# config.yaml
security:
  allowed_keys:
    - "mi-key-privada-1234"
    - "key-de-continue-dev"
```
Solo las peticiones con `Authorization: Bearer <key>` coincidente pasarán.

---

## Mantenimiento

### ¿Cómo actualizo a una nueva versión?
**Modo desarrollador:**
```bash
git pull origin main
pip install -r requirements.txt
python bridge_server.py
```

**Instalador (.exe):**
Descarga y ejecuta el nuevo `Gravity_AI_Bridge_VXX.X_Setup.exe`. El instalador preserva tu `config.yaml` y `_knowledge.json`.

---

### ¿Cómo limpio el audit log sin perder información?
El audit log (`_audit_log.jsonl`) crece indefinidamente. Para archivarlo:
```bash
# Mover el log actual a un archivo con fecha
move _audit_log.jsonl _audit_log_2026-04.jsonl
# El bridge creará uno nuevo automáticamente
```

---

### ¿Cómo reinicio el cost tracker?
Reinicia el Bridge. El `session_cost` se reinicia automáticamente. El `daily_cost` se reinicia a medianoche.

Para borrar el historial completo:
```bash
echo {"providers":{}, "daily":{}, "total":{}} > _cost_log.json
```

---

### ¿Dónde reporto bugs o sugiero mejoras?
- **GitHub Issues:** [github.com/DarckRovert/Gravity_AI_bridge/issues](https://github.com/DarckRovert/Gravity_AI_bridge/issues)
- **Twitch:** [twitch.tv/darckrovert](https://twitch.tv/darckrovert) (en directo)
- **CONTRIBUTING.md** — Para contribuir con código directamente
