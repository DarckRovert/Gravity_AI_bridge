import os
import re

files = [
    'tools/book_writer.py',
    'tools/fiction_writer.py',
    'tools/research_writer.py'
]

for filepath in files:
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add review_outline to write_book signature
    # Find def write_..._book(self, prompt, title, num_chapters, ...):
    content = re.sub(
        r'(def write_.*?_book\(.*?num_chapters=5)(,.*?\):|\):)',
        r'\1, review_outline=False\2',
        content,
        flags=re.DOTALL
    )

    # In write_book where outline is written
    target_str = 'atomic_write(os.path.join(book_dir, "2_escaleta.json"), outline_str)'
    if target_str in content:
        replacement = """atomic_write(os.path.join(book_dir, "2_escaleta.json"), outline_str)
            if review_outline:
                input(f"\\n[HITL] Escaleta guardada en {os.path.join(book_dir, '2_escaleta.json')}. Edite el archivo si lo desea y presione ENTER para continuar...")
                with open(os.path.join(book_dir, "2_escaleta.json"), 'r', encoding='utf-8') as f:
                    outline = json.load(f)"""
        content = content.replace(target_str, replacement)
        
    # Add to CLI input
    cli_target = 'caps = int(input("Número de capítulos deseados: "))'
    cli_target_alt = 'caps = int(input("Nmero de captulos deseados: "))' # Handle encoding quirks
    cli_repl = """caps = int(input("Número de capítulos deseados: "))
    hitl = input("¿Revisar escaleta manualmente antes de escribir? (s/n): ").strip().lower() == 's'"""
    
    if "caps = int(input(" in content:
        content = re.sub(r'caps = int\(input\(.*?\)\)', cli_repl, content)
        
        # update the call
        content = re.sub(
            r'\.write_.*?_book\(prompt=prompt, title=title, num_chapters=caps\)',
            lambda m: m.group(0)[:-1] + ', review_outline=hitl)',
            content
        )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched {filepath} with HITL")
