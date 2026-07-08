import os

files = ['tools/book_writer.py', 'tools/research_writer.py']

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 1. Add QA import
    if "from core.chapter_qa import qa_agent" not in content:
        content = content.replace("from tools.llm_utils import", "from core.chapter_qa import qa_agent\nfrom tools.llm_utils import")

    # 2. Add QA + Metrics inside the loop
    # In both book_writer and research_writer:
    # 
    #             # BUG-06 Resuelto: Append O(1) en lugar de reconstrucción dinámica O(n^2)
    #             atomic_append(book_file, chapter_text + "\n\n=== CAPITULO ===\n\n")
    # OR in book_writer:
    #             atomic_append(book_file, chapter_text + "\n\n=== CAPITULO ===\n\n")
    #
    # Then it does progress_file json.dumps
    
    target_str_1 = 'atomic_append(book_file, chapter_text + "\\n\\n=== CAPITULO ===\\n\\n")'
    replacement_str_1 = """# QA Check: Validar el capítulo antes de guardarlo
            qa_result = qa_agent.validate_chapter(chapter_text, base_context, "")
            if qa_result.get("status") == "FAIL":
                logger.warning(f"QA REJECTED Cap {chap_num}: {qa_result.get('feedback')}. Reescribiendo...")
                chapter_text = self._write_chapter(
                    chap, base_context, full_outline_text, accumulated_history
                )
            else:
                logger.info(f"QA PASSED Cap {chap_num}.")

            # Guardado
            atomic_append(book_file, chapter_text + "\\n\\n=== CAPITULO ===\\n\\n")"""
            
    if target_str_1 in content and "qa_agent.validate_chapter" not in content:
        content = content.replace(target_str_1, replacement_str_1)

    target_str_2 = """            atomic_write(
                progress_file,
                json.dumps(
                    {"ultimo_capitulo_completado": chap_num, "total": num_chapters}
                ),
            )"""
    target_str_2_alt = """            atomic_write(
                progress_file,
                json.dumps({"ultimo_capitulo": chap_num, "total": num_chapters}),
            )"""

    metrics_logic = """            word_count = len(chapter_text.split())
            progress_data = {"ultimo_capitulo_completado": chap_num, "total": num_chapters}
            
            if os.path.exists(progress_file):
                try:
                    with open(progress_file, "r") as pf:
                        old_progress = json.load(pf)
                        progress_data["total_words"] = old_progress.get("total_words", 0) + word_count
                except:
                    progress_data["total_words"] = word_count
            else:
                progress_data["total_words"] = word_count

            atomic_write(
                progress_file,
                json.dumps(progress_data, indent=2),
            )
            logger.info(f"[Metrics] Capítulo {chap_num}: {word_count} palabras. Total libro: {progress_data['total_words']} palabras.")"""

    if target_str_2 in content:
        content = content.replace(target_str_2, metrics_logic)
    elif target_str_2_alt in content:
        content = content.replace(target_str_2_alt, metrics_logic)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched QA and Metrics in {filepath}")
