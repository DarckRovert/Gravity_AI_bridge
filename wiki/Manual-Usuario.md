# 📖 Gravity AI Bridge — User Manual / Manual de Usuario

Welcome to the ultimate guide for **Gravity AI Bridge V7.1**. This document covers everything from hardware acceleration to IDE integration.

Bienvenido a la guía definitiva de **Gravity AI Bridge V7.1**. Este documento cubre todo, desde la aceleración de hardware hasta la integración con IDEs.

---

## 🛠️ Installation / Instalación

### [ES] Paso 1: Prerequisitos
- **Python 3.14+** instalado.
- Para aceleración NPU: Drivers **AMD Ryzen AI Software 1.7.1+**.
- Para aceleración GPU: **NVIDIA CUDA 12+** o **AMD ROCm/DirectML**.

### [EN] Step 1: Prerequisites
- **Python 3.14+** installed.
- For NPU acceleration: **AMD Ryzen AI Software 1.7.1+** drivers.
- For GPU acceleration: **NVIDIA CUDA 12+** or **AMD ROCm/DirectML**.

---

## 🚀 Deployment / Despliegue

### [ES] Iniciar el Bridge
```powershell
# Ejecuta el servidor principal
python bridge_server.py
```
El servidor estará disponible en `http://localhost:7860/v1`.

### [EN] Start the Bridge
```powershell
# Run the main server
python bridge_server.py
```
The server will be available at `http://localhost:7860/v1`.

---

## 🏗️ IDE Integration / Integración con IDEs

### [ES] Cursor / Aider / Continue
1. Configura el **Model Provider** como `OpenAI-Compatible`.
2. Establece la **Base URL** en `http://localhost:7860/v1`.
3. Para la API Key, usa cualquier texto (ej. `gravity-71`) si no has configurado una llave cloud.

### [EN] Cursor / Aider / Continue
1. Set the **Model Provider** to `OpenAI-Compatible`.
2. Set the **Base URL** to `http://localhost:7860/v1`.
3. For the API Key, use any text (e.g., `gravity-71`) if no cloud key is configured.

---

## ⚖️ License / Licencia

**Strictly Non-Commercial**: This software is owned by **DarckRovert**. Commercial use for profit is prohibited.

**Estrictamente No-Comercial**: Este software es propiedad de **DarckRovert**. El uso comercial con fines de lucro está prohibido.
