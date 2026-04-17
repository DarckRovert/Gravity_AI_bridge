# 📖 Manual de Usuario — Gravity AI Bridge V10.0

Este manual guía a los administradores en la operación diaria del ecosistema Gravity Bridge a través de su Dashboard Web unificado.

## 🏁 Inicio Rápido

1.  Asegúrate de haber ejecutado `launchers/INICIAR_TODO.bat` o tener el servidor corriendo.
2.  Accede mediante tu navegador a `http://localhost:7860`.
3.  Verifica que el indicador superior derecho muestre **"BRIDGE ONLINE"** en verde.

## 💬 Chat Auditor (Análisis de Sistema)

El **Chat Auditor** es tu interfaz directa con la inteligencia del Bridge.
- **Consultas de Sistema:** Puedes preguntar sobre el estado de los juegos, procesos o logs.
- **Acceso a Conocimiento:** El auditor utiliza el `_knowledge.json` para darte respuestas coherentes con la historia del proyecto.
- **Verificación:** Usa el comando `/verify` antes de aplicar cambios estructurales para que el agente audite tu plan.

## ⚔️ Panel Game Servers (WoW)

Desde esta sección gestionas tu infraestructura de World of Warcraft:
1.  **Controles de Proceso:** Usa los botones de **Iniciar**, **Detener** y **Reiniciar** para manejar `mangosd` y `realmd`. Las notificaciones (Toasts) te confirmarán el éxito de la operación.
2.  **Consola GM:** Escribe comandos nativos directamente (ej: `.announce`, `.account create`).
3.  **Exposición WAN:** El botón "Exponer a Internet" te pedirá tu IP pública para configurar automáticamente las rutas de acceso externo en las tablas de `realmd`.
4.  **Monitoreo de Jugadores:** Consulta en tiempo real quién está online, su nivel, raza y clase.

## 🎨 Vision Studio e Image Queue

Diseñado para la generación masiva de assets (ej: menús de comida o iconos de items):
1.  **Dashboard de Vision:** Visualiza la instancia de Fooocus integrada.
2.  **Cola de Imágenes:** Añade prompts a la cola interna. El Bridge gestionará la generación secuencial para no saturar tu GPU.
3.  **Estado de Generación:** Monitorea el progreso y el performance (it/s) de cada trabajo.

## 🚀 Panel de Despliegue (Deploy)

Centraliza el despliegue de tus aplicaciones web (como portales de cuentas o webs de guilds):
1.  **Ruta del Proyecto:** Ingresa la ruta local donde se encuentra tu proyecto web (ej: una app de Next.js).
2.  **Iniciar Deploy:** El botón iniciará un proceso de `npm install` -> `npm run build` -> `netlify deploy`.
3.  **Logs de Build:** Observa los errores de compilación directamente en la caja de logs integrada para diagnósticos rápidos.

## 🛡️ Monitor de Seguridad

Consulta regularmente este panel para asegurar la integridad de tu servidor:
- **Integridad:** Una marca verde en archivos clave significa que no han sido alterados.
- **Puertos:** Verifica que solo los puertos autorizados (7860, 8085, 3724, etc.) estén activos.
- **Alertas:** Revisa la lista de alertas recientes para detectar intentos de fuerza bruta o escaneos de puertos externos.

---
*Manual de Operación Diamond-Tier Edition.*
