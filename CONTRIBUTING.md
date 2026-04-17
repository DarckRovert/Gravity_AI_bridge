# Guía de Contribución — Gravity AI Bridge

¡Gracias por tu interés en mejorar Gravity AI Bridge! Para mantener la calidad "Diamond-Tier" de este proyecto, solicitamos que todas las contribuciones sigan estos estándares estrictos.

## ⚖️ Principios Fundamentales

1.  **Directo y Técnico:** No agregues comentarios superfluos ni código redundante.
2.  **Soberanía Local-First:** El código debe priorizar la ejecución local y la privacidad de los secretos del usuario (DPAPI).
3.  **Integridad de Marca:** Todo enlace externo debe apuntar a dominios oficiales de DarckRovert o documentación técnica de confianza.

## 🛠️ Estándares Técnicos

### Python
- Utiliza **type hinting** en todas las funciones y clases.
- Estilo de código PEP 8 (estricto).
- Manejo de excepciones específico; evita los bloques `try: except: pass` a menos que sea una captura de log controlada.

### WoW Lua (Addons asociados)
- Estricto cumplimiento de **Lua 5.0**.
- Prohibido el uso de operadores de Lua 5.1+ (ej: `#` para longitud, `math.huge`).

### Web Dashboard
- Vanilla JavaScript y Vanilla CSS únicamente.
- Prohibida la adición de librerías externas pesadas (como Tailwind o React) sin aprobación previa.

## 🔄 Proceso de Pull Request

1.  **Fork del Proyecto:** Crea una rama descriptiva (ej: `fix/srp6-auth` o `feat/new-monitor`).
2.  **Auditoría Local:** Asegúrate de ejecutar el comando `/verify` en el Chat Auditor del Dashboard antes de enviar.
3.  **Documentación:** Si tu cambio añade una nueva funcionalidad, debes actualizar la `/wiki` correspondiente.
4.  **Commit Messages:** Usa convenios de commits semánticos (ej: `feat:`, `fix:`, `refactor:`, `docs:`).

## 🛡️ Reporte de Errores

Si encuentras un bug, abre un **Issue** utilizando la plantilla de "Bug Report" y adjunta los logs relevantes del archivo `bridge_server.log`.

---
*Al contribuir, aceptas que tu código estará bajo la Licencia MIT del proyecto.*
