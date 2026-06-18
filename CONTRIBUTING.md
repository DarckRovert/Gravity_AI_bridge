# Guía de Contribución para Gravity AI Bridge

¡Gracias por tu interés en contribuir al ecosistema de Gravity AI!

## Reglas Invariantes
Toda contribución de código debe respetar estrictamente las reglas invariantes definidas en `core/autonomy_engine.py`:
1. Nunca exceder límites de costo de API codificados.
2. No comprometer la arquitectura HITL (Human-in-the-Loop).
3. Todo debe ser compatible con la ejecución local (offline-first o fallback local garantizado).

## Proceso de Pull Requests
1. Haz fork del proyecto y crea tu rama (`feature/nueva-habilidad`).
2. Añade documentación en la carpeta `/wiki` si alteras la arquitectura L0/L1/L2.
3. Envía el PR detallando el consumo de recursos y tiempo de procesamiento.
