# 🌐 Spanish Localization / Localización y Reglas de Idioma (G-PROT V7.1)

Este proyecto ha sido programado con **identidad Latinoamericana/Hispana nativa**.
A diferencia de todos los envoltorios (Wrappers) genéricos escritos en Inglés anglosajón, el ecosistema de **Gravity AI** usa prompts nativos, UI y control de errores fuertemente adaptados al español técnico.

## Filosofía del System Prompt Nativo
Todas nuestras inyecciones de contexto incluyen el override base:
`"Responde en ESPAÑOL. Riguroso y experto."`
Esto obliga a los modelos multilingües (DeepSeek, LLaMa-3, Qwen) a desactivar el sesgo inglés y entregar terminología técnica con gramática superior.

## Mantenimiento
Si decides realizar un fork de este código, siéntete libre de modificar la variable `language` e internacionalizar el texto enriquecido (Rich Text) de `ask_deepseek.py`. No obstante, el Core mantendrá su base documentada íntegramente en Español.
