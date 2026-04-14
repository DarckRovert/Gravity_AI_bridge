# 🔗 Gravity Integration Guide / Guía de Integración V9.3.1 PRO

Gravity AI Bridge connects your local hardware with any standard AI tool. 
Conecta tu hardware local con cualquier herramienta de IA estándar.

---

## 🏗️ Supported Providers / Motores Soportados

### [EN] Local Backends
- **Ollama**: Automatically detected on `localhost:11434`.
- **LM Studio**: Automatically detected on `localhost:1234`.
- **VLLM / Text-Generation-WebUI**: Supports any OpenAI-compatible server.

### [ES] Motores Locales
- **Ollama**: Detectado automáticamente en `localhost:11434`.
- **LM Studio**: Detectado automáticamente en `localhost:1234`.
- **VLLM / Text-Generation-WebUI**: Soporta cualquier servidor compatible con OpenAI.

---

## ☁️ Cloud Providers / Motores en la Nube

### [EN] Setup
You can configure cloud keys via the `KeyManager`:
- **OpenAI, Anthropic, Gemini, Mistral, Groq, DeepSeek, OpenRouter**.
- **Security**: Keys are encrypted via DPAPI (Windows) in `_keystore.bin`.

### [ES] Configuración
Puedes configurar llaves de nube vía el `KeyManager`:
- **OpenAI, Anthropic, Gemini, Mistral, Groq, DeepSeek, OpenRouter**.
- **Seguridad**: Las llaves se cifran vía DPAPI (Windows) en `_keystore.bin`.

---

## 🛠️ Usage / Uso

1. Start your local provider (e.g., Ollama).
2. Start the Bridge: `python bridge_server.py`.
3. Use the unified endpoint: `http://localhost:7860/v1`.

---

## ⚖️ Intellectual Property / Propiedad Intelectual
This project is owned by **DarckRovert**. Licensed under **MIT License**.

Este proyecto es propiedad de **DarckRovert**. Bajo Licencia **MIT License**.

*Official Support:* [twitch.tv/darckrovert](https://www.twitch.tv/darckrovert)
