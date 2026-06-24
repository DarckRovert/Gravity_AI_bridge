import re
import markdown


def clean_markdown_and_html():
    md_path = r"f:\Gravity_AI_bridge\ensayos_generados\El_Sustrato_Primordial\El_Sustrato_Primordial.md"
    html_path = r"f:\Gravity_AI_bridge\ensayos_generados\El_Sustrato_Primordial\El_Sustrato_Primordial.html"

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Eliminar bloques de matemáticas $$ ... $$
    def replace_math(match):
        text = match.group(1)
        text = text.replace(r"\text{", "")
        text = text.replace("}", "")
        text = text.replace(r"\cap", " y ")
        text = text.replace(r"\Psi", "Psi")
        text = text.replace(r"\rightarrow", "->")
        text = text.replace("$$", "")
        return text

    content = re.sub(r"\$\$(.*?)\$\$", replace_math, content, flags=re.DOTALL)

    # Algunas veces LaTeX en línea usa $ ... $
    content = re.sub(r"\$(.*?)\$", replace_math, content)

    # Reemplazar encabezados h4 por negritas simples para evitar errores de tachado en Google Docs
    content = re.sub(r"^#### (.*?)$", r"**\1**", content, flags=re.MULTILINE)

    # Escribir el markdown limpio
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Generar HTML
    html_content = markdown.markdown(content, extensions=["toc"])
    full_html = (
        '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n</head>\n<body>\n'
        + html_content
        + "\n</body>\n</html>"
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    print("Markdown limpiado de símbolos raros y HTML regenerado.")


if __name__ == "__main__":
    clean_markdown_and_html()
