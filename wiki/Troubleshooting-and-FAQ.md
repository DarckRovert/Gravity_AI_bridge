# 🛠️ Troubleshooting y FAQ

### ❌ El Orquestador no detecta mis modelos `.gguf`
**Causa:** La ruta `inputs/models/` no está siendo escaneada o el archivo no tiene la extensión correcta.
**Solución:** Mueve tus archivos `.gguf` a la carpeta `inputs/models/` y reinicia el puente. No necesitas compilar nada, la versión V16.2 ya incluye dependencias pre-compiladas Vulkan.

### ❌ "TimeoutError" en los Logs de la consola
**Tranquilo.** Esto significa que el Blindaje Anti-Caídas (Poison Pill Resilience) de V16.2 PRO interceptó a un motor defectuoso y cortó el lazo a los 8 segundos para evitar bloquear el resto de la IA. Es un comportamiento deseado.

### ❌ OOM (Out Of Memory)
**Solución:** Escribe `/limpiar` en el Chat Auditor. Esto vaciará instantáneamente la VRAM de tu APU Ryzen. Si usas Ollama, Gravity aplicará "Turbo KV-Cache" automáticamente.
