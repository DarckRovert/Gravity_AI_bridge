# 📜 CHANGELOG — Gravity AI Bridge

Historial completo de versiones y auditorías detalladas.

## [V7.1] — 2026-04-05 (Official Release)
**"The NPU Revolution"**

### 🚀 Novedades (Aceleración Híbrida)
- **Activación NPU (Ryzen AI)**: Integración masiva de **ONNX Runtime** para offloading de embeddings al NPU XDNA.
- **Protocolo Omni-Audit**: Inyección de lógica de auditoría senior en el prompt del sistema.
- **Hardware-Aware Profiler**: Detección dinámica de VRAM compartida/dedicada y cálculo de `num_ctx` optimizado.

### 🛠️ Correcciones y Mejoras
- **Unicode Fix**: Reconfiguración nativa de `stdout/stderr` a UTF-8 para terminales de Windows.
- **Saneamiento**: Eliminación de imports duplicados (`io`) y estandarización global de versión V7.1.
- **Oobabooga Fix**: Eliminación de falsos positivos en el descubrimiento de motores.

---

## [V7.0] — 2026-04-01
**"Omni-Tier Core"**

- Introducción de `bridge_server.py`.
- Soporte para modelos de 70B+ vía GGUF.
- Sistema de caché local `_knowledge.json`.
- Integración oficial con Cursor e IDEs modernos.
