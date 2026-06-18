import os
import markdown

def fix_grammar():
    md_path = r'f:\Gravity_AI_bridge\ensayos_generados\La_Física_del_Poder\La_Física_del_Poder.md'
    html_path = r'f:\Gravity_AI_bridge\ensayos_generados\La_Física_del_Poder\La_Física_del_Poder.html'

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Arreglar errores gramaticales obvios
    content = content.replace("La Tulpas", "Las Tulpas")
    content = content.replace("y incapaz", "e incapaz")
    content = content.replace("un acta radicalmente", "un acto radicalmente")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    html_content = '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n</head>\n<body>\n' + markdown.markdown(content, extensions=['toc']) + '\n</body>\n</html>'

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("Corrección gramatical y HTML generados con éxito.")

if __name__ == "__main__":
    fix_grammar()
