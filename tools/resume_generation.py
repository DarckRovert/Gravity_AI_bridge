import os
import sys
import json

sys.path.append(r"f:\Gravity_AI_bridge\tools")
from book_writer import GravityAuthor


def resume_book(title):
    author = GravityAuthor()
    book_dir = os.path.join(author.output_dir, title.replace(" ", "_"))
    progress_file = os.path.join(book_dir, "progreso_metadata.json")

    with open(os.path.join(book_dir, "1_contexto_base.md"), "r", encoding="utf-8") as f:
        base_context = f.read()

    with open(os.path.join(book_dir, "2_escaleta.json"), "r", encoding="utf-8") as f:
        outline = json.load(f)

    with open(progress_file, "r", encoding="utf-8") as f:
        prog = json.load(f)
        last_chap = prog.get("ultimo_capitulo_completado", 0)
        num_chapters = prog.get("total", 5)

    book_file = os.path.join(book_dir, f"{title.replace(' ', '_')}.md")

    # Read previous chapter to get summary
    previous_summary = ""
    if last_chap > 0:
        with open(
            os.path.join(book_dir, f"cap_{last_chap}.md"), "r", encoding="utf-8"
        ) as f:
            prev_text = f.read()
            previous_summary = author._summarize_chapter(prev_text)

    full_outline_text = "\n".join(
        [f"Cap {c.get('numero')}: {c.get('resumen_eventos')}" for c in outline]
    )
    source_text = author._extract_text_from_google_docs(
        "https://docs.google.com/document/d/17kUPrfLZAJc8F5Nj54co4BUO_GZMspo3CNZXnRBFop0/export?format=txt"
    )

    for chap in outline:
        chap_num = chap.get("numero")
        if chap_num <= last_chap:
            continue

        print(f"Resumiendo generación desde Capítulo {chap_num}...")
        chapter_text = author._write_chapter(
            chap, base_context, full_outline_text, previous_summary, source_text
        )

        with open(
            os.path.join(book_dir, f"cap_{chap_num}.md"), "w", encoding="utf-8"
        ) as f:
            f.write(chapter_text)

        with open(book_file, "a", encoding="utf-8") as f:
            f.write(chapter_text + "\n\n---\n\n")

        if chap_num < num_chapters:
            previous_summary = author._summarize_chapter(chapter_text)

        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(
                {"ultimo_capitulo_completado": chap_num, "total": num_chapters}, f
            )

        print(f"Capítulo {chap_num} guardado.")

    print(f"Libro reanudado y finalizado con éxito en {book_file}")


if __name__ == "__main__":
    resume_book("La Voluntad Soberana")
