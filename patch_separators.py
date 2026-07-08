import os

files_to_patch = ['tools/book_writer.py', 'tools/fiction_writer.py', 'tools/research_writer.py', 'tools/book_refiner.py']

for f in files_to_patch:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        content = content.replace('\n---\n\n', '\n=== CAPITULO ===\n\n')
        content = content.replace('\n\n---\n\n', '\n\n=== CAPITULO ===\n\n')
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Patched {f}')

epub_file = 'tools/epub_generator.py'
if os.path.exists(epub_file):
    with open(epub_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    content = content.replace(r're.split(r"(?m)^\s*---\s*$", content)', r're.split(r"(?m)^\s*===\s*CAPITULO\s*===\s*$", content)')
    
    with open(epub_file, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f'Patched {epub_file}')
