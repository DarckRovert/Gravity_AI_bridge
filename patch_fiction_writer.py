import os
import re

filepath = 'tools/fiction_writer.py'
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace self._safe_complete(messages... with safe_complete(provider_manager, messages...
    content = content.replace("self._safe_complete(messages)", "safe_complete(provider_manager, messages)")
    content = content.replace("self._safe_complete(messages, require_json=True)", "safe_complete(provider_manager, messages, require_json=True)")

    # Remove the _safe_complete definition
    # Find the start of _safe_complete
    lines = content.split('\n')
    start_idx = -1
    for i, line in enumerate(lines):
        if 'def _safe_complete(self, messages: list, max_retries=3, require_json=False) -> str:' in line:
            start_idx = i
            break
            
    if start_idx != -1:
        # Find the end (next definition or end of file)
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
    print("Patched fiction_writer.py")
