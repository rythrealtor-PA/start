#!/usr/bin/env python3
"""Final pass: music (ducked under the voice), sound effects, logo end card, loudness and cover frame.

Usage:
  python3 finalize.py --input v3.mp4 --output final.mp4 \
      [--music musica/tema.mp3 --music-db -20 --duck] \
      [--sfx "0.2:sfx/whoosh.wav,14.8:sfx/click.wav" --sfx-db -6] \
      [--logo marca/logos/logo.png --logo-seconds 2.5 --logo-width 0.62] \
      [--cover portada.jpg --cover-time 1.0] [--lufs -14 | --no-loudnorm]

--duck       music automatically drops while the person is speaking (sidechain compression).
--sfx        list of second:file pairs, in seconds of THIS video.
--logo       brand end card: N extra seconds are added after the last word; the final frame freezes,
             blurs and darkens, and the logo fades in while the music fades out.
             --logo-mode overlay puts the card over the last N seconds instead (no extra time).
Loudness is normalized to -14 LUFS (the usual target for Instagram/TikTok/YouTube).
"""
import argparse
import json
import subprocess
from pathlib import Path

AFMT = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    dur = float(info["format"]["duration"])
    w = h = None
    has_audio = False
    for s in info["streams"]:
        if s["codec_type"] == "video" and w is None:
            w, h = s["width"], s["height"]
        if s["codec_type"] == "audio":
            has_audio = True
    return dur, w, h, has_audio


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--music")
    ap.add_argument("--music-db", type=float, default=-20)
    ap.add_argument("--duck", action="store_true")
    ap.add_argument("--sfx", default="")
    ap.add_argument("--sfx-db", type=float, default=-6)
    ap.add_argument("--logo")
    ap.add_argument("--logo-seconds", type=float, default=2.5)
    ap.add_argument("--logo-mode", choices=["append", "overlay"], default="append")
    ap.add_argument("--logo-width", type=float, default=0.62, help="logo width as a fraction of the video width")
    ap.add_argument("--darken", type=float, default=0.6, help="how dark the end card background gets (0-1)")
    ap.add_argument("--cover")
    ap.add_argument("--cover-time", type=float, default=1.0)
    ap.add_argument("--lufs", type=float, default=-14)
    ap.add_argument("--no-loudnorm", action="store_true")
    ap.add_argument("--crf", type=int, default=18)
    args = ap.parse_args()

    dur, W, H, has_audio = probe(args.input)
    inputs = ["-i", args.input]
    n = 1
    graph = []

    # --- video: optional logo end card
    vout = "0:v"
    total = dur
    if args.logo:
        if args.logo_mode == "append":
            start = dur
            total = dur + args.logo_seconds
        else:
            start = max(0.0, dur - args.logo_seconds)
        inputs += ["-loop", "1", "-t", f"{args.logo_seconds:.3f}", "-i", args.logo]
        li = n
        n += 1
        lw = round(W * args.logo_width / 2) * 2
        pad = f"tpad=stop_mode=clone:stop_duration={args.logo_seconds:.3f}," if args.logo_mode == "append" else ""
        graph.append(f"[0:v]{pad}boxblur=20:2:enable='gte(t,{start:.3f})',"
                     f"drawbox=x=0:y=0:w=iw:h=ih:color=black@{args.darken}:t=fill:enable='gte(t,{start:.3f})'[bg]")
        graph.append(f"[{li}:v]scale={lw}:-1,format=rgba,fade=t=in:st=0:d=0.5:alpha=1,"
                     f"setpts=PTS-STARTPTS+{start:.3f}/TB[lg]")
        graph.append("[bg][lg]overlay=(W-w)/2:(H-h)/2:eof_action=pass:format=auto[vout]")
        vout = "[vout]"

    # --- audio
    mix = []
    if has_audio:
        graph.append(f"[0:a]{AFMT},apad=whole_dur={total:.3f}[voice0]")
    else:
        graph.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{total:.3f}[voice0]")
    voice = "voice0"

    if args.music:
        inputs += ["-stream_loop", "-1", "-i", args.music]
        mi = n
        n += 1
        fade_st = max(0.0, total - 1.5)
        graph.append(f"[{mi}:a]{AFMT},volume={args.music_db}dB,atrim=0:{total:.3f},"
                     f"afade=t=in:d=0.4,afade=t=out:st={fade_st:.3f}:d=1.5[mus]")
        if args.duck and has_audio:
            graph.append(f"[{voice}]asplit=2[voice1][sc]")
            graph.append("[mus][sc]sidechaincompress=threshold=0.03:ratio=8:attack=15:release=400[musd]")
            voice = "voice1"
            mix.append("[musd]")
        else:
            mix.append("[mus]")

    for k, item in enumerate(x for x in args.sfx.split(",") if x.strip()):
        t, f = item.split(":", 1)
        inputs += ["-i", f.strip()]
        si = n
        n += 1
        ms = max(0, round(float(t) * 1000))
        graph.append(f"[{si}:a]{AFMT},volume={args.sfx_db}dB,adelay={ms}|{ms}[sfx{k}]")
        mix.append(f"[sfx{k}]")

    chain = f"[{voice}]" + "".join(mix)
    post = "" if args.no_loudnorm else f",loudnorm=I={args.lufs}:TP=-1.5:LRA=11,{AFMT}"
    if mix:
        graph.append(f"{chain}amix=inputs={1 + len(mix)}:duration=first:normalize=0{post}[aout]")
    else:
        graph.append(f"[{voice}]anull{post}[aout]")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-stats", *inputs, "-filter_complex", ";".join(graph),
           "-map", vout if vout.startswith("[") else "0:v", "-map", "[aout]",
           "-c:v", "libx264", "-crf", str(args.crf), "-preset", "veryfast", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart", args.output]
    subprocess.run(cmd, check=True)
    print(f"Video final: {args.output} ({total:.1f}s, {W}x{H})")

    if args.cover:
        t = min(max(0.0, args.cover_time), max(0.0, total - 0.1))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", args.output, "-frames:v", "1",
                        "-q:v", "2", args.cover], check=True)
        print(f"Portada (frame {t:.1f}s): {args.cover}")


if __name__ == "__main__":
    main()
