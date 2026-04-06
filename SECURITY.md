# 🛡️ Política de Seguridad — Gravity AI Bridge

Tu privacidad es nuestra prioridad absoluta. Este proyecto está diseñado para funcionar en hardware local (Offline-First) para evitar la fuga de datos confidenciales.

## ⚠️ Reporte de Vulnerabilidades
Si encuentras un fallo de seguridad (ej. Inyección de prompts, bypass de autenticación local), por favor **NO abras un Issue público**.

Envía los detalles técnicos directamente al equipo de seguridad:
- **Email Técnico**: security@claseabc.netlify.app
- **Discord**: Comunidad DarckRovert (Canal #security)

## 🏗️ Alcance de Auditoría
- Desbordamiento de búfer en drivers locales (ROCm/NPU).
- Fuga de tokens en el Bridge Server.
- Persistencia de datos en `_knowledge.json`.

---
*Gracias por ayudarnos a mantener a Gravity seguro.*
