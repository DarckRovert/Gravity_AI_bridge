import os
import re
import base64
import markdown

book_dir = r"f:\Gravity_AI_bridge\ensayos_generados\Convergencia_Entropica"
md_file = os.path.join(book_dir, "Convergencia_Entropica.md")
html_file = os.path.join(book_dir, "Convergencia_Entropica.html")
cover_path = os.path.join(book_dir, "cover.png")

with open(md_file, "r", encoding="utf-8") as f:
    md_content = f.read()


def clean_latex(text):
    text = text.replace(r"\frac{1}{T", "1 / {T")
    text = text.replace(r"\frac{1}", "1 / ")
    text = text.replace(r"\to", "->")
    text = text.replace(r"$t$", "t")
    text = text.replace(r"$E_{at}$", "E_at")
    text = text.replace(r"T$", "T")
    text = text.replace(r"_{at}", "_at")
    text = text.replace(r"\Sigma", "Σ")
    text = text.replace(r"\Psi", "Ψ")
    text = text.replace(r"\Delta", "Δ")
    text = text.replace(r"\rightarrow", "->")
    text = text.replace(r"\text{T}_{\text{max}}", "T_max")
    text = text.replace(r"\text{T}", "T")
    text = text.replace(r"\text{max}", "max")
    text = text.replace(r"T_{crit}", "T_crit")
    text = text.replace("$$", "")
    text = re.sub(r"\$(.*?\\.*?)\$", r"\1", text)
    text = re.sub(r"\$([ΣΨΔT_max\s]+)\$", r"\1", text)
    text = text.replace(r"$T -> 0$", "T -> 0")
    text = text.replace(r"$T < T_crit$", "T < T_crit")
    text = text.replace(r"T_crit$", "T_crit")
    return text


cleaned_md = clean_latex(md_content)

# Arreglar tablas rotas
lines = cleaned_md.split("\n")
for i in range(len(lines)):
    if ":---" in lines[i] and "|" in lines[i]:
        if i > 0 and "|" not in lines[i - 1]:
            lines[i - 1] = "| " + lines[i - 1].replace("    ", " | ") + " |"
        if i > 0 and not lines[i - 1].strip().startswith("|"):
            lines[i - 1] = "| " + lines[i - 1]
        if i > 0 and not lines[i - 1].strip().endswith("|"):
            lines[i - 1] = lines[i - 1] + " |"

        # Limpiar fila de header
        lines[i - 1] = re.sub(r"\|\s*\|", "|", lines[i - 1])

cleaned_md = "\n".join(lines)
cleaned_md = re.sub(r"([^\n])\n(\s*\|.*\|.*\|)", r"\1\n\n\2", cleaned_md)
html_content = markdown.markdown(cleaned_md, extensions=["toc", "tables"])

# Cover
cover_html = ""
if os.path.exists(cover_path):
    with open(cover_path, "rb") as img_f:
        encoded = base64.b64encode(img_f.read()).decode("utf-8")
    cover_html = f'<div style="text-align: center; margin-bottom: 2em;"><img src="data:image/png;base64,{encoded}" style="max-width: 100%; height: auto; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);" alt="Portada" /></div>\n'

full_html = (
    '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n</head>\n<body>\n'
    + cover_html
    + html_content
    + "\n</body>\n</html>"
)

with open(html_file, "w", encoding="utf-8") as f:
    f.write(full_html)

print("HTML Regenerado con soporte para tablas y Unicode.")
