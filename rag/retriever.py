"""
Gravity AI — RAG Embedder + Retriever + PDF Parser V7.1

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

# NPU/ONNX dependencies (lazy loaded inside methods)
onnxruntime = None
tokenizers = None
numpy = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Embedder ──────────────────────────────────────────────────────────────────

class RAGEmbedder:
    _backend: str = None   # "ollama" | "sentence_transformers" | "openai" | "tfidf"
    _model:   str = ""
    _st_model = None

    @classmethod
    def _detect_backend(cls):
        # Try NPU (ONNX + DirectML)
        npu_dir = os.path.join(BASE_DIR, "rag", "models", "npu_minilm")
        if os.path.exists(os.path.join(npu_dir, "model.onnx")):
            cls._backend = "onnx_npu"
            cls._model   = "all-MiniLM-L6-v2"
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
        if backend == "onnx_npu":
            return cls._embed_onnx_npu(texts)
        elif backend == "ollama":
            return cls._embed_ollama(texts)
        elif backend == "sentence_transformers":
            return cls._embed_sentence_transformers(texts)
        elif backend == "openai":
            return cls._embed_openai(texts)
        else:
            return cls._embed_tfidf(texts)

    _onnx_session = None
    _tokenizer    = None

    @classmethod
    def _embed_onnx_npu(cls, texts):
        global onnxruntime, tokenizers, numpy
        import sys
        
        # PHASE 3: Gravity Hybrid Delegation (Conda Support)
        # If current python is 3.14+, we delegate to a 3.11 environment to use NPU
        if sys.version_info.major == 3 and sys.version_info.minor >= 14:
            return cls._embed_hybrid_conda(texts)

        if not cls._onnx_session:
            import onnxruntime
            from tokenizers import Tokenizer
            import numpy
            
            # ENFORCE ABSOLUTE CANONICAL PATHS FOR NPU DRIVER (Awakening V2)
            install_dir = r"C:\Program Files\RyzenAI\1.7.1"
            npu_dir     = os.path.join(BASE_DIR, "rag", "models", "npu_minilm")
            npu_bin     = os.path.join(install_dir, "onnxruntime", "bin")
            voe_dir     = os.path.join(install_dir, "voe-4.0-win_amd64")
            xclbin_path = os.path.join(voe_dir, "xclbins", "phoenix", "4x4.xclbin")
            config_file = os.path.join(voe_dir, "vaip_config.json")
            cache_dir   = os.path.join(BASE_DIR, "rag", "cache")
            
            # 1. Force Silence (Bypass UnicodeDecodeError)
            os.environ['ORT_LOGGING_LEVEL'] = '3'
            
            # 2. Critical NPU Plugin Handshake
            os.environ['ORT_VITISAI_EP_PATH'] = voe_dir
            if os.path.exists(npu_bin) and hasattr(os, "add_dll_directory"):
                os.add_dll_directory(npu_bin)
                os.add_dll_directory(voe_dir)
                os.environ["PATH"] = f"{npu_bin};{voe_dir};" + os.environ["PATH"]
            
            # 3. Awakening V2: Provider Options Structure
            provider_options = [{
                'config_file': config_file,
                'cacheDir': cache_dir,
                'cacheKey': 'gravity_v71_npu',
                'target': 'X1',
                'xclbin': xclbin_path
            }, {}, {}]
            
            try:
                model_path = os.path.join(npu_dir, "model_int8.onnx")
                cls._onnx_session = onnxruntime.InferenceSession(
                    model_path, 
                    providers=['VitisAIExecutionProvider', 'DmlExecutionProvider', 'CPUExecutionProvider'],
                    provider_options=provider_options
                )
            except Exception:
                # Fallback to GPU (DML)
                cls._onnx_session = onnxruntime.InferenceSession(
                    os.path.join(npu_dir, "model_int8.onnx"), 
                    providers=['DmlExecutionProvider', 'CPUExecutionProvider']
                )
            
            cls._tokenizer = Tokenizer.from_file(os.path.join(npu_dir, "tokenizer.json"))

        results = []
        for text in texts:
            encoded = cls._tokenizer.encode(text)
            input_ids = numpy.array([encoded.ids], dtype=numpy.int64)
            attn_mask = numpy.array([encoded.attention_mask], dtype=numpy.int64)
            type_ids  = numpy.array([encoded.type_ids], dtype=numpy.int64)
            
            inputs = {
                "input_ids": input_ids,
                "attention_mask": attn_mask,
                "token_type_ids": type_ids
            }
            outputs = cls._onnx_session.run(None, inputs)
            # Perform mean pooling on the output
            embeddings = outputs[0][0]
            sentence_embedding = numpy.mean(embeddings, axis=0)
            # L2 normalize
            norm = numpy.linalg.norm(sentence_embedding)
            sentence_embedding = (sentence_embedding / norm).tolist()
            results.append(sentence_embedding)
        return results

    @classmethod
    def _embed_hybrid_conda(cls, texts):
        """
        Delegates embedding generation to a Python 3.11 Conda environment.
        This bypasses binary compatibility issues in newer Python versions.
        """
        import subprocess
        import tempfile
        env_name = "gravity-npu"
        
        # 1. Create temporary exchange files
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f_in:
            json.dump(texts, f_in)
            in_path = f_in.name
            
        out_path = in_path + ".out.json"
        
        # 2. Worker script (one-liner version)
        worker_code = (
            f"import json, os, sys; "
            f"sys.path.append(r'{BASE_DIR}'); "
            f"from rag.retriever import RAGEmbedder; "
            f"with open(r'{in_path}', 'r') as fi: texts = json.load(fi); "
            f"vecs = RAGEmbedder._embed_onnx_npu(texts); "
            f"with open(r'{out_path}', 'w') as fo: json.dump(vecs, fo)"
        )
        
        # 3. Execution
        cmd = f"conda run -n {env_name} python -c \"{worker_code}\""
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
            with open(out_path, "r") as f_out:
                results = json.load(f_out)
        except Exception as e:
            # If hybrid fails, fallback to TF-IDF or CPU in current process
            print(f"[HYBRID ERROR] Fallback to CPU: {e}")
            return cls._embed_tfidf(texts)
        finally:
            # Cleanup
            for p in [in_path, out_path]:
                if os.path.exists(p): os.remove(p)
                
        return results

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
