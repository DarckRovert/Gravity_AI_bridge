import os

filepath = 'tools/fiction_writer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_str = """            atomic_write(
                progress_file,
                json.dumps(
                    {"ultimo_capitulo_completado": chap_num, "total": num_chapters}
                ),
            )"""

replacement_str = """            word_count = len(chapter_text.split())
            
            progress_data = {"ultimo_capitulo_completado": chap_num, "total": num_chapters}
            
            # Cargar progreso previo para métricas
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
            logger.info(f"[Metrics] Capítulo {chap_num}: {word_count} palabras. Total libro: {progress_data['total_words']} palabras.")
"""

if target_str in content:
    content = content.replace(target_str, replacement_str)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched fiction_writer.py with metrics")
else:
    print("Metrics target string not found")
