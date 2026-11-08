#!/usr/bin/env python3
"""Report which parts of the video toolkit are ready on this machine."""
from __future__ import annotations

import importlib.util
import os
import shutil
import socket
import subprocess


def ok(flag: bool) -> str:
    return "OK     " if flag else "MISSING"


def main() -> int:
    print("Video toolkit status\n--------------------")

    ff = shutil.which("ffmpeg")
    print(f"[{ok(bool(ff))}] ffmpeg            {ff or 'install: see docs/VIDEO_SETUP.md'}")

    fw = importlib.util.find_spec("faster_whisper") is not None
    print(f"[{ok(fw)}] faster-whisper    {'' if fw else 'pip install -r video-tools/requirements.txt'}")

    cb = importlib.util.find_spec("chatterbox") is not None
    gpu = "n/a"
    if cb:
        try:
            import torch
            if torch.cuda.is_available():
                gpu = f"CUDA ({torch.cuda.get_device_name(0)})"
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                gpu = "Apple MPS"
            else:
                gpu = "none - CPU only, generation will be slow"
        except Exception as e:  # noqa: BLE001
            gpu = f"torch error: {e}"
    print(f"[{ok(cb)}] chatterbox-tts    {('accelerator: ' + gpu) if cb else 'pip install -r video-tools/requirements.txt'}")

    uvx = shutil.which("uvx")
    print(f"[{ok(bool(uvx))}] uvx (runs Blender MCP) {uvx or 'install uv: https://docs.astral.sh/uv/'}")

    blender = shutil.which("blender")
    print(f"[{'OK     ' if blender else 'INFO   '}] blender on PATH   {blender or 'not on PATH (fine if installed as an app)'}")

    host = os.environ.get("BLENDER_HOST", "localhost")
    port = int(os.environ.get("BLENDER_PORT", "9876"))
    try:
        with socket.create_connection((host, port), timeout=1):
            up = True
    except OSError:
        up = False
    print(f"[{ok(up)}] Blender addon server at {host}:{port}  "
          f"{'' if up else '-> open Blender, press N, MCP for Blender tab, Start MCP Server'}")

    if ff:
        enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
        filt = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        print(f"[{ok('libx264' in enc)}] ffmpeg libx264    [{ok(' subtitles ' in filt)}] ffmpeg subtitles filter (libass)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
