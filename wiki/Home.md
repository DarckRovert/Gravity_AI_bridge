# Bienvenido a la Wiki de Gravity AI Bridge 🌌

Esta wiki documenta la arquitectura técnica de la versión 3.0 (Diamond-Tier) del ecosistema Gravity. Aquí encontrarás la información estructurada sobre cómo funciona internamente la plataforma, desde el manejo dinámico de NPUs hasta el flujo editorial multi-agente.

## Índice Técnico

1. **[Arquitectura Profunda (Deep Dive)](Architecture-Deep-Dive.md)**
   Conoce el cerebro de Gravity: `WorkflowEngine`, `ProviderManager` y la orquestación del `news_daemon.py`. Descubre por qué es a prueba de caídas.

2. **[Referencia de la API Central](API-Reference.md)**
   Documentación de los endpoints HTTP expuestos por el `bridge_server.py` y cómo el Frontend se comunica con el backend de IA.

3. **[Solución de Problemas (FAQ & Fallbacks)](Troubleshooting-and-FAQ.md)**
   Casos de estudio técnicos: Qué pasa cuando la NPU (XDNA) colapsa, cuando un LLM alucina, o cuando Git falla durante el despliegue automático.

---
*Para guías de instalación o contribución, referirse al archivo README.md en la raíz del repositorio.*
