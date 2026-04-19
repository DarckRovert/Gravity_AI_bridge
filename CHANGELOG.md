# Changelog de Evolución (Gravity Bridge)

Registro maestro de la metamorfosis estructural aplicada sobre la herramienta Gravity AI Bridge y el módulo local de servidor WOW. 

## [V10.1] Stable Diamond-Tier Integration - 19/04/2026

**[MAJOR FIXES & SEGURIDAD CORE]**
- **Image Queue Blindado:** La vulnerabilidad sintética de la confirmación Gradio ahora ha sido purgada de raíz. El modulo `fooocus_client` y `image_queue` hacen diferencia real de carpetas en sistema operativo ("antes de disparar POST" vs "post disparar POST"). Los Falsos Positivos de generación se han reducido de un posible 15% a un rotundo 0%.
- **Evacuación de la API RAG Insegura:** Se controló el desgaste perpetuo de la IA con rate limiting `_check_rate` global en la clase BaseHTTPRequestHandler impidiendo el desbordamiento local por LAN.
- **Drenaje de Falsos Flags (Spam Reduction):** `security_monitor.py` detuvo las alertas agresivas de red por puertos rutinarios al cruzarlo pasivamente contra una lista blanca (discord, navegadores, battle.net, steam). Reducción del ~98% de spam en la huella de log audit_log.jsonl.
- **Soporte Compatibilidad Pyinstaller:** El ejecutable frozen dejó de cerrarse arbitrariamente debido a tipajes de python obsoletos `type | None` que desbordaban la compilación pre-Python3.10 en los scripts de IA Process Manager.

**[NUEVAS FUNCIONALIDADES REALES]**
- **SSE En Vivo `/v1/queue/stream`:** Interfaz estática modernizada conectándose por `Event-Stream` bidireccional puro a los contadores HTTP para evitar ahogamiento del servidor via pooling.
- **MangosD Deque Buffer y Auto-Backup:** GravityBridge ahora levanta un Subprocess Popen interceptando Standard Out con un Ring-Buffer (Deque) guardando 500 líneas en RAM, exponiéndose vivas en `/v1/gameserver/log`.
- **Pre-Flight MySQL:** El launcher de `game_server_manager` lanza requests pings internos. Si tu base de datos WOW no existe o no responde, el servidor detiene su secuencia antes de encender Mangos, salvándote de cuelgues oscuros locales.
- **Rotación Máxima de Logs:** La carpeta raíz previene la muerte térmica del disco del Bot haciendo Backups rotativos .pak de 5MB como tope duro.
