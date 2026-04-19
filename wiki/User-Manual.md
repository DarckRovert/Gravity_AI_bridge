# 📖 Manual de Usuario Simplificado (Gravity Bridge Dashboard)

Para el usuario general que no codifica en Python pero debe utilizar las bondades de automatización difusiva.

## Uso del Panel Central (Viendo Endpoints V10.1)

1. **Ejecutar el Servidor Base**: Doble-click en `GravityBridge_Launcher.pyw`. Esto carga silenciosamente:
   - Tu monitor de Puertos (Filtro Antihack).
   - VRAM Optimizer (Detecta si usas Ollama para chat).
   - El túnel HTTP local `http://localhost:7860`.

2. **Panel Web Front-end**:
   Entra libremente a tu navegador `http://127.0.0.1:7860`.
   Allí dispondrás de paneles que hacen ping a los APIs recién declarados:
   - **World Of Warcraft Controls**: Start/Stop. Si la DB MySQL está apagada, un cartel de pre-flight test te botará advirtiéndose para evitar una catástrofe silenciosa de tu server. (Tus backups se guardan secretamente en `/saves/` al apagar el servidor).
   - **Agent Chat**: Tipearás a tus LLMs instalados listados con tu hardware vivo.
   - **Fooocus Queue**: Manda imágenes. ¡Ahora no necesitas parchar el error CP1252 manual! La IA se encargará de purgar los símbolos y entregarte el JPG final rastreándolo pasivamente.
