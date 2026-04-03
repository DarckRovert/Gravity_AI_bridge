# 🔗 Guía de Integración con Entornos (IDEs)

Gravity AI V4 contiene el **Gravity Bridge Server**. Este servidor expone una API compatible con OpenAI en el puerto `7860`. Gracias a esto, puedes engañar a cualquier editor del mundo para que use tu hardware local en lugar de pagar.

## 🚀 Requisito Previo (Crucial)
Antes de configurar cualquier IDE, debes tener el servidor corriendo.
Haz doble clic en `INICIAR_SERVIDOR.bat`.
Debes ver el consolador diciendo: `► Base URL: http://localhost:7860/v1`

---

## 🔹 1. Continue.dev (VS Code / JetBrains)

Continue es la extensión más popular. Gravity puede auto-configurarla por ti.

**Opción Automática:**
1. Abre Gravity (`INICIAR_AUDITOR.bat`)
2. Escribe el comando: `!integrar continue`
3. Reinicia VS Code. Listo.

**Opción Manual:**
1. Abre el archivo `~/.continue/config.yaml`
2. Modifica o añade este modelo en la lista de `models:`
```yaml
  - name: "Gravity Proxy GPU"
    provider: openai
    model: gravity-bridge-auto
    apiBase: "http://localhost:7860/v1"
    apiKey: "gravity-local"
```

## 🔹 2. CodeGPT (VS Code)

1. Abre las opciones de CodeGPT en VS Code (Icono del chat > Settings).
2. Selecciona como Provider: **Custom OpenAI** (o simplemente Custom).
3. Configura los siguientes parámetros:
   - **Base URL:** `http://localhost:7860/v1`
   - **API Key:** `gravity-local`
   - **Model:** `gravity-bridge-auto`

## 🔹 3. Cody (Sourcegraph)

Cody es un poco más restrictivo, pero soporta LLMs custom vía su API gateway o si le pasas configuraciones de endpoint de OpenAI de forma local a través del archivo de settings avanzado de VSCode.

En tu `settings.json` de VSCode añade:
```json
"cody.experimental.customModels": [
  {
    "model": "gravity-bridge",
    "provider": "openai",
    "endpoint": "http://localhost:7860/v1",
    "key": "gravity-local"
  }
]
```

## 🔹 4. Cursor IDE

Cursor permite anular las URLs base de OpenAI muy fácilmente.

1. Abre **Cursor Settings** (engranaje arriba a la derecha).
2. Ve a la sección **Models**.
3. Baja hasta **OpenAI API Key** y pon: `gravity-local`.
4. Justo debajo dale a **Override OpenAI Base URL** y pega: `http://localhost:7860/v1`
5. Arriba en la barra de modelos de chat añade uno llamado `gravity-bridge-auto` y úsalo.

## 🔹 5. Aider (Terminal IDE)

Aider es una CLI pura hiper rápida.
**Opción Automática:**
`!integrar aider` dentro de Gravity AI.

**Opción Manual:**
En la raíz de tu proyecto, lanza aider redirigiendo la API:
```bash
aider --openai-api-base http://localhost:7860/v1 --model openai/gravity-bridge-auto
```

## 🔹 6. Cline (VsCode Extension) / Roo Code

Cline (la herramienta de IA automatizada) permite Providers "Custom" u "OpenAI Compatible":
1. Ve a los Settings de Cline.
2. API Provider: `OpenAI Compatible`.
3. Base URL: `http://localhost:7860/v1`
4. API Key: `gravity-local`
5. Model ID: `gravity-bridge-auto`
