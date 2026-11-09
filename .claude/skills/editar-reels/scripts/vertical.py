#!/usr/bin/env python3
"""Turn a video into vertical 9:16 (1080x1920 by default).

Usage:
  python3 vertical.py INPUT OUTPUT [--mode crop|blur] [--x 0.5] [--y 0.5] [--height 1920] [--zoom 1.0]

crop (default): fills the frame, cutting the sides. --x moves the window left (0) / right (1)
                so the face stays centered (0.5 = middle).
blur:           shows the full original frame in the middle with a blurred copy behind it.
--height 3840 gives 4K vertical (2160x3840).
If the input is already vertical, it is only scaled/padded to the target size.
"""
import argparse
import json
import subprocess
from pathlib import Path


def size(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:stream_side_data=rotation", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    st = json.loads(out)["streams"][0]
    w, h = st["width"], st["height"]
    rot = 0
    for sd in st.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = abs(int(sd["rotation"]))
    if rot in (90, 270):
        w, h = h, w
    return w, h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--mode", choices=["crop", "blur"], default="crop")
    ap.add_argument("--x", type=float, default=0.5)
    ap.add_argument("--y", type=float, default=0.5)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--zoom", type=float, default=1.0, help=">1 punches in (e.g. 1.1) for a tighter framing")
    ap.add_argument("--crf", type=int, default=18)
    args = ap.parse_args()

    H = args.height
    W = round(H * 9 / 16 / 2) * 2
    w, h = size(args.input)

    if args.mode == "blur":
        vf = (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,"
              f"eq=brightness=-0.08[bg];[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")
    else:
        # scale so the frame covers WxH (times zoom), then crop a window positioned by x/y
        vf = (f"scale='max({W}/iw,{H}/ih)*{args.zoom}*iw':'max({W}/iw,{H}/ih)*{args.zoom}*ih',"
              f"crop={W}:{H}:'(iw-{W})*{min(max(args.x, 0), 1)}':'(ih-{H})*{min(max(args.y, 0), 1)}',setsar=1")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-stats", "-i", args.input, "-filter_complex", vf,
                    "-c:v", "libx264", "-crf", str(args.crf), "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-c:a", "copy", "-movflags", "+faststart", args.output], check=True)
    print(f"{w}x{h} -> {W}x{H} ({args.mode}) : {args.output}")


if __name__ == "__main__":
    main()
