# Troubleshooting y Preguntas Frecuentes (FAQ)

Esta guía te ayudará a resolver los problemas más comunes al operar Gravity AI (AgentShield V16.6).

## Preguntas Frecuentes (FAQ)

### ¿Por qué mi script/hook es bloqueado por AgentShield?
Si ves un error `PermissionError: AgentShield Core Protection blocked write attempt`, significa que el script intentó escribir en un área crítica protegida (ej: `core/`, `.agents/`, `.env`, `_settings.json`). Esta es una medida de seguridad (Ring 0) para evitar que el LLM modifique la arquitectura base o fugue secretos. Si necesitas escribir, asegúrate de que el script apunte a un directorio de trabajo válido como `scratch/` o un directorio de salidas específico.

### ¿Por qué mi comando de consola (shell) requiere aprobación pero los scripts Python no?
A partir de la Fase 16.5, los comandos directos a la terminal de Windows (`shell_exec`, `run_command`) son catalogados como **Herramientas de Alto Riesgo** por el `HITLManager` y bloquean la ejecución hasta que un humano lo aprueba (o lo rechaza automáticamente si corre en background). Los scripts Python (vía `code_runner`) corren en el **AST Sandbox** el cual restringe módulos peligrosos (como RCE de OS o Network Socket) en tiempo de compilación. Por ello gozan de autonomía completa.

### Gravity dice que "el hook no tiene una firma válida"
Mitigación CVE-2025-59536. Los archivos de Python en la carpeta `.agents/hooks/` deben estar registrados con su hash exacto en `%LOCALAPPDATA%\Gravity\hooks_trust.json`. Si editaste un hook manualmente, el hash cambió y el motor lo bloquea previniendo un ataque de envenenamiento de repositorio. Para arreglarlo, debes actualizar el hash en el archivo de confianza global.

## Troubleshooting

### Error: `No se pudo decodificar con utf-8, cp1252 ni latin-1`
A partir del filtro Unicode, el sistema lee con codificación estricta y purga caracteres invisibles. Si tu archivo contiene codificaciones corruptas extremas, asegúrate de guardar tus scripts de entrada puramente como UTF-8.

### La IA entra en un bucle intentando leer un archivo protegido
Revisa que en tus *prompts* o *skills* no estés pidiendo a la IA que inspeccione o deduzca variables leyendo el archivo `.env`. Este comportamiento está bloqueado intencionalmente para evitar fugas de secretos (*Secret Leak*). Las variables deben inyectarse por entorno, no dejar que la IA las lea desde disco.
