# 🛰️ ULTRA MASTER PLAN — GRAVITY AI BRIDGE V16.0 PRO
## Operación Aletheia-V2V + Multigenerador IA (AMD EDITION)

> **Generado el:** 2026-05-12  
> **Basado en:** Auditoría directa del código fuente. Sin suposiciones.

---

## 📋 ESTADO REAL DEL SISTEMA (POST-AUDITORÍA)

| Componente | Estado Real | Archivo |
|---|---|---|
| Motor de imágenes | ✅ Flux via Pollinations.ai (cloud, sin API key) | `tools/pollinations_generator.py` |
| Pipeline de video | ✅ Modularizado en `/core/video/` con capa Bridge retrocompatible | `/core/video/` y `core/video_pipeline.py` |
| Consistencia visual | ✅ `_extract_visual_anchor()` implementado | `core/video_pipeline.py:624` |
| ComfyUI portable | ✅ Instalado en `_integrations/ComfyUI_windows_portable/` | — |
| ComfyUI custom node | ✅ `ComfyUI-LTXVideo` instalado | `custom_nodes/ComfyUI-LTXVideo/` |
| ComfyUI client | ✅ Implementado | `_integrations/comfy_client.py` |
| Animation Engine L2 | ✅ Código implementado, fallback a L1 activo | `core/animation_engine.py:303` |
| ComfyUI habilitado | ❌ `comfyui.enabled: false` en config | `config.yaml:124` |
| Modelos en ComfyUI | ❌ Carpeta `models/` completamente vacía | `ComfyUI/models/` |
| Motor V2V (stream) | ❌ No existe ningún módulo | — |
| Spout2 / DirectML | ❌ No instalados | — |
| Fooocus | ⚠️ CPU-only, sin API REST activa | `_knowledge.json:74` |
| `onnxruntime` | ⚠️ Versión CPU (RAG). DirectML requiere venv aislado | `requirements.txt:15` |
| Frontend | ✅ React + Vite, 26 componentes | `frontend/src/components/` |

---

## 🎯 TRES OBJETIVOS

### A — Activar Pipeline L2 (ComfyUI)
El código ya existe. Solo faltan modelos y activar el flag.

### B — Motor V2V Tiempo Real (AMD Ryzen 7 8700G)
Infraestructura 0%. Entorno virtual aislado obligatorio.

### C — Consistencia Visual Inter-Escena (Image-to-Prompt)
`_extract_visual_anchor()` existe pero es solo texto. Necesita cierre visual.

---

## 🚀 FASES

### FASE 0 — Diagnóstico Hardware (~30 min)
1. Verificar drivers AMD Adrenalin 23.x+
2. Confirmar DDR5 en Dual Channel
3. Verificar UMA Framebuffer BIOS (mínimo 8GB iGPU)
4. Test `run_cpu.bat` de ComfyUI sin errores

### FASE 1 — Activar ComfyUI L2 (~2-4h)
1. Descargar SD 1.5 → `ComfyUI/models/checkpoints/`
2. Descargar LTX-Video `ltx-video-2b-v0.9.5.safetensors` → `models/diffusion_models/`
3. Activar `comfyui.enabled: true`, `animation_level: 2` en `config.yaml`
4. Crear `run_amd_cpu.bat` en ComfyUI portable
5. Registrar en `ai_process_manager`
6. Test: job video con `animation_level=2` genera clip real

### FASE 2 — Image-to-Prompt (~1-2 días)
1. Instalar `ComfyUI-moondream2` o `ComfyUI-WD14-tagger`
2. Crear `_integrations/workflow_img2prompt.json`
3. Implementar `_get_scene_visual_context()` en `video_pipeline.py`
4. Integrar en loop de generación de escenas

### FASE 3 — Motor V2V AMD DirectML (~3-5 días)
Estructura:
```
_integrations/v2v_engine/
  env/            ← venv aislado (onnxruntime-directml, opencv)
  models/         ← SD1.5 Turbo ONNX FP16 + ControlNet ONNX FP16
  v2v_pipeline.py ← Captura 384x384 → inferencia → Spout2/VirtualCam
  v2v_server.py   ← WebSocket:7861 control de estilo en vivo
  optimize_models.py ← Conversión .safetensors → .onnx (Microsoft Olive)
  run_v2v.bat     ← Launcher aislado
```
Nuevos: `V2VStudio.tsx` en frontend + rutas `/v1/v2v/*` en bridge server.

---

## ⚠️ RESTRICCIONES CRÍTICAS

- `onnxruntime-directml` **NUNCA** en el entorno principal — rompe el RAG
- Fooocus no tiene API REST — no usable como backend de imágenes
- Spout2 requiere instalación de sistema — fallback a OBS VirtualCam
- NPU (Ryzen AI) es experimental para ControlNet — fallback a iGPU

---

## 📌 ORDEN DE EJECUCIÓN
```
FASE 0 → FASE 1 → FASE 2 → FASE 3
```
No saltarse Fase 0. Si DirectML no funciona, Fase 3 no tiene sentido.
