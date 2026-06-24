# 🛠️ Troubleshooting y FAQ

### ❌ El Orquestador no detecta mis modelos `.gguf`
**Causa:** La ruta `models/` no está siendo escaneada o el archivo no tiene la extensión correcta.
**Solución:** Mueve tus archivos `.gguf` a la carpeta `models/` y reinicia el puente. No necesitas compilar nada, la versión V16.3 ya incluye dependencias pre-compiladas Vulkan.

### ❌ "TimeoutError" en los Logs de la consola
**Tranquilo.** Esto significa que el Blindaje Anti-Caídas (Poison Pill Resilience) de V16.3 PRO interceptó a un motor defectuoso y cortó el lazo a los 8 segundos para evitar bloquear el resto de la IA. Es un comportamiento deseado.

### ❌ OOM (Out Of Memory)
**Solución:** En la versión V16.3 PRO, el **Memory Guard** monitorea la RAM libre de tu sistema. Si es menor de 2.5 GB, reduce el tiempo de inactividad a 15 segundos y desaloja las IAs automáticamente. También puedes forzar la limpieza de contexto escribiendo `/limpiar` en el Chat Auditor. Si utilizas Ollama, Gravity aplicará "Turbo KV-Cache" automáticamente.
