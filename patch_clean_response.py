import os
import re

files_to_patch = [
    'tools/book_writer.py', 
    'tools/fiction_writer.py', 
    'tools/research_writer.py', 
    'tools/book_refiner.py',
    'tools/research_refiner.py'
]

for filepath in files_to_patch:
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace self._clean_response with clean_response
    content = content.replace("self._clean_response(", "clean_response(")

    # Find the def _clean_response block
    lines = content.split('\n')
    start_idx = -1
    for i, line in enumerate(lines):
        if 'def _clean_response(self, text: str) -> str:' in line:
            start_idx = i
            break
            
    if start_idx != -1:
        # Find the end (next def or EOF)
        end_idx = -1
        for i in range(start_idx + 1, len(lines)):
            if lines[i].startswith('    def '):
                end_idx = i
                break
                
        if end_idx != -1:
            lines = lines[:start_idx] + lines[end_idx:]
        else:
            lines = lines[:start_idx]
            
    content = '\n'.join(lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched {filepath}")
