#!/usr/bin/env python3
"""Captions and timing with faster-whisper (free, open source, runs on CPU).

Examples
--------
  # Captions for a finished voiceover or video
  python video-tools/transcribe.py out/voiceover.wav

  # Short punchy captions for Reels/TikTok/Shorts (3 words per caption)
  python video-tools/transcribe.py out/voiceover.wav --max-words 3

  # Better accuracy (slower): small, medium, large-v3, turbo
  python video-tools/transcribe.py interview.mp4 --model medium --lang en

Outputs, next to the input unless --out-dir is given:
  <name>.srt   captions for YouTube / editors / ffmpeg burn-in
  <name>.vtt   web captions
  <name>.json  every segment and word with start/end times, so Claude can
               cut scenes, time Blender keyframes, or find what was said when
  <name>.txt   plain transcript
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def fmt_time(seconds: float, sep: str) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def build_cues(segments: list[dict], max_words: int, max_chars: int) -> list[dict]:
    """Group words into caption cues. max_words=0 keeps whisper's own segments."""
    if max_words <= 0:
        return [{"start": s["start"], "end": s["end"], "text": s["text"].strip()} for s in segments]
    cues: list[dict] = []
    for seg in segments:
        words = seg.get("words") or []
        current: list[dict] = []
        for w in words:
            candidate = "".join(x["word"] for x in current + [w]).strip()
            if current and (len(current) >= max_words or len(candidate) > max_chars):
                cues.append(_cue(current))
                current = []
            current.append(w)
            if w["word"].rstrip().endswith((".", "!", "?")):
                cues.append(_cue(current))
                current = []
        if current:
            cues.append(_cue(current))
    return cues


def _cue(words: list[dict]) -> dict:
    return {"start": words[0]["start"], "end": words[-1]["end"], "text": "".join(w["word"] for w in words).strip()}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("media", type=Path, help="Audio or video file")
    p.add_argument("--model", default="small", help="tiny, base, small, medium, large-v3, turbo (default: small)")
    p.add_argument("--lang", default=None, help="Language code (auto-detect if omitted)")
    p.add_argument("--max-words", type=int, default=0, help="Words per caption (0 = natural sentences)")
    p.add_argument("--max-chars", type=int, default=42, help="Max characters per caption line")
    p.add_argument("--out-dir", type=Path, default=None)
    p.add_argument("--device", default="auto", help="auto, cpu or cuda")
    p.add_argument("--compute-type", default="default", help="e.g. int8 (CPU), float16 (GPU)")
    args = p.parse_args()

    if not args.media.exists():
        p.error(f"file not found: {args.media}")

    from faster_whisper import WhisperModel

    print(f"[whisper] loading model '{args.model}' ...", file=sys.stderr)
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    seg_iter, info = model.transcribe(str(args.media), language=args.lang, word_timestamps=True, vad_filter=True)
    print(f"[whisper] language={info.language} ({info.language_probability:.0%}), duration={info.duration:.1f}s", file=sys.stderr)

    segments = []
    for s in seg_iter:
        segments.append({
            "start": round(s.start, 3),
            "end": round(s.end, 3),
            "text": s.text.strip(),
            "words": [{"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word} for w in (s.words or [])],
        })
        print(f"  [{s.start:6.2f} -> {s.end:6.2f}] {s.text.strip()}", file=sys.stderr)

    cues = build_cues(segments, args.max_words, args.max_chars)
    out_dir = args.out_dir or args.media.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / args.media.stem

    with open(f"{base}.srt", "w", encoding="utf-8") as f:
        for i, c in enumerate(cues, 1):
            f.write(f"{i}\n{fmt_time(c['start'], ',')} --> {fmt_time(c['end'], ',')}\n{c['text']}\n\n")
    with open(f"{base}.vtt", "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for c in cues:
            f.write(f"{fmt_time(c['start'], '.')} --> {fmt_time(c['end'], '.')}\n{c['text']}\n\n")
    with open(f"{base}.json", "w", encoding="utf-8") as f:
        json.dump({"language": info.language, "duration": round(info.duration, 3), "segments": segments, "captions": cues}, f, indent=2, ensure_ascii=False)
    with open(f"{base}.txt", "w", encoding="utf-8") as f:
        f.write(" ".join(s["text"] for s in segments).strip() + "\n")

    print(f"[whisper] wrote {base}.srt .vtt .json .txt ({len(cues)} captions)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
