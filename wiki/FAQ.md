# ❓ FAQ y Resolución de Problemas — V10.0

Esta sección recopila las dudas más comunes y los errores típicos encontrados durante la fase de auditoría y operación de Gravity AI Bridge.

## 📡 Conectividad y Red

### ❌ Error: "Connection Refused" al entrar al Dashboard
**Causa:** El servidor no se ha iniciado o hay un proceso bloqueando el puerto 7860.
**Solución:** 
1. Revisa que `python bridge_server.py` esté corriendo sin errores en la consola.
2. Ejecuta `netstat -ano | findstr :7860` para ver si el puerto está ocupado.

### ❌ Error: "429 Too Many Requests" en la API de Chat
**Causa:** Has superado el límite de peticiones configurado en `config.yaml` o el proveedor de IA (ej: OpenAI) está limitando tu cuenta.
**Solución:** Revisa la clave `rate_limit.requests_per_minute` en tu archivo de configuración y asegúrate de que no es demasiado restrictiva.

## 🎮 Game Server Manager

### ❌ El servidor WoW no inicia pero el Bridge dice "Starting"
**Causa:** Rutas mal configuradas en `config.yaml` o falta de permisos de administrador.
**Solución:** Asegúrate de que las rutas a `mangosd.exe` y `realmd.exe` son absolutas (ej: `F:\Server\bin\mangosd.exe`). Ejecuta el Bridge como Administrador.

### ❌ No puedo registrar cuentas desde el Portal Web
**Causa:** El Bridge no tiene acceso a la base de datos `realmd` de MaNGOS o las credenciales en `config.yaml` son incorrectas.
**Solución:** Verifica la clave `game_servers.wow_vanilla.db_connection`.

## 🛡️ Seguridad y Auditoría

### ⚠️ El Monitor de Seguridad marca "SOSPECHOSO" en un puerto
**Causa:** Hay un proceso escuchando en un puerto que no está en la `WHITELIST_PORTS` de `core/security_monitor.py`.
**Solución:** Si el puerto es legítimo (ej: un nuevo servicio que has instalado), añádelo a la lista blanca en `core/security_monitor.py`.

### ❌ Mis API Keys desaparecen al reiniciar
**Causa:** El cifrado DPAPI falló o el archivo de base de datos de claves está corrupto.
**Solución:** Asegúrate de que no estás moviendo la instalación a otro PC (DPAPI está vinculado al hardware/usuario). Debes volver a guardar las llaves mediante el Dashboard.

## 🚀 Deploy Manager

### ❌ El deploy a Netlify falla con "npm not found"
**Causa:** Node.js no está instalado o no está en el PATH del sistema que ejecuta el Bridge.
**Solución:** Abre una terminal y escribe `npm -v`. Si no funciona, instala Node.js LTS y reinicia el Bridge.

---
*¿Tu problema no está aquí? Abre un Issue en GitHub o consulta con el Auditor en el chat del Dashboard.*
