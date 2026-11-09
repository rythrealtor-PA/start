#!/usr/bin/env python3
"""Cut silences and bad takes out of a talking-head video (jump cuts).

Usage (with transcript from transcribe.py — recommended):
  python3 cut_silences.py --input toma.mp4 --words palabras.json --output v1_corte.mp4 \
      [--words-out palabras_corte.json] [--drop "12.4-17.9,41-44.2"] [--max-gap 0.35] [--pad 0.03]

Usage without transcript (detects silence from the audio):
  python3 cut_silences.py --input toma.mp4 --from-silence --output v1_corte.mp4 [--noise -35] [--min-silence 0.4]

--drop   time ranges (in seconds of the ORIGINAL video) to remove, e.g. false starts / repeated takes.
--max-gap pauses longer than this between words are removed (natural pauses shorter than this stay).
--pad    margin kept before/after each word so syllables are not clipped (default 30 ms).
--dry-run only print the plan (kept segments and resulting duration), do not render.

Cuts are snapped to the frame grid, so audio and video stay in sync no matter how many cuts there are.
Also writes OUTPUT.cortes.json with the kept segments (original time -> new time).
"""
import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,r_frame_rate,avg_frame_rate",
         "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    duration = float(info["format"]["duration"])
    fps, has_audio = None, False
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and fps is None:
            for key in ("avg_frame_rate", "r_frame_rate"):
                val = s.get(key, "0/0")
                if val and val != "0/0":
                    fr = Fraction(val)
                    if 1 <= fr <= 240:
                        fps = fr
                        break
        if s.get("codec_type") == "audio":
            has_audio = True
    return duration, fps or Fraction(30), has_audio


def parse_ranges(text):
    ranges = []
    if not text:
        return ranges
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        a, b = part.split("-")
        a, b = float(a), float(b)
        if b > a:
            ranges.append((a, b))
    return sorted(ranges)


def subtract(segments, cuts):
    """Remove the `cuts` intervals from `segments`."""
    result = []
    for s, e in segments:
        pieces = [(s, e)]
        for cs, ce in cuts:
            nxt = []
            for ps, pe in pieces:
                if ce <= ps or cs >= pe:
                    nxt.append((ps, pe))
                    continue
                if cs > ps:
                    nxt.append((ps, cs))
                if ce < pe:
                    nxt.append((ce, pe))
            pieces = nxt
        result.extend(pieces)
    return result


def merge(segments):
    segments = sorted(segments)
    out = []
    for s, e in segments:
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def segments_from_words(words, max_gap, pad, duration, drops):
    kept = [w for w in words if not any(a <= (w["start"] + w["end"]) / 2 <= b for a, b in drops)]
    segs = []
    cur = None
    for w in kept:
        s, e = w["start"], w["end"]
        if cur is None:
            cur = [s, e]
        elif s - cur[1] <= max_gap and not any(a < s and b > cur[1] for a, b in drops):
            cur[1] = max(cur[1], e)
        else:
            segs.append(tuple(cur))
            cur = [s, e]
    if cur:
        segs.append(tuple(cur))
    padded = [(max(0.0, s - pad), min(duration, e + pad)) for s, e in segs]
    return merge(subtract(merge(padded), drops)), kept


def segments_from_silence(path, duration, noise, min_silence, pad, drops):
    res = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
         f"silencedetect=n={noise}dB:d={min_silence}", "-f", "null", "-"],
        capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", res.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", res.stderr)]
    silences = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else duration
        silences.append((max(0.0, s + pad), max(0.0, e - pad)))
    speech = subtract([(0.0, duration)], [x for x in silences if x[1] > x[0]])
    return merge(subtract(speech, drops))


def snap(segments, fps, min_len):
    snapped = []
    for s, e in segments:
        s2 = math.floor(s * fps) / fps
        e2 = math.ceil(e * fps) / fps
        if e2 - s2 >= min_len:
            snapped.append((float(s2), float(e2)))
    return merge(snapped)


