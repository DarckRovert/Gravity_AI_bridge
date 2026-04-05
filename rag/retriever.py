"""
Gravity AI — RAG Embedder + Retriever + PDF Parser V7.0

Embedder backends (in priority order):
  1. Ollama (nomic-embed-text) — 0 cost, offline, best quality for local
  2. sentence-transformers (all-MiniLM-L6-v2) — local, needs ~90MB download
  3. OpenAI text-embedding-3-small — cloud, $0.02/1M tokens if key available

Retriever combines vector search with BM25-like keyword matching for hybrid search.
PDF/DOCX parser extracts text for indexing.
"""

import os
import re
import json
import math
import hashlib
import urllib.request
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Embedder ──────────────────────────────────────────────────────────────────

class RAGEmbedder:
    _backend: str = None   # "ollama" | "sentence_transformers" | "openai" | "tfidf"
    _model:   str = ""
    _st_model = None

    @classmethod
    def _detect_backend(cls):
        if cls._backend:
            return cls._backend
        # Try Ollama nomic-embed-text
        try:
            data = json.loads(
                urllib.request.urlopen(
                    urllib.request.Request("http://localhost:11434/api/tags"), timeout=1
                ).read()
            )
            models = [m["name"] for m in data.get("models", [])]
            embed_model = next((m for m in models if "embed" in m or "nomic" in m), None)
            if embed_model:
                cls._backend = "ollama"
                cls._model   = embed_model
                return cls._backend
        except Exception:
            pass
        # Try sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            cls._st_model = SentenceTransformer("all-MiniLM-L6-v2")
            cls._backend  = "sentence_transformers"
            return cls._backend
        except Exception:
            pass
        # Try OpenAI embeddings
        try:
            from key_manager import KeyManager
            if KeyManager.has_key("openai"):
                cls._backend = "openai"
                cls._model   = "text-embedding-3-small"
                return cls._backend
        except Exception:
            pass
        # Ultimate fallback: TF-IDF pseudo-embedding (no external dependencies)
        cls._backend = "tfidf"
        return cls._backend

    @classmethod
    def embed(cls, texts: list[str]) -> list[list[float]]:
        """Returns a list of embedding vectors for the given texts."""
        backend = cls._detect_backend()
        if backend == "ollama":
            return cls._embed_ollama(texts)
        elif backend == "sentence_transformers":
            return cls._embed_sentence_transformers(texts)
        elif backend == "openai":
            return cls._embed_openai(texts)
        else:
            return cls._embed_tfidf(texts)

    @classmethod
    def _embed_ollama(cls, texts):
        results = []
        for text in texts:
            payload = json.dumps({"model": cls._model, "prompt": text}).encode()
            req     = urllib.request.Request(
                "http://localhost:11434/api/embeddings", data=payload,
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    d = json.loads(r.read())
                results.append(d.get("embedding", [0.0] * 768))
            except Exception:
                results.append([0.0] * 768)
        return results

    @classmethod
    def _embed_sentence_transformers(cls, texts):
        vecs = cls._st_model.encode(texts, show_progress_bar=False)
        return [v.tolist() for v in vecs]

    @classmethod
    def _embed_openai(cls, texts):
        from key_manager import KeyManager
        key = KeyManager.get_key("openai")
        payload = json.dumps({"input": texts, "model": cls._model}).encode()
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        req     = urllib.request.Request(
            "https://api.openai.com/v1/embeddings", data=payload, headers=headers
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
        return [item["embedding"] for item in d["data"]]

    @classmethod
    def _embed_tfidf(cls, texts):
        """
        Minimal TF-IDF-inspired 512-dim pseudo-embedding.
        Not semantic, but enables basic keyword-similarity search when no
        real embedding backend is available. Zero dependencies.
        """
        DIM = 512
        def _hash_vec(text):
            words = re.findall(r'\w+', text.lower())
            vec   = [0.0] * DIM
            for w in words:
                h = int(hashlib.md5(w.encode()).hexdigest(), 16) % DIM
                vec[h] += 1.0
            # L2 normalize
            norm = math.sqrt(sum(x*x for x in vec)) or 1.0
            return [x / norm for x in vec]
        return [_hash_vec(t) for t in texts]

    @classmethod
    def get_backend_name(cls) -> str:
        return cls._detect_backend()


# ── Retriever ─────────────────────────────────────────────────────────────────

class RAGRetriever:
    @staticmethod
    def retrieve(query: str, top_k: int = 5) -> list[dict]:
        """
        Hybrid retrieval: vector similarity + BM25-like keyword boost.
        Returns top-K chunks sorted by combined score.
        """
        from rag.vector_store import VectorStore
        query_emb = RAGEmbedder.embed([query])[0]
        results   = VectorStore.search(query_emb, top_k=top_k * 2)

        # BM25-like keyword boost
        query_words = set(re.findall(r'\w+', query.lower()))
        for r in results:
            doc_words   = Counter(re.findall(r'\w+', r["text"].lower()))
            keyword_score = sum(doc_words[w] for w in query_words if w in doc_words)
            r["combined"] = r["similarity"] * 0.7 + min(keyword_score / 20.0, 0.3)

        results.sort(key=lambda x: x["combined"], reverse=True)
        return results[:top_k]

    @staticmethod
    def retrieve_as_context(query: str, top_k: int = 5, max_chars: int = 15000) -> str:
        """Returns retrieved chunks formatted as a context string for injection."""
        results = RAGRetriever.retrieve(query, top_k=top_k)
        if not results:
            return ""
        parts = ["**Contexto recuperado del índice RAG:**\n"]
        total = 0
        for i, r in enumerate(results, 1):
            src   = r.get("source", "unknown")
            sim   = r.get("similarity", 0.0)
            text  = r["text"]
            block = f"\n--- Fragmento {i} (fuente: {os.path.basename(src)}, sim={sim:.2f}) ---\n{text}\n"
            if total + len(block) > max_chars:
                break
            parts.append(block)
            total += len(block)
        return "".join(parts)


# ── Indexer (high-level API) ──────────────────────────────────────────────────

class RAGIndexer:
    @staticmethod
    def index_text(text: str, source: str = "manual", metadata: dict = None) -> int:
        """Chunks and indexes a text string."""
        from rag.chunker      import chunk_text
        from rag.vector_store import VectorStore
        chunks = chunk_text(text)
        for c in chunks:
            c["source"]   = source
            c["metadata"] = metadata or {}
        if not chunks:
            return 0
        embeddings = RAGEmbedder.embed([c["text"] for c in chunks])
        return VectorStore.upsert(chunks, embeddings)

    @staticmethod
    def index_file(path: str) -> int:
        """Reads, chunks and indexes a single file."""
        from rag.chunker import chunk_file
        chunks = chunk_file(path)
        if not chunks:
            return 0
        embeddings = RAGEmbedder.embed([c["text"] for c in chunks])
        from rag.vector_store import VectorStore
        return VectorStore.upsert(chunks, embeddings)

    @staticmethod
    def index_folder(folder: str, extensions: set = None) -> tuple[int, int]:
        """Indexes all matching files in a folder. Returns (files, chunks) count."""
        if extensions is None:
            extensions = {".py",".js",".ts",".md",".txt",".rs",".go",".java",
                          ".c",".cpp",".h",".lua",".sh",".yaml",".toml",".json"}
        skip_dirs = {".git","node_modules",".venv","__pycache__","target",".next","dist"}
        file_count, chunk_count = 0, 0
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                if any(fname.endswith(e) for e in extensions):
                    path   = os.path.join(root, fname)
                    added  = RAGIndexer.index_file(path)
                    if added > 0:
                        file_count  += 1
                        chunk_count += added
        return file_count, chunk_count

    @staticmethod
    def index_pdf(path: str) -> int:
        """Extracts text from a PDF and indexes it."""
        try:
            import pypdf
            with open(path, "rb") as f:
                reader = pypdf.PdfReader(f)
            text = "\n\n".join(p.extract_text() or "" for p in reader.pages)
        except ImportError:
            try:
                from PyPDF2 import PdfReader
                with open(path, "rb") as f:
                    reader = PdfReader(f)
                text = "\n\n".join(
                    p.extract_text() or "" for p in reader.pages
                )
            except Exception as e:
                return 0
        except Exception:
            return 0
        return RAGIndexer.index_text(text, source=path, metadata={"type": "pdf"})
