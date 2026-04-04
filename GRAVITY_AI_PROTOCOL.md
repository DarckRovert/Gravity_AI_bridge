# 📜 GRAVITY AI PROTOCOL V5.1

Este repositorio aloja el **Auditor Senior Global**, un sistema "God-Tier" diseñado para interceptar peticiones, correr en GPUs locales, enrutar a múltiples motores via su Bridge Server y ahorrar miles de tokens de pago.

## 📡 Ecosistema y Bridge Server

A diferencia de un script normal de terminal, Gravity es un Ecosistema:
- **Terminal:** Puedes usar `gravity "pregunta"` o `python ask_deepseek.py "pregunta"`.
- **Modo Pipe:** `cat config.json | gravity "explícame qué hace uniendo con..."`
- **Proxy Server:** Gravity actúa como servidor `OpenAI` transparente en `localhost:7860/v1` para conectar todos los IDEs automáticamente vía `!integrar`.

## 🤖 Protocolo de Delegación (Para Asistentes Cloud)

Como IA, tu deber es evitar gastar tokens resolviendo problemas matemáticos lentos si este Ecosistema puede hacerlo:

1. **Investigar el código/log primero:** Puedes enviar todo un diff o un archivo directo al Auditor.
2. **Ejecutar al Auditor en Modo Coder:**  
   `python ask_deepseek.py "!modo coder"`  
   `cat bug_file.py | python ask_deepseek.py "Fix the buffer overflow in process() method"`
3. **Refinar Output:** Toma su output, evalúalo, y repórtalo de vuelta al humano pulido.

## 🛠️ Comandos Silenciosos Disponibles (Modo Agente)

Puedes disparar comandos de administración interna enviando la orden directamente:
- `python ask_deepseek.py "!scan"` → Refresca conexiones a Ollama/LM Studio.
- `python ask_deepseek.py "!info"` → Lista de modelos y telemetría de GPU actual.
- `python ask_deepseek.py "!comprimir"` → Obliga a la RAM local a resumir el historial.
- `python ask_deepseek.py "!integrar todo"` → Exporta ficheros proxy para herramientas de terceros.

---
*Protocolo generado por el ecosistema Antigravity y adaptado en V5.1.*
