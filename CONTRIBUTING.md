# 🛠️ Guía de Contribución al Core de Gravity AI

¡Gracias por querer aportar al Ecosistema V5.1 de Gravity! El objetivo principal es mantener la UI de consola ultra-fluida y el Bridge proxy corriendo sin dependencias pesadas.

## Requisitos de Código (Hard Rules)
1. **Cero Dependencias Bloqueantes:** El proyecto se enorgullece de usar únicamente `urllib`, `socket` y librerías stdlib de Python para el servidor y llamadas. La única dependencia estética es `rich` y `pyfiglet`. **No se aceptarán frameworks masivos como Flask/FastAPI.**
2. **Compatibilidad Universal:** Todo el código CLI debe utilizar escapes ANSII transparentes y compatibilidad con `Cmd/PowerShell`. (Usar `os.name == 'nt'` inteligentemente).
3. **Resiliencia de JSON:** Nunca añadas mutaciones directas a JSON sin empaquetarlas en bloques de `try/except`. ¡La salvaguarda de datos es prioritaria!

## Añadir un Nuevo Motor a `provider_scanner.py`
Si ha surgido una nueva app en el mercado (como LM Studio o Jan), puedes añadirla rápidamente al escáner:

Simplemente dirígete a la clase `ProviderScanner` y fíjate en el array constante `KNOWN_PROVIDERS`. Añade un nuevo bloque de diccionario con el puerto oficial de esa herramienta, y si soporta la API de OpenAI pon su protocolo en `openai`. El puente enrutará y detectará ese motor de inmediato.

```python
    KNOWN_PROVIDERS = [
        {"name": "Ollama", "port": 11434, "protocol": "ollama"},
        {"name": "LM Studio", "port": 1234, "protocol": "openai"},
        {"name": "Tu Nueva App", "port": 9999, "protocol": "openai"}
    ]
```

## Sistema de Reporte de Errores (Issues)
Abre un ticket con tu stack (Ej: Ryzen 8700G, Windows 11, LM Studio versión X). Adjuntar el output del log del servidor Bridge que puedes capturar ejecutando `bridge_server.py` manualmente es esencial para rastrear el fallo en el proxy.
