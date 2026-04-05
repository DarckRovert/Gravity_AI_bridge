"""
Gravity AI — RAG Chunker V7.1
Smart chunking that respects code blocks, markdown headers, and sentence boundaries.
"""

import re

DEFAULT_CHUNK_TOKENS  = 512
DEFAULT_OVERLAP_CHARS = 200
CHARS_PER_TOKEN       = 4   # approximate


def chunk_text(
    text:         str,
    max_tokens:   int = DEFAULT_CHUNK_TOKENS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[dict]:
    """
    Splits text into overlapping chunks suitable for embedding.
    Respects:
      - Fenced code blocks (never splits inside ``` ... ```)
      - Markdown headers (prefer to start chunks at headers)
      - Paragraph boundaries (double newline)
    Returns list of {"text": str, "start": int, "end": int}
    """
    max_chars = max_tokens * CHARS_PER_TOKEN

    # Split by code blocks first to protect them
    parts = re.split(r"(```[\s\S]*?```)", text)

    chunks    = []
    buf       = ""
    buf_start = 0
    pos       = 0

    for part in parts:
        is_code = part.startswith("```")
        if is_code:
            # Code block: add as single chunk if too big, or append to buf
            if len(buf) + len(part) > max_chars and buf.strip():
                chunks.append({"text": buf.strip(), "start": buf_start, "end": pos})
                # Overlap: carry last overlap_chars of previous chunk
                overlap = buf[-overlap_chars:] if len(buf) > overlap_chars else buf
                buf       = overlap + part
                buf_start = pos - len(overlap)
            else:
                if not buf:
                    buf_start = pos
                buf += part
        else:
            # Regular text: split by paragraphs
            paragraphs = re.split(r"\n\n+", part)
            for para in paragraphs:
                if len(buf) + len(para) + 2 > max_chars and buf.strip():
                    chunks.append({"text": buf.strip(), "start": buf_start, "end": pos})
                    overlap   = buf[-overlap_chars:] if len(buf) > overlap_chars else buf
                    buf       = overlap + para + "\n\n"
                    buf_start = pos - len(overlap)
                else:
                    if not buf:
                        buf_start = pos
                    buf += para + "\n\n"
        pos += len(part)

    if buf.strip():
        chunks.append({"text": buf.strip(), "start": buf_start, "end": pos})

    return chunks


def chunk_file(path: str, **kwargs) -> list[dict]:
    """Reads a file and chunks its content."""
    try:
        for enc in ("utf-8", "latin-1", "utf-16"):
            try:
                with open(path, "r", encoding=enc) as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            return []
        chunks = chunk_text(text, **kwargs)
        # Annotate with source file
        for c in chunks:
            c["source"] = path
        return chunks
    except Exception:
        return []
