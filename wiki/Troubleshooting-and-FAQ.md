# 🛠️ Troubleshooting & FAQ / Solución de Problemas

This guide provides solutions to common hardware and configuration issues for Gravity AI Bridge V7.1.

Esta guía proporciona soluciones a problemas comunes de hardware y configuración para Gravity AI Bridge V7.1.

---

## 💻 Hardware Issues / Errores de Hardware

### [EN] NPU Not Detected (Ryzen AI)
- **Cause**: Driver version incompatibility or missing `XDNA` firmware.
- **Fix**: Install **Ryzen AI Software 1.7.1**. Ensure Secure Boot allows unsigned bitstreams or use the iGPU fallback.

### [ES] NPU No Detectado (Ryzen AI)
- **Causa**: Incompatibilidad de controladores o falta del firmware `XDNA`.
- **Solución**: Instala **Ryzen AI Software 1.7.1**. Asegura que el Secure Boot permita bitstreams o usa el fallback a iGPU.

### [EN] Out of Memory (OOM)
- **Cause**: Context window too large for your VRAM.
- **Fix**: The `hardware_profiler.py` automatically calculates the optimal `num_ctx`. Ensure you are not running other GPU-heavy apps.

---

## 📡 Connectivity / Conectividad

- **Base URL**: `http://localhost:7860/v1`
- **Error 404/Connection Refused**: Ensure `bridge_server.py` is running. Check your firewall settings for port 7860.

---

## ⚖️ Intellectual Property / Propiedad Intelectual
This project is owned by **DarckRovert**. Licensed under **PolyForm Non-Commercial 1.0.0**.

Este proyecto es propiedad de **DarckRovert**. Bajo Licencia **PolyForm No-Comercial 1.0.0**.

*Official Support:* [twitch.tv/darckrovert](https://www.twitch.tv/darckrovert)
