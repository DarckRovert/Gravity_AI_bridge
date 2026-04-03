# ❓ Preguntas Frecuentes (FAQ) & Troubleshooting

**El menú me dice 🔴 Inactivo en todos mis proveedores, pero yo instalé LM Studio / Ollama.**
Asegúrate de que estás corriendo el servicio local.
- En **LM Studio:** Necesitas apretar el botón grande que dice "Start Server" en la pestaña de Local Server.
- En **Ollama:** El ícono de la alpaca debe estar blanco en la bandeja del sistema (abajo a la derecha en Windows).

---

**Gravity Bridge me marca "Modelo Externo" o tamaño 0.0 GB en algunos motores.**
Los motores compatibles con la API de OpenAI (como LM Studio o Jan) actualmente devuelven información sobre qué modelos están cargados en VRAM, pero **omiten el peso exacto en Bytes del modelo original** por limitaciones de la API oficial de OpenAI. Tu modelo funcionará a la perfección.

---

**¿Por qué VS Code (Continue.dev) o Cursor me dan error de API Key al usar el Bridge?**
El `bridge_server.py` no exige API keys reales, funciona de forma totalmente libre en Local. Sin embargo, todos los IDEs o plugins de IA son estrictos obligando a tener texto en ese campo. En la parte de **API Key pon siempre `gravity-local`** o la palabra "test". No lo dejes vacío.

---

**El comando `/leer-carpeta` cargó un archivo rarísimo y arrojó UnicodeDecodeError.**
El comando está fuertemente filtrado por código para leer solo `.js`, `.py`, `.json`, `.ts` y afines (ignorando Venvs, Git y fotos). Si metes un archivo malicioso, internamente usará `try/except` silencioso para ignorarlo sin caerse. Si falla, el archivo no entrará en el prompt, tu TUI seguirá funcionando perfecta.

---

**Comprimí el contexto con `!comprimir` y la IA parece haberse olvidado de mi nombre.**
La compresión usa un prompt instructivo que fuerza a la IA a resumir el "Código técnico y arquitectónico" ignorando saludos o charlas efímeras para ahorrar tokens. Si precisas datos ultra exactos guardados durante 100 turnos, te recomendamos usar el comando `!aprende [El dato que precises]` en vez de dejarlo a la suerte en la historia.
