"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — LaTeX Cleaner V1.0                                           ║
║   Módulo centralizado de limpieza LaTeX → Unicode/texto plano.              ║
║   Reutilizable por research_writer.py, fix_final_html.py y cualquier        ║
║   pipeline de post-procesamiento de texto generado por LLM.                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import re

# ── Mapa de comandos LaTeX → Unicode ─────────────────────────────────────────
_LATEX_UNICODE_MAP = {
    r"\Sigma":   "Σ",
    r"\sigma":   "σ",
    r"\Psi":     "Ψ",
    r"\psi":     "ψ",
    r"\Delta":   "Δ",
    r"\delta":   "δ",
    r"\Omega":   "Ω",
    r"\omega":   "ω",
    r"\Lambda":  "Λ",
    r"\lambda":  "λ",
    r"\Alpha":   "Α",
    r"\alpha":   "α",
    r"\Beta":    "Β",
    r"\beta":    "β",
    r"\Gamma":   "Γ",
    r"\gamma":   "γ",
    r"\Phi":     "Φ",
    r"\phi":     "φ",
    r"\Theta":   "Θ",
    r"\theta":   "θ",
    r"\Pi":      "π",
    r"\pi":      "π",
    r"\mu":      "μ",
    r"\nu":      "ν",
    r"\rho":     "ρ",
    r"\tau":     "τ",
    r"\chi":     "χ",
    r"\xi":      "ξ",
    r"\eta":     "η",
    r"\infty":   "∞",
    r"\to":      "→",
    r"\rightarrow": "→",
    r"\leftarrow":  "←",
    r"\Rightarrow": "⇒",
    r"\Leftarrow":  "⇐",
    r"\leq":     "≤",
    r"\geq":     "≥",
    r"\neq":     "≠",
    r"\approx":  "≈",
    r"\cdot":    "·",
    r"\times":   "×",
    r"\div":     "÷",
    r"\pm":      "±",
    r"\subset":  "⊂",
    r"\supset":  "⊃",
    r"\cup":     "∪",
    r"\cap":     "∩",
    r"\forall":  "∀",
    r"\exists":  "∃",
    r"\partial": "∂",
    r"\nabla":   "∇",
    r"\sum":     "Σ",
    r"\prod":    "Π",
    r"\int":     "∫",
    r"\sqrt":    "√",
}


def clean(text: str) -> str:
    """
    Limpia todo el LaTeX de un texto generado por LLM.
    Convierte comandos a Unicode donde es posible y elimina el resto.
    Preserva el texto semántico intacto (no elimina contenido, solo notación).
    """
    if not text:
        return text

    # 0. Limpiar tags de razonamiento del LLM (<think>...</think>)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

    # 1. Reemplazar comandos con argumentos de texto: \text{...} → el contenido
    text = re.sub(r'\\text\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\mathrm\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\mathbf\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\mathit\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\operatorname\{([^}]*)\}', r'\1', text)

    # 2. Reemplazar \frac{num}{den} → num/den
    text = re.sub(r'\\frac\{([^}]*)\}\{([^}]*)\}', r'\1/\2', text)

    # 3. Reemplazar comandos conocidos → Unicode
    for latex_cmd, unicode_char in _LATEX_UNICODE_MAP.items():
        text = text.replace(latex_cmd, unicode_char)

    # 4. Subíndices y superíndices: _{...} → _texto  |  ^{...} → ^texto
    text = re.sub(r'_\{([^}]*)\}', r'_\1', text)
    text = re.sub(r'\^\{([^}]*)\}', r'^\1', text)
    # Subíndices simples sin llaves: _x → _x (ya es legible, no tocar)

    # 5. Eliminar bloques matemáticos $$ ... $$ (multilínea)
    text = re.sub(r'\$\$.*?\$\$', '', text, flags=re.DOTALL)

    # 6. Eliminar $ ... $ cuando contiene comandos LaTeX
    #    (NO tocar $ cuando es símbolo de moneda, ej: "$50 millones")
    def _clean_inline_math(m):
        inner = m.group(1)
        # Si contiene comandos LaTeX o variables matemáticas, limpiar
        if re.search(r'\\|_{|}|[A-Z][a-z]?_{', inner):
            return inner  # devolver el contenido sin los $
        # Si parece símbolo de dinero (dígitos cerca), preservar
        return m.group(0)

    text = re.sub(r'\$([^$\n]{1,200}?)\$', _clean_inline_math, text)

    # 7. Eliminar entornos LaTeX residuales: \begin{...} ... \end{...}
    text = re.sub(r'\\begin\{[^}]*\}.*?\\end\{[^}]*\}', '', text, flags=re.DOTALL)

    # 8. Eliminar comandos LaTeX restantes desconocidos: \comando
    #    Solo los que no son parte de un path de Windows (ej: \Users)
    text = re.sub(r'\\(?!Users|[A-Z]:\\)[a-zA-Z]+', '', text)

    # 9. Limpiar llaves sueltas residuales
    text = re.sub(r'\{([^}]*)\}', r'\1', text)

    # 10. Normalizar espacios múltiples (sin tocar newlines)
    text = re.sub(r'[ \t]{2,}', ' ', text)

    return text


def clean_markdown_tables(text: str) -> str:
    """
    Asegura que todas las tablas Markdown tengan una línea en blanco antes
    para que el parser las reconozca correctamente.
    """
    # Agregar línea en blanco antes de filas de tabla si no existe
    text = re.sub(r'([^\n])\n(\s*\|)', r'\1\n\n\2', text)
    return text


def full_clean(text: str) -> str:
    """
    Pipeline completo: limpieza LaTeX + normalización de tablas Markdown.
    Usar este método en el pipeline de generación de libros.
    """
    text = clean(text)
    text = clean_markdown_tables(text)
    return text
