# 🌌 Gravity AI Bridge v10.0 [Diamond-Tier Edition]

![Version](https://img.shields.io/badge/Version-10.0_Stable-blueviolet?style=for-the-badge&logo=rocket)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge&logo=mit)
![Python](https://img.shields.io/badge/Python-3.9+-yellow?style=for-the-badge&logo=python)
![OS](https://img.shields.io/badge/OS-Windows_Direct-blue?style=for-the-badge&logo=windows)

**Gravity AI Bridge** es la vanguardia en orquestación de IA y gestión de infraestructura local-first. Diseñado por **DarckRovert**, este puente actúa como el núcleo inteligente que conecta tus procesos de juego (WoW), despliegues web (Netlify) y modelos de IA (Ollama/Cloud) en un entorno unificado, seguro y de alta latencia.

---

## 💎 Características Principales

### ⚔️ Game Server Manager (MaNGOS/vMaNGOS)
- **Control Unificado:** Arranca, detiene y monitoriza worldserver/realmd (MaNGOS/vMaNGOS/TrinityCore).
- **SRP-6a:** Portal de registro seguro integrado.
- **Exposure WAN:** Exposición automática a internet con balanceo de IPs públicas.
- **Monitoreo MySQL:** Observa jugadores online, niveles y clases en tiempo real.

### 🛡️ Security Monitor (Watchdog Zero-Trust)
- **Whitelists:** Monitoreo estricto de puertos TCP/UDP y procesos autorizados.
- **Integridad:** Verificación SHA-256 de binarios críticos.
- **Anti-Intrusión:** Notificaciones instantáneas (Toasts) ante accesos no autorizados.

### 🚀 Deploy Manager (CI/CD Local)
- **Pipeline Automatizado:** `npm build` → `Netlify deploy` con un solo click.
- **Streaming de Logs:** Depuración en tiempo real del proceso de build desde el Dashboard.

---

## 🛠️ Guía de Inicio Rápido

### Instalación
```cmd
git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
cd Gravity_AI_bridge
launchers\INSTALAR.bat
```

### Uso mediante CLI
```cmd
# Iniciar modo interactivo
gravity

# Procesar consulta directa
gravity "analiza este log: AttributeError: ..."

# Analizar archivos mediante Pipe
cat server.log | gravity "identifica errores críticos"
```

### Integración con Python SDK
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:7860/v1", api_key="gravity-local")

response = client.chat.completions.create(
    model="gravity-bridge-auto",
    messages=[{"role": "user", "content": "Estado del bridge?"}]
)
print(response.choices[0].message.content)
```

---

## 🖥️ Requisitos de Hardware y Software

- **S.O:** Windows 10/11 (Optimizado para DPAPI).
- **Python:** 3.9 o superior.
- **GPU (Opcional - Imagen):** Recomendado AMD con **HIP SDK** instalado.
    - **IMPORTANTE:** Instala `AMD-Software-PRO-Edition-26.Q1-Win11-For-HIP.exe` y **reinicia Windows** para habilitar la generación de imágenes por GPU.

---

## 📚 Documentación Técnica (Wiki)

Para detalles exhaustivos, consulta nuestra Wiki local:
- [**📖 Manual de Usuario**](wiki/Manual-Usuario.md): Instalación, Launchers, CLI y RAG.
- [**📡 Guía de API**](wiki/Guia-API.md): Referencia técnica de endpoints, JSON y métricas.
- [**🧱 Arquitectura**](wiki/Arquitectura.md): Deep-dive sobre DPAPI, WAL y orquestación.
- [**⚔️ Game Server Guide**](wiki/Game-Server-Guide.md): Configuración de WoW MaNGOS.

---

## 🤝 Contribución y Marca

Este proyecto sigue los lineamientos de **DarckRovert**.
- **Twitch:** [twitch.tv/darckrovert](https://twitch.tv/darckrovert)
- **GitHub:** [DarckRovert](https://github.com/DarckRovert)

---

## 📄 Licencia

Este proyecto está bajo la Licencia **MIT** (2026). Consulta el archivo [LICENSE](LICENSE) para más detalles.
