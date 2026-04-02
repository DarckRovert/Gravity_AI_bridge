# 📜 Protocolo de Integración: Gravity AI Bridge

Este archivo es una guía de persistencia para **cualquier asistente de IA (Antigravity, Claude, etc.)** que trabaje en este repositorio. Su objetivo es maximizar la eficiencia y reducir costos delegando tareas al modelo local.

---

## 🤖 El Sistema: Auditor Senior V2.1 (Multi-IA)
El proyecto ha evolucionado a una plataforma flexible:
- **Script Principal:** `ask_deepseek.py` (ahora con soporte multi-modelo).
- **Ajustes:** `_settings.json` (persistencia del modelo preferido).
- **Memoria:** `_history.json` (sesión) y `_knowledge.json` (reglas).

## 📡 Protocolo de Delegación (IA a IA)
Cuando Antigravity (o cualquier IA) delegue una tarea al Auditor local, se recomienda:
1. **Llamar al Auditor con argumentos** (Modo Agente): 
   `python ask_deepseek.py "TU PREGUNTA TÉCNICA"`
   - Esto activará la **respuesta en Inglés Técnico**, lo que optimiza la precisión lógica y reduce tokens innecesarios.
2. **Refinar en Español para el usuario:** Traduce o adapta la respuesta técnica del Auditor local para la entrega final.

## 🛠️ Comandos de Interfaz (Consola)
- `python ask_deepseek.py "/leer ruta/al/archivo"` -> Audita un archivo.
- `python ask_deepseek.py "!aprende regla"` -> Inyecta una regla permanente.
- `python ask_deepseek.py "!reglas"` -> Lista el conocimiento actual.

## ⚖️ Regla de Oro
**No consumas tokens de la nube innecesariamente.** Si una tarea puede ser resuelta por el Auditor Senior local, delégala primero. Solo usa los créditos del usuario para el refinamiento final o tareas que el modelo local no pueda resolver.

---
*Protocolo generado por Antigravity — Auditoría y Eficiencia ante todo.*
