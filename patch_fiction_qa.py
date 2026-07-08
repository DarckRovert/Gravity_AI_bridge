import os

filepath = 'tools/fiction_writer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add the import
import_stmt = "from core.chapter_qa import qa_agent\n"
if "from core.chapter_qa import qa_agent" not in content:
    content = content.replace("from tools.llm_utils import clean_response", "from tools.llm_utils import clean_response\n" + import_stmt)

# 2. Add the QA check inside the main writing loop
# Find where the chapter is successfully written and before atomic_append
# Original:
#             logger.info(f"Fase 3: Escribiendo Capítulo {chap_num}: {chap_title}...")
#             chapter_text = self._write_chapter(
# ...
#             # BUG-06 Resuelto: Append O(1) en lugar de reconstrucción O(n^2)
#             atomic_append(book_file, chapter_text + "\n\n=== CAPITULO ===\n\n")

target_str = """            # BUG-06 Resuelto: Append O(1) en lugar de reconstrucción O(n^2)
            atomic_append(book_file, chapter_text + "\\n\\n=== CAPITULO ===\\n\\n")"""

replacement_str = """            # QA Check: Validar el capítulo antes de guardarlo
            qa_result = qa_agent.validate_chapter(chapter_text, base_context, self.lore_bible)
            if qa_result.get("status") == "FAIL":
                logger.warning(f"QA REJECTED Cap {chap_num}: {qa_result.get('feedback')}. Reescribiendo...")
                # Hacemos un reintento simple
                chapter_text = self._write_chapter(
                    c, base_context, full_outline_text, accumulated_history
                )
            else:
                logger.info(f"QA PASSED Cap {chap_num}.")

            # BUG-06 Resuelto: Append O(1) en lugar de reconstrucción O(n^2)
            atomic_append(book_file, chapter_text + "\\n\\n=== CAPITULO ===\\n\\n")"""

content = content.replace(target_str, replacement_str)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched fiction_writer.py with QA Agent")
