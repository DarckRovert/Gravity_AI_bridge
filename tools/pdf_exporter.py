"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — PDF Exporter (KDP Ready)                                      ║
║                                                                              ║
║   Convierte un archivo Markdown o HTML de Gravity en un PDF formateado       ║
║   profesionalmente para publicación en Amazon KDP o impresión.               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import argparse
from core.logger import log

try:
    import markdown
    import weasyprint
except ImportError:
    weasyprint = None
    markdown = None

def export_to_pdf(input_md: str, output_pdf: str, title: str = "Libro"):
    if not weasyprint or not markdown:
        log.error("Dependencias faltantes. Instala: pip install Markdown weasyprint")
        return False
        
    if not os.path.exists(input_md):
        log.error(f"Archivo no encontrado: {input_md}")
        return False

    with open(input_md, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Convertir MD a HTML
    html_body = markdown.markdown(md_text, extensions=['extra', 'toc'])

    # CSS Profesional para impresión KDP (6x9 pulgadas típico)
    css_content = """
    @page {
        size: 6in 9in;
        margin: 0.75in;
        @bottom-center {
            content: counter(page);
            font-family: "Garamond", serif;
            font-size: 10pt;
        }
    }
    body {
        font-family: "Garamond", "Times New Roman", serif;
        font-size: 11pt;
        line-height: 1.4;
        text-align: justify;
    }
    h1 {
        page-break-before: always;
        text-align: center;
        margin-top: 2in;
        margin-bottom: 1in;
        font-size: 24pt;
        text-transform: uppercase;
    }
    h2 {
        font-size: 16pt;
        margin-top: 2em;
        margin-bottom: 1em;
    }
    p {
        text-indent: 0.25in;
        margin: 0;
    }
    p:first-of-type {
        text-indent: 0;
    }
    """

    full_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>{css_content}</style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """

    log.info(f"Generando PDF en {output_pdf}...")
    try:
        weasyprint.HTML(string=full_html).write_pdf(output_pdf)
        log.info("PDF generado exitosamente.")
        return True
    except Exception as e:
        log.error(f"Error generando PDF: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gravity AI PDF Exporter")
    parser.add_argument("input", help="Ruta al archivo Markdown de entrada")
    parser.add_argument("--output", "-o", help="Ruta del PDF de salida", default="output.pdf")
    args = parser.parse_args()
    
    export_to_pdf(args.input, args.output)
