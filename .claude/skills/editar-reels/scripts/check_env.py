#!/usr/bin/env python3
"""Check which tools the editar-reels skill needs are installed.

Prints a human summary plus install hints for the current OS.
Use --json for machine-readable output.
Exit code 0 = the basics (ffmpeg, ffprobe, a transcriber) are ready, 2 = something essential is missing.
"""
import importlib.util
import json
import platform
import shutil
import subprocess
import sys


def has_module(name):
    return importlib.util.find_spec(name) is not None


def ffmpeg_filters():
    if not shutil.which("ffmpeg"):
        return set()
    try:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return set()
    names = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and len(parts[0]) == 3:
            names.add(parts[1])
    return names


def main():
    system = platform.system()
    filters = ffmpeg_filters()
    status = {
        "os": system,
        "python": sys.version.split()[0],
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "ffprobe": bool(shutil.which("ffprobe")),
        "ffmpeg_libass": "ass" in filters,
        "transcriber_faster_whisper": has_module("faster_whisper"),
        "transcriber_openai_whisper": has_module("whisper"),
        "node": bool(shutil.which("node")),
        "npx": bool(shutil.which("npx")),
        "rembg_optional": has_module("rembg"),
    }
    status["transcriber"] = status["transcriber_faster_whisper"] or status["transcriber_openai_whisper"]
    status["ready_basic"] = status["ffmpeg"] and status["ffprobe"] and status["transcriber"]

    hints = []
    if not status["ffmpeg"] or not status["ffprobe"]:
        hints.append({
            "Darwin": "brew install ffmpeg",
            "Windows": "winget install --id Gyan.FFmpeg -e",
        }.get(system, "sudo apt install ffmpeg   (o el paquete equivalente de tu distribución)"))
    elif not status["ffmpeg_libass"]:
        hints.append("Tu FFmpeg no tiene libass (subtítulos). Instala una versión completa: brew install ffmpeg / winget install Gyan.FFmpeg")
    if not status["transcriber"]:
        hints.append(f"{sys.executable} -m pip install faster-whisper   (transcripción local; la primera vez descarga el modelo, ~500 MB)")
    if not status["node"]:
        hints.append("Opcional, para gráficos animados con Remotion: instala Node.js LTS desde https://nodejs.org")

    if "--json" in sys.argv:
        print(json.dumps({**status, "install_hints": hints}, indent=2, ensure_ascii=False))
    else:
        def mark(ok):
            return "OK " if ok else "FALTA"
        print(f"Sistema: {system} · Python {status['python']}")
        print(f"[{mark(status['ffmpeg'] and status['ffprobe'])}] FFmpeg (cortar, unir, exportar)")
        print(f"[{mark(status['ffmpeg_libass'])}] Subtítulos en FFmpeg (libass)")
        print(f"[{mark(status['transcriber'])}] Transcriptor (faster-whisper u openai-whisper)")
        print(f"[{mark(status['node'])}] Node.js (opcional: gráficos animados con Remotion)")
        print(f"[{mark(status['rembg_optional'])}] rembg (opcional: texto detrás de la cabeza)")
        if hints:
            print("\nPara instalar lo que falta:")
            for h in hints:
                print("  " + h)
        print("\nListo para editar." if status["ready_basic"] else "\nFalta lo básico; instala lo de arriba y vuelve a correr este chequeo.")
    sys.exit(0 if status["ready_basic"] else 2)


if __name__ == "__main__":
    main()
