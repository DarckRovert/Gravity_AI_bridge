"""
ContentNormalizerNode — Normalización genérica de contenido JSON para portal.
Soporta: noticias, ensayos, artículos científicos, etc.
Configurable via inputs: content_type, valid_categories, image_prompt_prefix, author.
"""
import re
import json
import threading
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List

from core.workflow_engine import GravityNode, registry
from core.logger import log


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-")


@registry.register
class ContentNormalizerNode(GravityNode):
    NODE_TYPE = "ContentNormalizer"
    DESCRIPTION = (
        "Normaliza JSON crudo de LLM para publicación en el portal. "
        "Añade slug-ID, fecha, imagen Pollinations.ai, tipo de contenido y autor. "
        "Soporta noticias, ensayos y artículos científicos."
    )
    INPUT_SCHEMA = {
        "raw_json": "TEXT",
        "content_type": "TEXT",        # "news" | "essay" | "science"
        "author": "TEXT",              # Ej: "Nexo Ágora — Redacción Científica"
        "image_prompt_prefix": "TEXT", # Ej: "cyberpunk science dark lab"
        "valid_categories": "TEXT",    # JSON array string, ej: '["Física","Neuro"]'
        "default_category": "TEXT",    # Ej: "Ciencia"
    }
    OUTPUT_SCHEMA = {
        "normalized_json": "TEXT"
    }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        raw_json_str = inputs.get("raw_json", "")
        content_type = inputs.get("content_type", "news")
        author = inputs.get("author", "Nexo Ágora")
        image_prompt_prefix = inputs.get("image_prompt_prefix", "cyberpunk news dark photorealistic")
        default_category = inputs.get("default_category", "Tecnología Descentralizada")

        # Parse valid_categories from JSON string
        valid_categories: List[str] = []
        raw_cats = inputs.get("valid_categories", "")
        if raw_cats:
            try:
                valid_categories = json.loads(raw_cats)
            except Exception:
                valid_categories = []

        if not raw_json_str:
            raw_json_str = "{}"

        # ── Limpieza de <think> y prefijos conversacionales ──────────────
        text = raw_json_str
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        if "<think>" in text:
            text = re.sub(r"<think>.*", "", text, flags=re.DOTALL).strip()

        prefixes_to_strip = [
            "Aquí tienes", "Aquí está", "Claro, aquí",
            "Entendido.", "¡Por supuesto!", "Here is",
        ]
        for prefix in prefixes_to_strip:
            if text.lower().startswith(prefix.lower()):
                lines = text.split("\n")
                while lines and (
                    lines[0].lower().startswith(prefix.lower()) or lines[0].strip() == ""
                ):
                    lines.pop(0)
                text = "\n".join(lines).strip()

        # ── Extracción de JSON con 4 capas de fallback ──────────────────
        article_data = None

        # 1. Parser directo
        try:
            article_data = json.loads(text, strict=False)
        except Exception:
            pass

        # 2. Buscar bloque markdown ```json```
        if not article_data:
            json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if json_match:
                try:
                    article_data = json.loads(json_match.group(1), strict=False)
                except Exception:
                    pass

        # 3. Buscar desde primera llave
        if not article_data:
            brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
            if brace_match:
                try:
                    article_data = json.loads(brace_match.group(1), strict=False)
                except Exception:
                    pass

        # 4. Reparar JSON truncado
        if not article_data:
            log.warning(f"[{self.__class__.__name__}] Intentando reparar JSON truncado...")
            repaired = {}
            for field in ["category", "title", "excerpt", "subtitle"]:
                m = re.search(rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
                if m:
                    repaired[field] = m.group(1).replace("\\n", "\n").replace('\\"', '"')
            ft_match = re.search(r'"fullText"\s*:\s*"(.*?)(?:"|$)', text, re.DOTALL)
            if ft_match:
                ft = ft_match.group(1).rstrip("\\").replace("\\n", "\n").replace('\\"', '"')
                if not ft.endswith("."):
                    ft += " [Transmisión cortada — fragmento recuperado.]"
                repaired["fullText"] = ft
            feat_m = re.search(r'"featured"\s*:\s*(true|false)', text)
            repaired["featured"] = feat_m.group(1) == "true" if feat_m else False

            if "title" in repaired:
                article_data = repaired
            else:
                raise ValueError("No se pudo extraer JSON ni repararlo.")

        # ── Normalización de llaves ─────────────────────────────────────
        normalized = {}
        for k, v in article_data.items():
            k_lower = k.lower()
            if k_lower in ("title", "titulo", "título", "title_articulo"):
                normalized["title"] = v
            elif k_lower in ("subtitle", "subtitulo", "subtítulo"):
                normalized["subtitle"] = v
            elif k_lower in ("excerpt", "extracto", "resumen", "description", "summary"):
                normalized["excerpt"] = v
            elif k_lower in ("fulltext", "fulltext_articulo", "texto", "contenido", "full_text", "cuerpo"):
                normalized["fullText"] = v
            elif k_lower in ("category", "categoria", "categoría"):
                normalized["category"] = v
            elif k_lower in ("featured", "destacado"):
                if isinstance(v, str):
                    normalized["featured"] = v.lower() in ("true", "1", "si", "sí")
                else:
                    normalized["featured"] = bool(v)
            elif k_lower in ("readingtime", "reading_time", "tiempo_lectura"):
                normalized["readingTime"] = v
            else:
                normalized[k] = v

        # ── Garantizar llaves mínimas ───────────────────────────────────
        if "title" not in normalized:
            normalized["title"] = "Transmisión Clandestina de la Zona Ágora"
        if "excerpt" not in normalized:
            normalized["excerpt"] = "Reporte interceptado de los nodos de Gravity AI."
        if "fullText" not in normalized:
            normalized["fullText"] = "### Canal de contingencia activo\n\nNo se pudo decodificar."

        # Validar categoría
        if valid_categories and normalized.get("category") not in valid_categories:
            normalized["category"] = default_category
        elif "category" not in normalized:
            normalized["category"] = default_category

        if "featured" not in normalized:
            normalized["featured"] = False

        # ── Campos computados ───────────────────────────────────────────
        normalized["id"] = slugify(normalized["title"])
        normalized["type"] = content_type
        normalized["author"] = author
        normalized["date"] = datetime.now().isoformat()
        normalized["tags"] = normalized.get("tags", [])

        if "readingTime" not in normalized:
            # Estimar por longitud del texto (~200 palabras/min)
            word_count = len(normalized.get("fullText", "").split())
            normalized["readingTime"] = max(3, word_count // 200)

        # ── Imagen Pollinations.ai ──────────────────────────────────────
        title_encoded = urllib.parse.quote(normalized["title"][:120])
        prefix_encoded = urllib.parse.quote(image_prompt_prefix)
        img_url = (
            f"https://image.pollinations.ai/prompt/{prefix_encoded}%20"
            f"{title_encoded}?width=800&height=600"
        )
        normalized["image"] = img_url

        def _warm_image(_url=img_url, _cls=self.__class__.__name__):
            try:
                req = urllib.request.Request(_url, headers={"User-Agent": "Mozilla/5.0"})
                urllib.request.urlopen(req, timeout=45)
                log.info(f"[{_cls}] Imagen pre-calentada OK.")
            except Exception as e:
                log.warning(f"[{_cls}] Fallo al pre-calentar imagen: {e}")

        threading.Thread(target=_warm_image, daemon=True).start()
        log.info(f"[{self.__class__.__name__}] Pre-calentamiento de imagen disparado en background.")

        return {
            "normalized_json": json.dumps(normalized, ensure_ascii=False)
        }
