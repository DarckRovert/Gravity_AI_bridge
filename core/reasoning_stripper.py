"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI — REASONING STRIPPER V10.0                                ║
║         Módulo compartido para eliminar bloques de pensamiento interno       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Extracción DRY de la clase ReasoningStripper previamente duplicada en
bridge_server.py y ask_deepseek.py.

Elimina los bloques de razonamiento interno de los modelos que los emiten
(DeepSeek-R1, QwQ, etc.) para entregarle al usuario únicamente la respuesta
limpia.

Etiquetas reconocidas:
  - <think>...</think>         (DeepSeek R1, estándar)
  - <|canal|>pensamiento...    (variantes internas locales)
  - <channel|>                 (cierre de variante interna)
"""


class ReasoningStripper:
    """
    Procesador de chunks de streaming que filtra bloques de razonamiento
    interno de los modelos de IA.

    Diseñado para uso stateeful en streaming: instanciar una vez por request
    y llamar process_chunk() por cada fragmento recibido.

    Uso:
        stripper = ReasoningStripper()
        for chunk in stream:
            clean = stripper.process_chunk(chunk)
            if clean:
                yield clean
    """

    def __init__(self):
        self.in_reasoning = False
        self.buffer       = ""
        self.start_tags   = ["<think>", "<|canal|>pensamiento"]
        self.end_tags     = ["</think>", "<channel|>"]

    def process_chunk(self, text: str) -> str:
        """
        Procesa un fragmento de texto y retorna la parte visible (sin
        bloques de razonamiento). Mantiene estado entre llamadas para
        manejar tags que se parten entre chunks.
        """
        self.buffer += text
        output = ""

        while self.buffer:
            if not self.in_reasoning:
                # Buscar el inicio de un bloque de razonamiento más cercano
                closest_start = -1
                for tag in self.start_tags:
                    pos = self.buffer.find(tag)
                    if pos != -1 and (closest_start == -1 or pos < closest_start):
                        closest_start = pos

                if closest_start != -1:
                    output += self.buffer[:closest_start]
                    self.buffer = self.buffer[closest_start:]
                    matched_tag = next(
                        (t for t in self.start_tags if self.buffer.startswith(t)),
                        None
                    )
                    if matched_tag:
                        self.buffer = self.buffer[len(matched_tag):]
                        self.in_reasoning = True
                else:
                    # Sin tag de inicio — verificar si el buffer termina con
                    # prefijo parcial de un tag (puede completarse en el
                    # siguiente chunk)
                    if any(tag.startswith(self.buffer[-1:]) for tag in self.start_tags):
                        break
                    output += self.buffer
                    self.buffer = ""
            else:
                # Dentro de un bloque de razonamiento — buscar cierre
                closest_end = -1
                for tag in self.end_tags:
                    pos = self.buffer.find(tag)
                    if pos != -1 and (closest_end == -1 or pos < closest_end):
                        closest_end = pos

                if closest_end != -1:
                    self.buffer = self.buffer[closest_end:]
                    matched_tag = next(
                        (t for t in self.end_tags if self.buffer.startswith(t)),
                        None
                    )
                    if matched_tag:
                        self.buffer = self.buffer[len(matched_tag):]
                        self.in_reasoning = False
                else:
                    # Sin cierre todavía — descartar buffer actual y esperar
                    self.buffer = ""
                    break

        return output

    def reset(self) -> None:
        """Reinicia el estado del stripper para reutilización."""
        self.in_reasoning = False
        self.buffer       = ""
