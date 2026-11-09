#!/usr/bin/env python3
"""Create the Reels/ working folder used by the editar-reels skill.

Usage: python3 init_project.py ./Reels
Safe to run again: existing files are never overwritten.
"""
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent

FOLDERS = {
    "tomas": "Deja aquí tus videos grabados en bruto. Nunca se modifican: Claude trabaja con una copia.",
    "referencias": "Videos o capturas de estilos que te gustan (tuyos o de otros creadores). Claude los usa como guía.",
    "marca/logos": "Logos en PNG o SVG con fondo transparente.",
    "marca/fuentes": "Archivos de fuentes .ttf u .otf (por ejemplo, de Google Fonts).",
    "musica": "Música con licencia de uso (libre de derechos).",
    "sfx": "Efectos de sonido: whoosh, click, pop… con licencia de uso.",
    "broll": "Tomas de apoyo propias: casas, interiores, drone, pueblo, carretera, firmas, llaves.",
    "proyectos": "Un folder por reel con todas sus versiones (v1_corte, v2_subs, final…).",
}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    root = Path(sys.argv[1]).expanduser().resolve()
    created = []
    for rel, note in FOLDERS.items():
        d = root / rel
        if not d.exists():
            d.mkdir(parents=True)
            created.append(rel + "/")
        readme = d / "LEEME.txt"
        if not readme.exists():
            readme.write_text(note + "\n", encoding="utf-8")

    templates = {
        root / "marca" / "estilo.md": SKILL_DIR / "assets" / "estilo-plantilla.md",
        root / "marca" / "aprendizajes.md": SKILL_DIR / "assets" / "aprendizajes-plantilla.md",
    }
    for dest, src in templates.items():
        if not dest.exists() and src.exists():
            shutil.copyfile(src, dest)
            created.append(str(dest.relative_to(root)))

    print(f"Carpeta de trabajo: {root}")
    if created:
        print("Creado:")
        for c in created:
            print("  " + c)
    else:
        print("Todo ya existía; no se cambió nada.")


if __name__ == "__main__":
    main()
