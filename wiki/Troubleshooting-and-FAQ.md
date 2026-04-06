# 🛠️ Troubleshooting-and-FAQ

Gravity AI V7.1 está diseñado para ser robusto, pero la computación local puede ser impredecible debido a drivers y puertos.

## ❓ Preguntas Frecuentes (FAQ)

### 1. ¿Por qué el NPU está al 0% en el Administrador de Tareas?
El NPU Ryzen AI se activa dinámicamente. En V7.1, **solo se activa durante la indexación (Embeddings)** o tareas de búsqueda semántica. El chat principal (LLM) corre en la **GPU 780M** para mayor velocidad de generación.

### 2. ¿Cómo soluciono el error de Unicode en terminales de Windows?
Gravity V7.1 intenta reconfigurar `sys.stdout` a UTF-8. Si ves caracteres extraños, ejecuta este comando en PowerShell antes de iniciar el bridge:
`[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`

### 3. ¿Por qué el modelo de 26B tarda tanto en cargar?
En iGPUs como la 780M, el motor debe reservar gran parte de la RAM compartida. Ten paciencia la primera vez (puede tardar hasta 45-60s).

## 🛠️ Errores Comunes

### Error: `Address already in use (7860)`
- **Causa**: Ya tienes una instancia de Gravity corriendo o una herramienta como Oobabooga está usando el puerto.
- **Solución**: Cierra procesos previos o cambia el puerto en `_settings.json`.

### Error: `No module named onnxruntime`
- **Solución**: Asegúrate de haber ejecutado `python setup_npu.py` para instalar los drivers de aceleración.

### Conflicto de Oobabooga
- **Efecto**: El bridge se detecta a sí mismo como un servidor Oobabooga y entra en bucle.
- **Solución**: El bridge V7.1 ya ignora el puerto 7860 en el escaneo de Oobabooga.

---
*Si tu problema persiste, reportalo en el [Repositorio Oficial](https://github.com/DarckRovert/Gravity_AI_bridge).*
