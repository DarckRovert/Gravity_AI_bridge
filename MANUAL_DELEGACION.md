# 🤝 Manual de Delegación (Gravity AI V7.1 — Auditor-to-Local)

Si abres un chat de Inteligencia Artificial para trabajar en un **proyecto computacional completamente distinto** (y la IA en la nube no recuerda nada sobre cómo está estructurado tu sistema de auditoría local), puedes obligarla a canalizar sus algoritmos a través de tu **propia GPU y tu hardware DeepSeek-R1**.

Siguiendo este manual conectarás la inteligencia de tu IDE o de un chat fresco (como Antigravity) directamente a tu terminal.

---

## 🏗️ Preparación (Una sola vez por proyecto)

La Inteligencia Artificial en la nube sabe qué herramientas usar porque lee las variables de entorno de sus áreas de trabajo. Debes darle "las instrucciones".

1. Dirígete a la carpeta raíz de tu software **Gravity_AI_bridge**.
2. Copia la carpeta oculta **`.agents`** (completa, con sus flujos de trabajo adentros).
3. Pégala en la carpeta raíz de tu **Nuevo Proyecto** (el que vayas a programar).

---

## 🎯 Testeo: Qué decirle al Nuevo Chat

Abre la conversación en tu nuevo entorno de trabajo. Todo lo que tienes que escribirle es lo siguiente usando tu slash-command activador:

> `/delegar Revisa las fallas de mi código actual en network.py, y entrégame la solución directamente desde mi máquina.`

**¿Qué sucederá tras bambalinas?**
* El Chat interceptará el comando `/delegar` y leerá silenciosamente el manual oculto en `.agents/workflows/delegar.md`.
* Conocerá la existencia de un comando global llamado `gravity`.
* Ejecutará una línea de CMD como: `type network.py | gravity "Busca errores de sintaxis y retorna la refactorización"`.
* Tu propio equipo físico (Ollama / DeepSeek) tomará la antorcha, pensará la solución y la escupirá de vuelta hacia el puente.
* El Chat finalmente formateará la respuesta y te la entregará visualmente perfecta.

### Método Alternativo (Si no quieres copiar archivos)
Si simplemente no deseas arrastrar la carpeta `.agents` a tus nuevos proyectos, también puedes darnos la orden directa e imperativa en tu primer prompt:

> *"Usa tu terminal integrada para inyectar este archivo a mi inteligencia de escritorio. Usa el comando: `type src\main.js | gravity "corrige las importaciones de React"` y muéstrame exactamente lo que te responda."*
