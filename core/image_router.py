"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — Image Router V1.0                                            ║
║   Orquestador de fallback para generación de imágenes.                      ║
║   Prioridad: Pollinations Flux → Pollinations Turbo → SVG Placeholder.      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import os
import logging
from typing import Optional

logger = logging.getLogger("ImageRouter")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate(
    prompt: str,
    output_path: str,
    width: int = 1024,
    height: int = 1024,
    title: str = "",
    **kwargs,
) -> dict:
    """
    Intenta generar una imagen en orden de fallback:
    1. Pollinations Flux (alta calidad)
    2. Pollinations Turbo (más rápido)
    3. SVG placeholder de alta calidad con el título incrustado

    Returns:
        dict: {"success": bool, "path": str, "provider": str, "error": str}
    """
    from tools import pollinations_generator

    # ── Intento 1: Pollinations Flux ─────────────────────────────────────────
    try:
        result = pollinations_generator.generate(
            prompt=prompt,
            output_path=output_path,
            width=width,
            height=height,
            model="flux",
            enhance=True,
            negative_prompt="text, typography, letters, words, watermark, signature, comic, cartoon",
        )
        if result.get("success"):
            logger.info("ImageRouter: imagen generada con Pollinations Flux.")
            return {"success": True, "path": output_path, "provider": "pollinations/flux", "error": ""}
        error_code = result.get("status_code", 0)
        logger.warning(f"ImageRouter: Pollinations Flux falló (HTTP {error_code}). Intentando Turbo...")
    except Exception as e:
        logger.warning(f"ImageRouter: Pollinations Flux excepción: {e}. Intentando Turbo...")

    # ── Intento 2: Pollinations Turbo ────────────────────────────────────────
    try:
        result2 = pollinations_generator.generate(
            prompt=prompt,
            output_path=output_path,
            width=width,
            height=height,
            model="turbo",
            enhance=False,
        )
        if result2.get("success"):
            logger.info("ImageRouter: imagen generada con Pollinations Turbo.")
            return {"success": True, "path": output_path, "provider": "pollinations/turbo", "error": ""}
        logger.warning(f"ImageRouter: Pollinations Turbo también falló. Generando SVG placeholder...")
    except Exception as e:
        logger.warning(f"ImageRouter: Pollinations Turbo excepción: {e}. Generando SVG placeholder...")

    # ── Intento 3: SVG Placeholder ───────────────────────────────────────────
    svg_path = output_path.rsplit(".", 1)[0] + ".svg"
    label = title or prompt[:60]
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0a1a"/>
      <stop offset="50%" stop-color="#0d1a2e"/>
      <stop offset="100%" stop-color="#1a0a2e"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  <!-- Decorative circles -->
  <circle cx="{width//2}" cy="{height//3}" r="120" fill="none" stroke="#c9a96e" stroke-width="0.5" opacity="0.3"/>
  <circle cx="{width//2}" cy="{height//3}" r="80" fill="none" stroke="#c9a96e" stroke-width="0.3" opacity="0.2"/>
  <!-- Title -->
  <text x="{width//2}" y="{height//2}" font-family="Georgia, serif" font-size="36"
        fill="#c9a96e" text-anchor="middle" dominant-baseline="middle" filter="url(#glow)">{label}</text>
  <!-- Divider -->
  <line x1="{int(width*0.15)}" y1="{int(height*0.55)}" x2="{int(width*0.85)}" y2="{int(height*0.55)}"
        stroke="#c9a96e" stroke-width="0.8" opacity="0.5"/>
  <!-- Subtitle -->
  <text x="{width//2}" y="{int(height*0.60)}" font-family="Georgia, serif" font-size="16"
        fill="#6688aa" text-anchor="middle">Gravity Research Author</text>
</svg>'''

    try:
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        logger.info(f"ImageRouter: SVG placeholder generado en {svg_path}")
        return {"success": True, "path": svg_path, "provider": "svg_placeholder", "error": ""}
    except Exception as e:
        logger.error(f"ImageRouter: todos los métodos fallaron. Último error: {e}")
        return {"success": False, "path": "", "provider": "", "error": str(e)}
