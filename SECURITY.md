# Política de Seguridad — Gravity AI Bridge

## 🛡️ Nuestro Compromiso con la Seguridad

En Gravity AI Bridge, la seguridad de tus datos y la integridad de tu infraestructura son nuestra máxima prioridad. Dado que este software maneja credenciales críticas y acceso a procesos del sistema, aplicamos una arquitectura de **Confianza Cero** en el desarrollo de nuestras APIs internas.

## 🚀 Reporte de Vulnerabilidades

Si descubres una vulnerabilidad de seguridad en este proyecto, te pedimos que NO abras un Issue público. En su lugar, sigue este protocolo:

1.  **Envío Privado:** Envía un correo electrónico detallado a [seguridad@darckrovert.com].
2.  **Detalles:** Incluye una descripción del fallo, los pasos para reproducirlo y, si es posible, un script de prueba (PoC).
3.  **Respuesta:** Recibirás una respuesta de nuestro equipo en menos de 24 horas confirmando la recepción.

## 💎 Características de Seguridad de la V10.0

- **Cifrado DPAPI:** Todos los secretos (API Keys, tokens) se cifran mediante la Data Protection API nativa de Windows, vinculada a tu cuenta de usuario del sistema operativo.
- **Whitelist de Puertos:** El monitor de seguridad bloquea cualquier socket no autorizado explícitamente en la configuración.
- **Aislamiento de Procesos:** Los agentes operan con los privilegios mínimos necesarios para interactuar con los procesos de juego.

## 🏁 Alcance

Esta política cubre todos los archivos contenidos en este repositorio, incluyendo el servidor Bridge, el Dashboard Web y los gestores de procesos en la carpeta `core/`.

---
*Gracias por ayudarnos a mantener Gravity AI Bridge seguro para todos.*
