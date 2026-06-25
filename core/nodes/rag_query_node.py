"""
Gravity Workflow Node: RAGQuery
Consulta el índice RAG local con una pregunta y retorna contexto relevante.
"""

from core.workflow_engine import GravityNode, registry
from core.logger import log


@registry.register
class RAGQueryNode(GravityNode):
    NODE_TYPE = "RAGQuery"
    DESCRIPTION = "Consulta el índice RAG local y retorna contexto semántico relevante."
    INPUT_SCHEMA = {
        "query": "TEXT",
        "top_k": "INT",    # default 5
        "min_score": "FLOAT",  # default 0.5
    }
    OUTPUT_SCHEMA = {
        "context": "TEXT",
        "sources": "JSON_LIST",
        "found": "BOOL",
    }

    def execute(self, inputs: dict) -> dict:
        from rag.retriever import RAGRetriever

        query: str = inputs.get("query", "")
        top_k: int = int(inputs.get("top_k") or self.config.get("top_k") or 5)
        min_score: float = float(inputs.get("min_score") or self.config.get("min_score") or 0.5)

        log.info(f"[RAGQueryNode] Consultando RAG: '{query[:60]}' (top_k={top_k})")

        try:
            results = RAGRetriever.retrieve(query=query, top_k=top_k)
            if not results:
                return {"context": "", "sources": [], "found": False}

            filtered = [r for r in results if r.get("score", 0) >= min_score]
            context = "\n\n".join(
                f"[Fuente: {r.get('source', 'RAG')}]\n{r.get('text', '')}"
                for r in filtered
            )
            sources = [{"source": r.get("source"), "score": r.get("score")} for r in filtered]

            return {"context": context, "sources": sources, "found": bool(filtered)}

        except Exception as exc:
            log.warning(f"[RAGQueryNode] Error en RAG: {exc}")
            return {"context": "", "sources": [], "found": False}
