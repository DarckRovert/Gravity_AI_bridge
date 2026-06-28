# Gravity UI (V16.14 PRO)

Este es el frontend oficial de **Gravity AI Bridge**. Construido con React, TypeScript y TailwindCSS, sirve como el centro de control táctico (Dashboard) para monitorear el enjambre de agentes y la telemetría del sistema en tiempo real.

## Arquitectura de UI
- **Framework:** React 18 + Vite
- **Estilos:** TailwindCSS (Cyberpunk/Dark Mode nativo)
- **Iconografía:** Lucide React
- **Comunicaciones:** 
  - `HTTP REST / SSE` para el núcleo del Gravity Bridge.
  - `WebSockets (Puerto 9999)` para conexión LAN directa y bidireccional con el bus sensorial de J.A.R.V.I.S.

## Módulos Principales
1. **Chat Inteligente:** Interfaz para el enjambre multi-agente (`Swarm`).
2. **Telemetría de Hardware:** Gráficas circulares para uso de RAM y VRAM de AMD.
3. **J.A.R.V.I.S Sensory Net (Nuevo):** Panel especializado para la interacción y monitoreo del flujo cognitivo del Asistente de Voz. Se conecta por WebSockets y permite la lectura de STT (Entrada), TTS (Salida) y el "Cognitive Loop" (Pensamiento) en tiempo real.

## Desarrollo
Para correr el entorno de desarrollo con Hot-Module-Replacement:
```bash
npm install
npm run dev
```

Para generar la compilación de producción optimizada (la cual servirá FastAPI):
```bash
npm run build
` 
