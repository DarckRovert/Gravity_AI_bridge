# 🌌 Gravity AI Bridge V7.1 — Omni-Tier Architecture

[![Status](https://img.shields.io/badge/Status-Official_Release-blue?style=for-the-badge)](https://claseabc.netlify.app)
[![Version](https://img.shields.io/badge/Version-V7.1_Omni--Tier-magenta?style=for-the-badge)](https://claseabc.netlify.app)
[![Hardware](https://img.shields.io/badge/Hardware-Tri--Hybrid_(CPU/GPU/NPU)-green?style=for-the-badge)](https://claseabc.netlify.app)

**Gravity AI Bridge** es el orquestador de inteligencia artificial local definitivo. Diseñado para desarrolladores senior que exigen privacidad total, latencia ultra-baja y aprovechamiento máximo del silicio moderno (NPU/GPU). Intercepta peticiones de IDEs (Cursor, Aider, Continue) y las enruta inteligentemente hacia tu hardware local o nubes seguras.

---

## 🚀 Características God-Tier (V7.1)

- **⚡ Aceleración Tri-Híbrida**: Primer bridge local que utiliza simultáneamente **CPU**, **GPU (ROCm/DirectML)** y el **NPU (Ryzen AI/XDNA)** para offloading de tareas.
- **🛡️ Protocolo Omni-Audit**: Sistema de auditoría técnica que inyecta instrucciones de razonamiento matemático y detección de vulnerabilidades en cada consulta.
- **🌐 Proxy Universal**: Emulación perfecta del API de OpenAI en `localhost:7860/v1` para integración instantánea con cualquier herramienta de terceros.
- **📦 Motor RAG (AI Search)**: Indexación semántica ultra-rápida de repositorios completos utilizando el NPU para generar embeddings sin tocar el rendimiento del chat.
- **📊 Hardware Profiler**: Telemetría dinámica que calcula el `num_ctx` óptimo basado en tu VRAM real y tipo de cuantización (Q8/Q4).

---

## 🛠️ Instalación y Configuración

### 1. Requisitos Previos
- **AMD Ryzen AI** (7840U/8840HS o superior) o **NVIDIA RTX 30+**.
- **Python 3.14+** (Configurado para UTF-8 nativo).
- **Controladores Adrenalin 23.9.1+** (Para soporte de IPU/NPU).

### 2. Despliegue Rápido
```powershell
# Clonar y preparar entorno
git clone https://github.com/DarckRovert/Gravity_AI_bridge
cd Gravity_AI_bridge

# Activar acelerador NPU (Ryzen AI)
python setup_npu.py

# Iniciar servidor Bridge
python bridge_server.py
```

### 3. Integración en IDE (Cursor/Aider)
Configura tu Base URL como: `http://localhost:7860/v1` y usa el comando `!info` en la terminal de Gravity para ver los modelos activos.

---

## 📂 Estructura del Ecosistema

- `/providers`: Controladores inteligentes para Ollama, LM Studio y VLLM.
- `/rag`: Motor de búsqueda semántica optimizado para NPU.
- `/wiki`: Documentación profunda sobre arquitectura y seguridad.
- `ask_deepseek.py`: Frontend Senior personalizado con auditoría Omni-Audit.
- `hardware_profiler.py`: El cerebro de detección de hardware.

---

## 📄 Licencia y Contribución

Este proyecto está bajo la **Licencia MIT**. Si deseas contribuir, por favor revisa nuestro [CONTRIBUTING.md](CONTRIBUTING.md).

---
*Desarrollado por el ecosistema **Antigravity** & **DarckRovert**.*
*Sitio Oficial:* [claseabc.netlify.app](https://claseabc.netlify.app)
