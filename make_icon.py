"""
make_icon.py — Gravity AI Bridge V10.0
Genera gravity_icon.ico en assets/ desde cero usando solo Pillow.
Ejecutar si el .ico se pierde o para actualizarlo.

    python make_icon.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(BASE_DIR, "assets", "gravity_icon.ico")

SIZES = [256, 128, 64, 48, 32, 16]

_BG     = (9,   12,  16 )   # Deep Space
_RING1  = (124, 58,  237)   # Quantum Violet
_RING2  = (79,  70,  229)   # Indigo Accent
_TEXT   = (167, 139, 250)   # Lavender


def _make_frame(size: int) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size // 2
    r  = size // 2 - 1

    # Fondo oscuro circular
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*_BG, 255))

    # Anillo externo Quantum Violet
    rw = max(2, size // 10)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 outline=(*_RING1, 230), width=rw)

    # Anillo interno suave
    r2 = r - rw - max(1, size // 16)
    draw.ellipse([cx - r2, cy - r2, cx + r2, cy + r2],
                 outline=(*_RING2, 120), width=max(1, size // 20))

    # Letra "G" centrada
    fsize = max(8, size * 38 // 100)
    font  = None
    for font_path in [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]:
        try:
            font = ImageFont.truetype(font_path, fsize)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "G", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    offset_y = max(1, size // 20)
    draw.text((cx - tw // 2, cy - th // 2 - offset_y), "G",
              fill=(*_TEXT, 255), font=font)

    return img


def main():
    os.makedirs(os.path.join(BASE_DIR, "assets"), exist_ok=True)
    frames = [_make_frame(s) for s in SIZES]
    frames[0].save(
        OUT_PATH,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=frames[1:],
    )
    size_kb = os.path.getsize(OUT_PATH) // 1024
    print(f"[OK] {OUT_PATH}")
    print(f"     Tamaños: {SIZES}")
    print(f"     Archivo: {size_kb} KB")


if __name__ == "__main__":
    main()
