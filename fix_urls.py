import os, glob
import re

src_dir = r'f:\Gravity_AI_bridge\frontend\src'
files = glob.glob(os.path.join(src_dir, '**', '*.tsx'), recursive=True)
files += glob.glob(os.path.join(src_dir, '**', '*.ts'), recursive=True)

count = 0
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    new_content = content.replace("'http://localhost:7860/", "'/")
    new_content = new_content.replace("`http://localhost:7860/", "`/")
    new_content = new_content.replace('\"http://localhost:7860/', '\"/')
    new_content = new_content.replace("const API = 'http://localhost:7860';", "const API = '';")

    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        count += 1

print(f'Modified {count} files.')
