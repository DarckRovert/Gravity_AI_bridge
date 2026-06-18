import os
import base64

book_dir = r"f:\Gravity_AI_bridge\ensayos_generados\Convergencia_Entropica"
html_file = os.path.join(book_dir, "Convergencia_Entropica.html")
cover_path = os.path.join(book_dir, "cover.png")

if os.path.exists(cover_path) and os.path.exists(html_file):
    with open(cover_path, "rb") as img_f:
        encoded = base64.b64encode(img_f.read()).decode('utf-8')
    cover_html = f'<div style="text-align: center; margin-bottom: 2em;"><img src="data:image/png;base64,{encoded}" style="max-width: 100%; height: auto; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);" alt="Portada" /></div>\n'
    
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "data:image/png;base64" not in content:
        # Insert after <body> tag
        content = content.replace("<body>\n", "<body>\n" + cover_html)
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("Portada incrustada con éxito.")
    else:
        print("La portada ya estaba incrustada.")
else:
    print("No se encontraron los archivos.")
