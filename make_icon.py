"""
make_icon.py — Gravity AI Bridge V16.0 PRO
Genera assets/gravity_icon.ico desde cero usando Pillow.
Se invoca automáticamente por build_installer.bat si el .ico no existe.
"""

import os
import sys


def make_ico():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[ERROR] Pillow no instalado. Ejecuta: pip install Pillow")
        sys.exit(1)

    sizes = [256, 128, 64, 48, 32, 16]
    frames = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Fondo circular degradado simulado con elipses
        margin = int(size * 0.05)
        draw.ellipse(
            [margin, margin, size - margin, size - margin], fill=(7, 9, 14, 255)
        )

        # Anillo exterior
        ring = int(size * 0.08)
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            outline=(99, 102, 241, 255),
            width=max(1, ring),
        )

        # Letra "G" centrada
        font_size = max(8, int(size * 0.55))
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        text = "G"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (size - tw) // 2
        ty = (size - th) // 2 - int(size * 0.03)
        draw.text((tx, ty), text, font=font, fill=(198, 156, 109, 255))

        frames.append(img)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    ico_path = os.path.join(assets_dir, "gravity_icon.ico")

    frames[0].save(
        ico_path, format="ICO", sizes=[(s, s) for s in sizes], append_images=frames[1:]
    )
    print(f"[OK] Icono generado: {ico_path}")


if __name__ == "__main__":
    make_ico()
