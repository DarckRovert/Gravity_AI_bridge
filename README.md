# 🌌 Gravity AI Bridge v10.0 [Diamond-Tier Edition]

![Version](https://img.shields.io/badge/Version-10.0_Stable-blueviolet?style=for-the-badge&logo=rocket)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge&logo=mit)
![Python](https://img.shields.io/badge/Python-3.9+-yellow?style=for-the-badge&logo=python)
![OS](https://img.shields.io/badge/OS-Windows_Direct-blue?style=for-the-badge&logo=windows)

**Gravity AI Bridge** es una plataforma de orquestación de IA y gestión de infraestructura de alto rendimiento, diseñada específicamente para el ecosistema de servidores privados (WoW) y automatización de despliegues web. Desarrollado por **DarckRovert**, esta versión 10.0 representa el pináculo de la estabilidad y la integración "Local-First".

---

## 💎 Características Principales

### ⚔️ Game Server Manager (MaNGOS/vMaNGOS)
Control absoluto sobre tu infraestructura de juego con soporte nativo para **SRP-6a**.
- **Gestión de Cuentas:** Registro y auditoría de cuentas con firewall integrado.
- **Exposure WAN:** Exposición segura a internet mediante reglas nativas y monitorización de IP pública.
- **Control SOAP:** Consola GM integrada para envío de comandos remotos.
- **Auto-Restart:** Vigilancia de procesos `mangosd` y `realmd` con autorecuperación en ms.

### 🛡️ Security Monitor (Vigilancia Activa)
Un agente de seguridad incesante que protege la integridad del entorno.
- **Whitelist de Puertos:** Monitoreo en tiempo real de sockets abiertos (TCP/UDP), detectando intrusiones inmediatamente.
- **File Integrity:** Hash-checking (SHA-256) de archivos críticos para prevenir manipulaciones.
- **Process Guard:** Detección de procesos sospechosos y monitoreo de consumo anómalo de recursos.

### 🚀 Deploy Manager (CICD Integrado)
Automatización del ciclo de vida de tus aplicaciones web.
- **Pipeline Netlify:** npm build → auditoría → despliegue automático con un solo click.
- **Logging Real-time:** Seguimiento visual del progreso de compilación directamente en el Dashboard.

### 📊 Dashboard Holístico
Interfaz web premium construida con Vanilla JS/CSS para máxima velocidad y sin dependencias pesadas.
- **Chat Auditor:** Interacción directa con el motor de IA para análisis del sistema.
- **Vision Studio:** Integración directa con Fooocus/Ollama para generación de assets.
- **Métricas de Latencia:** Gráficos dinámicos de respuesta del proveedor de IA.

---

## 🏗️ Arquitectura del Sistema

El sistema opera bajo un modelo de **Micro-Kernel de Orquestación**, donde el `bridge_server.py` centraliza la lógica y delega a agentes autónomos:

1.  **Core Internal:** Gestión de persistencia (SQLite con WAL mode), caché inteligente y limitadores de tasa.
2.  **Hardware Layer (DPAPI):** Cifrado de nivel militar de Windows para secretos y llaves de API.
3.  **Web Interface:** Servidor dinámico asíncrono que sirve el Dashboard con capacidades de *Hot-Reload*.

---

## 🛠️ Instalación Rápida

1. **Clonar Repositorio:**
   ```bash
   git clone https://github.com/DarckRovert/Gravity_AI_bridge.git
   ```
2. **Dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Lanzamiento:**
   Ejecutar `launchers/INICIAR_TODO.bat` o iniciar manualmente:
   ```bash
   python bridge_server.py
   ```

---

## 📋 Requisitos del Sistema

- **SRE:** Python 3.9 o superior.
- **Servidor:** Windows 10/11 (Optimizado para latencia nativa).
- **IA:** Acceso a proveedores locales (Ollama/LM Studio) o Cloud (Anthropic/OpenAI).

---

## 🤝 Contribución y Soporte

Las contribuciones son bienvenidas. Por favor, revisa [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir un Pull Request.

- **Autor:** [DarckRovert](https://github.com/DarckRovert)
- **Twitch:** [twitch.tv/darckrovert](https://twitch.tv/darckrovert)

---

## 📄 Licencia

Este proyecto está bajo la Licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---
*Gravity AI Bridge: El futuro de la orquestación inteligente está aquí.*
