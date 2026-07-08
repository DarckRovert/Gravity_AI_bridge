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

    # In fiction_writer and research_writer, the writing logic is in write_fiction_book / write_research_book directly.
    # In book_writer, it delegates to _orchestrate_writing.

    # 1. Fix the signatures to accept review_outline: bool = False
    content = re.sub(
        r'(def write_.*?_book\(.*?num_chapters:\s*int\s*=\s*\d+)(,.*?\):|\):)',
        r'\1, review_outline: bool = False\2',
        content,
        flags=re.DOTALL
    )

    # For book_writer, we also need to pass it to _orchestrate_writing
    if "def _orchestrate_writing" in content:
        content = re.sub(
            r'(def _orchestrate_writing\(.*?resume=True)(,.*?\):|\):)',
            r'\1, review_outline=False\2',
            content,
            flags=re.DOTALL
        )
        content = re.sub(
            r'return self\._orchestrate_writing\(\n?\s*title=title,\n?\s*num_chapters=num_chapters,',
            r'return self._orchestrate_writing(\n            title=title,\n            num_chapters=num_chapters,\n            review_outline=review_outline,',
            content
        )
        # Also fix rewrite_and_expand_document
        content = re.sub(
            r'(def rewrite_and_expand_document\(.*?num_chapters:\s*int\s*=\s*\d+)(,.*?\):|\):)',
            r'\1, review_outline: bool = False\2',
            content,
            flags=re.DOTALL
        )
        # Fix the call to _orchestrate_writing from rewrite_and_expand_document
        content = re.sub(
            r'return self\._orchestrate_writing\(\n\s*title=title,\n\s*num_chapters=num_chapters,\n\s*phase1_callable',
            r'return self._orchestrate_writing(\n            title=title,\n            num_chapters=num_chapters,\n            review_outline=review_outline,\n            phase1_callable',
            content
        )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed signatures in {filepath}")
