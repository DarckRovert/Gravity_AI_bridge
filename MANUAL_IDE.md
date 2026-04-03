# Integración de Gravity AI Bridge con IDEs

Gravity AI Bridge intercepta de forma transparente el tráfico de Inteligencia Artificial para enviarlo directo a tu modelo local.

Cuando envías el comando `!integrar` desde la consola o ejecutas el instalador, el Bridge crea los "planos de arquitectura" (`.json` y `.yaml`) necesarios para configurar los 3 IDEs principales del mercado. 

La integración funciona a través de un estándar universal compatible con OpenAI, apuntando la IP hacia nuestro Server local (`http://localhost:7860/v1`).

Sigue estas sencillas instrucciones para conectar tu IDE preferido:

---

## 1. VS Code + Continue.dev

Continue.dev es la extensión líder de inteligencia artificial para VS Code.

**Paso a paso:**
1. Instala la extensión **Continue** en Visual Studio Code.
2. Haz clic en el ícono de Continue en la barra lateral izquierda.
3. Haz clic en la rueda de engranaje (⚙️ Settings) abajo a la derecha de Continue para abrir su `config.json`.
4. Busca la sección `"models": [` y pega nuestro bloque de configuración. El resultado debe verse parecido a esto:

```json
  "models": [
    {
      "title": "Gravity Bridge",
      "provider": "openai",
      "model": "gravity-bridge-auto",
      "apiBase": "http://localhost:7860/v1",
      "apiKey": "gravity"
    }
  ]
```
5. Guarda el archivo. Selecciona "Gravity Bridge" en el desplegable de Continue y voilá, ya estás conectado.

>*Nota técnica: Nuestro comando te genera un archivo de referencia en `Gravity_AI_bridge/.continue/config.yaml`, puedes copiar la información directamente de allí si prefieres usar su nuevo formato YAML.*

---

## 2. Cursor IDE

Cursor es un editor de código inteligente diseñado desde cero alrededor de IA.

**Paso a paso:**
1. Abre **Cursor IDE**.
2. Dale a la rueda de engranaje (⚙️ Cursor Settings) ubicada en la esquina superior derecha o mediante el menú.
3. Ve a la pestaña **Models**.
4. Dirígete a la sección inferior llamada **OpenAI API Key** y marca el toggle:
   * **Base URL:** `http://localhost:7860/v1`
   * **API Key:** `gravity`
5. Arriba, en la lista de modelos de Cursor, asegúrate de activar un modelo personalizado y llamarlo explícitamente `gravity-bridge-auto`.
6. Selecciona el modelo. La pantalla mostrará que la conexión ha sido enrutada a través del Gravity Server.

---

## 3. Aider (CLI Coder)

Aider es la mejor herramienta de terminal para refactoring guiado por IA. Funciona ejecutándose desde cualquier consola apuntando al backend.

**Paso a paso:**
1. Instala aider: `pip install aider-chat`
2. Si prefieres la configuración automática, nuestro puente crea un archivo `aider.conf.yml` en la carpeta `Gravity_AI_bridge`.
3. Alternativamente, simplemente lanza Aider desde la misma terminal que Gravity con el siguiente comando expreso:
```bash
aider --openai-api-base http://localhost:7860/v1 --model openai/gravity-bridge-auto --openai-api-key gravity
```

---

### ¿Cómo sé si funciona?

Abre nuestro **Gravity Bridge Server** haciendo doble clic en `INICIAR_SERVIDOR.bat`.
Debes dejar la pantalla negra abierta de fondo. Cada vez que le pidas algo a VS Code o Cursor, verás la solicitud imprimiéndose en verde atravesando la "malla interna" del servidor en vivo.
