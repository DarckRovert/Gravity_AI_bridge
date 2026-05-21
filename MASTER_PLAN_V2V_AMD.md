# 🛰️ PLAN MAESTRO: OPERACIÓN ALETHEIA-V2V (AMD EDITION)

## 🎯 OBJETIVO
Dotar al sistema de capacidades de transformación visual AI en tiempo real (Video-to-Video) similares a DeluluStream, optimizadas específicamente para hardware AMD (Ryzen 7 8700G).

---

## 💻 ESPECIFICACIONES TÉCNICAS (TARGET)
- **CPU/GPU:** Ryzen 7 8700G (Radeon 780M).
- **NPU:** Ryzen AI (XDNA Architecture).
- **RAM:** 32GB DDR5 (Configuración de UMA Framebuffer crítica).
- **OS:** Windows 11.

---

## 🛠️ ARQUITECTURA DEL SOFTWARE

### 1. Motor de Inferencia y Optimización
- **Runtime:** `onnxruntime-directml` (Para aprovechar la aceleración de hardware de Microsoft en AMD).
- **Optimizador:** **Microsoft Olive** para convertir modelos PyTorch a ONNX con cuantización **FP16/INT8**.
- **Modelos:** 
  - `SD v1.5 Turbo` o `LCM-LoRA` (Modelos de un solo paso de muestreo).
  - `ControlNet Canny/Depth` (Versiones ultra-ligeras).

### 2. Pipeline de Procesamiento (Dual-Path)
Para maximizar los FPS, dividiremos la carga:
- **Camino A (NPU):** Procesamiento de ControlNet (Detección de estructura física y pose).
- **Camino B (iGPU):** Inferencia del UNet y Decodificador VAE (Generación de píxeles).

### 3. Sistema de Video (Zero Latency)
- **Captura:** OpenCV con `CAP_DSHOW` (Buffer=1).
- **Salida:** **Spout2** (Memoria compartida de GPU a GPU para OBS).
- **Resolución Target:** 384x384 -> Upscale a 720p/1080p vía FSR (FidelityFX Super Resolution).

---

## 🚀 HITOS DE IMPLEMENTACIÓN (ROADMAP)

### Fase 1: Entorno y Drivers
- Configuración de `DirectML` y validación de drivers de AMD.
- Instalación de `Ryzen AI SDK`.
- Test de ancho de banda de memoria compartida.

### Fase 2: El Motor V2V
- Script de optimización de modelos con Olive.
- Implementación de `StreamDiffusion` adaptado para DirectML.
- Pruebas de FPS base (Meta: >15 FPS iniciales).

### Fase 3: Integración OBS
- Configuración del servidor Spout2 en Python.
- Creación de la fuente de captura en OBS Studio.
- Sincronización de audio/video (Delay compensation).

---

## ⚠️ NOTAS DE SEGURIDAD Y ESTABILIDAD
- El sistema debe incluir un **Fail-safe** que conmute a la cámara real si el proceso de IA se detiene.
- Monitoreo térmico constante de la APU.
