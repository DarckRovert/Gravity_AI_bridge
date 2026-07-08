"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — LaTeX Cleaner                                                 ║
║                                                                              ║
║   Limpia artefactos LaTeX residuales de texto generado por LLMs.            ║
║   Algunos modelos (especialmente los entrenados en papers académicos)        ║
║   tienden a insertar notación LaTeX en sus respuestas Markdown.             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import re


def full_clean(text: str) -> str:
    """
    Limpia texto Markdown de artefactos LaTeX y otros residuos de generación LLM.

    Transformaciones aplicadas:
      1. Fórmulas LaTeX display ($$...$$) → texto plano entre corchetes.
      2. Fórmulas LaTeX inline ($...$) → texto plano.
      3. Comandos LaTeX comunes (\textbf, \emph, \cite, etc.) → contenido sin markup.
      4. Entornos LaTeX (\\begin{...}...\\end{...}) → eliminados.
      5. Normalización de saltos de línea excesivos (>2 consecutivos → 2).
      6. Limpieza de espacios al inicio/fin de cada línea.
    """
    if not text:
        return ""

    # 1. Entornos LaTeX completos (equation, align, figure, table, etc.)
    text = re.sub(
        r"\\begin\{[^}]+\}.*?\\end\{[^}]+\}",
        "",
        text,
        flags=re.DOTALL,
    )

    # 2. Fórmulas display ($$...$$) — preservar el contenido legible si lo hay
    def _display_formula(m):
        inner = m.group(1).strip()
        # Si es muy corta, simplemente quitar los signos
        if len(inner) < 60:
            return f"[{inner}]"
        return ""

    text = re.sub(r"\$\$(.*?)\$\$", _display_formula, text, flags=re.DOTALL)

    # 3. Fórmulas inline ($...$) — preservar si son cortas y legibles
    def _inline_formula(m):
        inner = m.group(1).strip()
        if len(inner) < 40 and "\\" not in inner:
            return inner
        return f"[{inner}]" if len(inner) < 80 else ""

    text = re.sub(r"\$([^$\n]{1,100}?)\$", _inline_formula, text)

    # 4. Comandos LaTeX con argumento (\textbf{X} → X, \emph{X} → X, etc.)
    text = re.sub(
        r"\\(?:textbf|textit|emph|underline|textrm|texttt|textsc|text)\{([^}]*)\}",
        r"\1",
        text,
    )

    # 5. Comandos de cita (\cite{...}, \ref{...}) → eliminar
    text = re.sub(r"\\(?:cite|ref|label|footnote|href|url)\{[^}]*\}", "", text)

    # 6. Comandos LaTeX sueltos sin argumento (\newpage, \noindent, etc.)
    text = re.sub(
        r"\\(?:newpage|pagebreak|noindent|par|hfill|vfill|clearpage|centering|linebreak)\b",
        "",
        text,
    )

    # 7. Backslashes LaTeX residuales al inicio de línea (\\Item, \\section, etc.)
    text = re.sub(r"\\[a-zA-Z]+\{", "", text)
    text = re.sub(r"\\[a-zA-Z]+\b", "", text)

    # 8. Llaves LaTeX residuales
    text = re.sub(r"[{}]", "", text)

    # 9. Normalizar saltos de línea
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 10. Limpiar líneas con solo espacios
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()
