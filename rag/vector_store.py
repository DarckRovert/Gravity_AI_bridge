"""
Gravity AI — RAG Vector Store V7.0
SQLite + VSS (vector similarity search) or pure Python cosine fallback.
No external service required.
"""

import os
import json
import struct
import math
import sqlite3
import threading
import time

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG_DIR       = os.path.join(BASE_DIR, "_rag_index")
RAG_DB        = os.path.join(RAG_DIR, "index.sqlite")
_lock         = threading.Lock()

os.makedirs(RAG_DIR, exist_ok=True)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(RAG_DB, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            source    TEXT,
            text      TEXT NOT NULL,
            embedding BLOB,
            metadata  TEXT,
            added_at  REAL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON documents(source)")
    conn.commit()
    return conn


def _vec_to_blob(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _blob_to_vec(blob: bytes) -> list[float]:
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


def _cosine(a: list[float], b: list[float]) -> float:
    dot  = sum(x * y for x, y in zip(a, b))
    na   = math.sqrt(sum(x * x for x in a))
    nb   = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class VectorStore:
    """
    SQLite-backed vector store with pure-Python cosine similarity search.
    Automatically integrates with RAGEmbedder for embedding generation.
    """

    @staticmethod
    def upsert(chunks: list[dict], embeddings: list[list[float]]) -> int:
        """Inserts or updates chunks with their embeddings. Returns inserted count."""
        with _lock:
            conn    = _get_conn()
            count   = 0
            now     = time.time()
            for chunk, emb in zip(chunks, embeddings):
                source = chunk.get("source", "")
                text   = chunk.get("text", "")
                meta   = json.dumps({k: v for k, v in chunk.items() if k not in ("text", "embedding")})
                blob   = _vec_to_blob(emb)
                conn.execute(
                    "INSERT INTO documents (source, text, embedding, metadata, added_at) VALUES (?,?,?,?,?)",
                    (source, text, blob, meta, now)
                )
                count += 1
            conn.commit()
        return count

    @staticmethod
    def delete_by_source(source: str) -> int:
        with _lock:
            conn = _get_conn()
            n    = conn.execute("SELECT COUNT(*) FROM documents WHERE source=?", (source,)).fetchone()[0]
            conn.execute("DELETE FROM documents WHERE source=?", (source,))
            conn.commit()
        return n

    @staticmethod
    def search(query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Returns top-K chunks ranked by cosine similarity."""
        with _lock:
            conn = _get_conn()
            rows = conn.execute("SELECT id, source, text, embedding, metadata FROM documents").fetchall()

        if not rows:
            return []

        scored = []
        for row in rows:
            doc_id, source, text, blob, meta = row
            if blob:
                doc_emb = _blob_to_vec(blob)
                sim     = _cosine(query_embedding, doc_emb)
                scored.append({
                    "id":         doc_id,
                    "source":     source,
                    "text":       text,
                    "similarity": sim,
                    "metadata":   json.loads(meta) if meta else {},
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def stats() -> dict:
        with _lock:
            conn    = _get_conn()
            total   = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            sources = conn.execute("SELECT COUNT(DISTINCT source) FROM documents").fetchone()[0]
            size_kb = os.path.getsize(RAG_DB) // 1024 if os.path.exists(RAG_DB) else 0
        return {"total_chunks": total, "sources": sources, "size_kb": size_kb}

    @staticmethod
    def clear() -> int:
        with _lock:
            conn = _get_conn()
            n    = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            conn.execute("DELETE FROM documents")
            conn.commit()
        return n
