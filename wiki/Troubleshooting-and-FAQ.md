# 🛠️ Troubleshooting & FAQ

Soluciones crudas para los problemas más severos dentro del `Gravity AI Bridge`.

### Q: El Servidor WoW se marca como "Cerrado Inesperadamente" pero los exes siguen vivos.
**Solución (V10.1):** Existe un bloqueo zombie (PID lockiado sin interfaz). El sistema detiene MangosD automáticamente si detecta un PID fantasma a través de tu memoria RAM en el `_stdout_buffers`. Usa el botón "KILL FORZADO" del Dashboard, este inyectará un `taskkill /F /IM mangosd.exe` sin preguntar.

### Q: Fooocus dice "En progreso" pero no guarda NADA.
**Solución:** Probablemente desconfiguraste el enviroment. La V10.1 cruza listas físicas de la carpeta `outputs`. Asegúrate que no tengas configurado un Path personalizado escondido en el YAML de Fooocus hacia otra ruta remota o disco D:\ distinto.

### Q: ¡El log Security_Audit es basura de 10 megas!
**Solución de versión:** Actualiza a la V10.1 compilada. La V10.1 alertaba todas las conexiones efímeras. La revisión actual rota los JSONL después de 5MB en disco (`.pak`) e ignora estáticamente puertos superiores listados como Steam o Discord. Si quieres bloquear *literalmente TODO*, modifica el array whitelist duro en `core/security_monitor.py`.

### Q: PyInstaller Compilado se crashea en un loop infinito negro.
**Causa:** Python puro en su versión congelada rompe incompatibilidades de tipado (PEP 604 vs viejo typing).  
**Solución:** Estás usando la rama desactualizada. Usa estrictamente el release tag 10.1 donde los pipes `str | int` fueron extirpados por completo de `multi_agent.py`.
