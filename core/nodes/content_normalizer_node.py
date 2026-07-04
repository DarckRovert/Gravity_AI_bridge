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
        raw_json_str = inputs.get("raw_json") or "{}"
        content_type = inputs.get("content_type") or "news"
        author = inputs.get("author") or "Nexo Ágora"
        image_prompt_prefix = inputs.get("image_prompt_prefix") or "cyberpunk news dark photorealistic"
        default_category = inputs.get("default_category") or "Tecnología Descentralizada"

        # Parse valid_categories from JSON string
        valid_categories: List[str] = []
        raw_cats = inputs.get("valid_categories") or ""
        if raw_cats:
            try:
                parsed_cats = json.loads(raw_cats)
                if isinstance(parsed_cats, list):
                    valid_categories = parsed_cats
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
            
            # Extract common string fields (English and Spanish)
            string_fields = [
                "category", "categoria", "categoría", 
                "title", "titulo", "título", "title_articulo",
                "excerpt", "extracto", "resumen", "description", "summary",
                "subtitle", "subtitulo", "subtítulo", "region", "región", "pais", "país"
            ]
            for field in string_fields:
                m = re.search(rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*?)(?:"|$)', text, re.IGNORECASE | re.DOTALL)
                if m:
                    repaired[field] = m.group(1).replace("\\n", "\n").replace('\\"', '"')
            
            # Extract full text fields
            ft_fields = ["fullText", "fulltext_articulo", "texto", "contenido", "full_text", "cuerpo"]
            for ft_field in ft_fields:
                ft_match = re.search(rf'"{ft_field}"\s*:\s*"((?:[^"\\]|\\.)*?)(?:"|$)', text, re.IGNORECASE | re.DOTALL)
                if ft_match:
                    ft = ft_match.group(1).rstrip("\\").replace("\\n", "\n").replace('\\"', '"')
                    if not ft.endswith("."):
                        ft += " [Transmisión cortada — fragmento recuperado.]"
                    repaired[ft_field] = ft
                    break
            
            # Extract featured
            feat_m = re.search(r'"(featured|destacado)"\s*:\s*(true|false)', text, re.IGNORECASE)
            repaired["featured"] = feat_m.group(2).lower() == "true" if feat_m else False

            if repaired:
                article_data = repaired
            else:
                log.warning(f"[{self.__class__.__name__}] Falló la reparación estructurada. Tratando como texto plano.")
                article_data = {
                    "fullText": text.strip()[:3000] + " [Texto recuperado en crudo]"
                }

        # ── Validar tipo de datos antes de iterar ───────────────────────
        if isinstance(article_data, list):
            if len(article_data) > 0 and isinstance(article_data[0], dict):
                article_data = article_data[0]
            else:
                article_data = {"fullText": str(article_data)}

        if not isinstance(article_data, dict):
            article_data = {"fullText": str(article_data)}

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
            elif k_lower in ("region", "región", "pais", "país"):
                normalized["region"] = v
            else:
                normalized[k] = v

        # ── Garantizar llaves mínimas ───────────────────────────────────
        if "title" not in normalized or not isinstance(normalized["title"], str):
            normalized["title"] = str(normalized.get("title", "Transmisión Clandestina de la Zona Ágora"))
        if "excerpt" not in normalized or not isinstance(normalized["excerpt"], str):
            normalized["excerpt"] = str(normalized.get("excerpt", "Reporte interceptado de los nodos de Gravity AI."))
        if "fullText" not in normalized or not isinstance(normalized["fullText"], str):
            normalized["fullText"] = str(normalized.get("fullText", "### Canal de contingencia activo\n\nNo se pudo decodificar."))

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

        # Estimar por longitud del texto (~200 palabras/min)
        word_count = len(normalized.get("fullText", "").split())
        computed_reading_time = max(3, word_count // 200)

        if "readingTime" in normalized:
            try:
                # El LLM a veces alucina "5 minutos", forzar a int
                normalized["readingTime"] = int(re.sub(r"\D", "", str(normalized["readingTime"])))
                if normalized["readingTime"] <= 0:
                    normalized["readingTime"] = computed_reading_time
            except Exception:
                normalized["readingTime"] = computed_reading_time
        else:
            normalized["readingTime"] = computed_reading_time

        # ── Imagen Pollinations.ai ──────────────────────────────────────
        # Resolución 16:9 para artfículos de portal (estándar web)
        img_width = 1200
        img_height = 675
        if content_type == "science":
            img_width, img_height = 1280, 720

        # Sanitizar título para Pollinations: remover caracteres especiales que rompen la URL o el prompt
        import re
        safe_title = re.sub(r'[^a-zA-Z0-9\sñÑáéíóúÁÉÍÓÚüÜ,.-]', '', normalized["title"][:120])
        title_encoded = urllib.parse.quote(safe_title.strip(), safe='')
        prefix_encoded = urllib.parse.quote(image_prompt_prefix, safe='')
        img_url = (
            f"https://image.pollinations.ai/prompt/{prefix_encoded}%20"
            f"{title_encoded}?width={img_width}&height={img_height}&nologo=true"
        )

        # Verificar que la imagen sea accesible antes de publicar
        image_ok = False
        try:
            req_check = urllib.request.Request(
                img_url,
                headers={"User-Agent": "Mozilla/5.0"},
                method="HEAD",
            )
            with urllib.request.urlopen(req_check, timeout=30) as r:
                image_ok = r.status == 200
        except Exception as _img_err:
            log.warning(f"[{self.__class__.__name__}] Pollinations no responde ({_img_err}). Usando placeholder SVG.")

        if image_ok:
            normalized["image"] = img_url
            # Pre-calentar en background (solo si sabemos que la URL es válida)
            def _warm_image(_url=img_url, _cls=self.__class__.__name__):
                try:
                    req = urllib.request.Request(_url, headers={"User-Agent": "Mozilla/5.0"})
                    urllib.request.urlopen(req, timeout=45)
                    log.info(f"[{_cls}] Imagen pre-calentada OK.")
                except Exception as e:
                    log.warning(f"[{_cls}] Fallo al pre-calentar imagen: {e}")
            threading.Thread(target=_warm_image, daemon=True).start()
        else:
            # Fallback: placeholder SVG inline (sin dependencias externas)
            safe_title = normalized["title"][:60].replace('"', "'").replace('<', '').replace('>', '')
            safe_type = content_type.upper()
            svg_data = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{img_width}" height="{img_height}">'
                f'<rect width="100%" height="100%" fill="#0d0d0d"/>'
                f'<rect x="40" y="40" width="{img_width-80}" height="{img_height-80}" '
                f'fill="none" stroke="#9b30ff" stroke-width="2"/>'
                f'<text x="50%" y="42%" font-family="monospace" font-size="18" fill="#9b30ff" '
                f'text-anchor="middle">[NEXO ÁGORA — {safe_type}]</text>'
                f'<text x="50%" y="55%" font-family="monospace" font-size="14" fill="#cccccc" '
                f'text-anchor="middle">{safe_title}</text>'
                f'</svg>'
            )
            import base64
            b64 = base64.b64encode(svg_data.encode("utf-8")).decode()
            normalized["image"] = f"data:image/svg+xml;base64,{b64}"
            log.info(f"[{self.__class__.__name__}] Usando placeholder SVG local.")


        return {
            "normalized_json": json.dumps(normalized, ensure_ascii=False)
        }
