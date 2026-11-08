#!/usr/bin/env python3
"""Put it all together with ffmpeg: visuals + voiceover + burned-in captions.

Visuals can be a video (e.g. a Blender render), a folder of Blender PNG frames,
or a single still image (it is held for the length of the voiceover).

Examples
--------
  # Blender MP4 render + voiceover + captions, vertical 1080x1920 for Reels/TikTok
  python video-tools/assemble.py --visual renders/house.mp4 --audio out/voiceover.wav \
      --subs out/voiceover.srt --size 1080x1920 --out out/final.mp4

  # Folder of Blender frames (0001.png, 0002.png, ...) at 30 fps
  python video-tools/assemble.py --visual renders/frames --fps 30 --audio out/voiceover.wav --out out/final.mp4

  # Single listing photo held under the voiceover, 16:9 for YouTube
  python video-tools/assemble.py --visual photo.jpg --audio out/voiceover.wav --subs out/voiceover.srt --out out/final.mp4

If the visual is shorter than the voiceover, the last frame is held; the output
always runs exactly as long as the voiceover.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".exr"}


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def subtitle_filter(subs: Path, font_size: int) -> str:
    # ffmpeg's filter syntax needs ':' and '\' escaped inside the path
    escaped = str(subs.resolve()).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
    style = (
        f"FontName=Arial,FontSize={font_size},Bold=1,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,Alignment=2,MarginV=60"
    )
    return f"subtitles='{escaped}':force_style='{style}'"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--visual", type=Path, required=True, help="Video file, image, or folder of frames")
    p.add_argument("--audio", type=Path, required=True, help="Voiceover (.wav/.mp3)")
    p.add_argument("--subs", type=Path, help="Captions .srt to burn in")
    p.add_argument("--music", type=Path, help="Optional background music (ducked to --music-volume)")
    p.add_argument("--music-volume", type=float, default=0.12)
    p.add_argument("--size", default="1920x1080", help="WxH, e.g. 1920x1080 (YouTube) or 1080x1920 (Reels/TikTok)")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--font-size", type=int, default=0, help="Caption size (0 = automatic)")
    p.add_argument("--out", type=Path, default=Path("final.mp4"))
    args = p.parse_args()

    if not shutil.which("ffmpeg"):
        p.error("ffmpeg is not installed (see docs/VIDEO_SETUP.md)")
    for path in [args.visual, args.audio] + ([args.subs] if args.subs else []) + ([args.music] if args.music else []):
        if not path.exists():
            p.error(f"not found: {path}")

    w, h = (int(x) for x in args.size.lower().split("x"))
    duration = probe_duration(args.audio)

    cmd = ["ffmpeg", "-y"]
    if args.visual.is_dir():
        frames = sorted(f for f in args.visual.iterdir() if f.suffix.lower() in IMAGE_EXT)
        if not frames:
            p.error(f"no image frames in {args.visual}")
        list_file = args.out.with_suffix(".frames.txt")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        list_file.write_text("".join(f"file '{f.resolve()}'\nduration {1 / args.fps:.6f}\n" for f in frames)
                             + f"file '{frames[-1].resolve()}'\n")
        cmd += ["-f", "concat", "-safe", "0", "-i", str(list_file)]
    elif args.visual.suffix.lower() in IMAGE_EXT:
        cmd += ["-loop", "1", "-framerate", str(args.fps), "-i", str(args.visual)]
    else:
        cmd += ["-i", str(args.visual)]
    cmd += ["-i", str(args.audio)]
    if args.music:
        cmd += ["-stream_loop", "-1", "-i", str(args.music)]

    vf = [
        f"scale={w}:{h}:force_original_aspect_ratio=increase",
        f"crop={w}:{h}",
        f"fps={args.fps}",
        f"tpad=stop_mode=clone:stop_duration={duration:.3f}",
        "format=yuv420p",
    ]
    if args.subs:
        vf.append(subtitle_filter(args.subs, args.font_size or max(14, round(min(w, h) / 1080 * 16))))
    filters = f"[0:v]{','.join(vf)}[v]"
    if args.music:
        filters += f";[2:a]volume={args.music_volume}[m];[1:a][m]amix=inputs=2:duration=first:normalize=0[a]"
        audio_map = "[a]"
    else:
        audio_map = "1:a"

    cmd += [
        "-filter_complex", filters, "-map", "[v]", "-map", audio_map,
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(args.out),
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    print("[assemble] " + " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)
    print(f"[assemble] wrote {args.out} ({duration:.1f}s, {w}x{h})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