def remap(words, segments):
    out, offset, table = [], 0.0, []
    for s, e in segments:
        table.append((s, e, offset))
        offset += e - s
    for w in words:
        mid = (w["start"] + w["end"]) / 2
        for s, e, off in table:
            if s <= mid <= e:
                ns = off + max(0.0, w["start"] - s)
                ne = off + min(e - s, w["end"] - s)
                out.append({**w, "start": round(ns, 3), "end": round(max(ne, ns + 0.02), 3)})
                break
    return out, table


def render(src, dst, segments, fps, has_audio, crf, preset):
    eps = 0.5 / float(fps)
    # frame k is kept when k/fps is in [s, e): compare against half-frame-shifted bounds so float
    # rounding never drops or adds a frame at a cut
    expr = "+".join(f"between(t\\,{s - eps:.6f}\\,{e - eps:.6f})" for s, e in segments)
    graph = f"[0:v]fps={fps.numerator}/{fps.denominator},select='{expr}',setpts=N/FRAME_RATE/TB[v]"
    if has_audio:
        # exclusive end for audio so its length matches the selected video frames exactly
        aexpr = "+".join(f"(gte(t\\,{s:.6f})*lt(t\\,{e:.6f}))" for s, e in segments)
        graph += f";[0:a]aselect='{aexpr}',asetpts=N/SR/TB[a]"
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(graph)
        script = f.name
    cmd = ["ffmpeg", "-y", "-v", "error", "-stats", "-i", str(src), "-filter_complex_script", script, "-map", "[v]"]
    if has_audio:
        cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-crf", str(crf), "-preset", preset, "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(dst)]
    subprocess.run(cmd, check=True)
    Path(script).unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--words")
    ap.add_argument("--words-out")
    ap.add_argument("--from-silence", action="store_true")
    ap.add_argument("--drop", default="")
    ap.add_argument("--max-gap", type=float, default=0.35)
    ap.add_argument("--pad", type=float, default=0.03)
    ap.add_argument("--noise", type=float, default=-35)
    ap.add_argument("--min-silence", type=float, default=0.4)
    ap.add_argument("--min-segment", type=float, default=0.12)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="veryfast")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.input)
    duration, fps, has_audio = probe(src)
    drops = parse_ranges(args.drop)

    words = []
    if args.words:
        words = json.loads(Path(args.words).read_text(encoding="utf-8"))["words"]
        segments, kept = segments_from_words(words, args.max_gap, args.pad, duration, drops)
    elif args.from_silence:
        if not has_audio:
            sys.exit("El video no tiene audio; no puedo detectar silencios.")
        segments = segments_from_silence(src, duration, args.noise, args.min_silence, args.pad, drops)
        kept = []
    else:
        sys.exit("Indica --words palabras.json (recomendado) o --from-silence.")

    segments = snap(segments, fps, args.min_segment)
    if not segments:
        sys.exit("No quedó ningún tramo con voz. Revisa --drop, --noise o la transcripción.")
    new_words, table = remap(kept, segments)
    new_dur = sum(e - s for s, e in segments)

    print(f"Original: {duration:.1f}s · Final: {new_dur:.1f}s · Cortes: {len(segments) - 1} · "
          f"Quitado: {duration - new_dur:.1f}s ({100 * (duration - new_dur) / duration:.0f}%)")
    if args.dry_run:
        for s, e, off in table:
            print(f"  {s:8.2f} - {e:8.2f}  ->  {off:8.2f}")
        return

    dst = Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)
    render(src, dst, segments, fps, has_audio, args.crf, args.preset)

    edl = {"source": str(src), "fps": float(fps), "original_duration": duration, "new_duration": new_dur,
           "segments": [{"start": s, "end": e, "new_start": off} for s, e, off in table], "dropped": drops}
    dst.with_suffix(".cortes.json").write_text(json.dumps(edl, indent=1), encoding="utf-8")
    if args.words_out:
        Path(args.words_out).write_text(
            json.dumps({"source": str(dst), "duration": new_dur, "words": new_words}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"Palabras con tiempos nuevos: {args.words_out}")
    print(f"Video cortado: {dst}")


if __name__ == "__main__":
    main()
