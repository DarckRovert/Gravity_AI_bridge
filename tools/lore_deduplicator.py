"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — Lore Deduplicator CLI                                        ║
║                                                                              ║
║   Limpia archivos de lore Markdown eliminando entidades duplicadas.         ║
║                                                                              ║
║   Uso:                                                                       ║
║     python tools/lore_deduplicator.py                 (lore_bible.md)      ║
║     python tools/lore_deduplicator.py ruta/al/lore.md                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.visual_lore import deduplicate_lore_file  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="Gravity Lore Deduplicator — elimina entidades duplicadas de archivos de lore Markdown."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=os.path.join(BASE_DIR, "lore_bible.md"),
        help="Ruta al archivo de lore .md (default: lore_bible.md en la raíz del proyecto)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra cuántos duplicados se eliminarían sin modificar el archivo.",
    )
    args = parser.parse_args()

    lore_path = os.path.abspath(args.path)

    if not os.path.exists(lore_path):
        print(f"[ERROR] Archivo no encontrado: {lore_path}")
        sys.exit(1)

    print(f"Procesando: {lore_path}")

    if args.dry_run:
        # Contar duplicados sin escribir
        import re

        with open(lore_path, "r", encoding="utf-8") as f:
            content = f.read()

        discovery_header = "## Nuevas Entidades Descubiertas"
        parts = content.split(discovery_header)
        if len(parts) <= 1:
            print("No se encontraron secciones de entidades. Nada que limpiar.")
            return

        all_entities_text = "\n".join(parts[1:])
        h3_pattern = re.compile(r"(### [^\n]+(?:\n(?!###)[^\n]*)*)")
        all_entries = h3_pattern.findall(all_entities_text)

        seen_names: set = set()
        duplicates = 0
        for entry in all_entries:
            name_match = re.match(r"### ([^:\n]+)", entry)
            if not name_match:
                continue
            name = name_match.group(1).strip().lower()
            if name in seen_names:
                duplicates += 1
                print(f"  [DRY-RUN] Duplicado encontrado: '{name_match.group(1).strip()}'")
            else:
                seen_names.add(name)

        print(f"\n[DRY-RUN] Se eliminarían {duplicates} entidades duplicadas.")
    else:
        removed = deduplicate_lore_file(lore_path)
        if removed > 0:
            print(f"\n✓ Lore limpiado. {removed} entidades duplicadas eliminadas.")
        else:
            print("\n✓ Lore ya estaba limpio. Sin cambios.")


if __name__ == "__main__":
    main()
