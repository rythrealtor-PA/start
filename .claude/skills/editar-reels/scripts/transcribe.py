#!/usr/bin/env python3
"""Word-level transcription of a video, run locally.

Usage:
  python3 transcribe.py INPUT_VIDEO OUTPUT.json [--language es|en] [--model small]

Writes:
  OUTPUT.json  {"language": ..., "duration": ..., "words": [{"w","start","end"}...]}
  OUTPUT.txt   readable transcript, one line per segment with [mm:ss.s] timestamps

Uses faster-whisper if installed, otherwise openai-whisper. Audio never leaves the machine.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def extract_audio(video, wav):
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)],
        check=True,
    )


def fmt(t):
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:04.1f}"


def run_faster_whisper(wav, model_name, language):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="auto", compute_type="int8")
    segments, info = model.transcribe(str(wav), language=language, word_timestamps=True, vad_filter=False)
    words, segs = [], []
    for seg in segments:
        segs.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
        for w in seg.words or []:
            words.append({"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
    return info.language, words, segs


def run_openai_whisper(wav, model_name, language):
    import whisper
    model = whisper.load_model(model_name)
    result = model.transcribe(str(wav), language=language, word_timestamps=True)
    words, segs = [], []
    for seg in result.get("segments", []):
        segs.append({"start": seg["start"], "end": seg["end"], "text": seg["text"].strip()})
        for w in seg.get("words", []):
            words.append({"w": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)})
    return result.get("language", language), words, segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--language", default=None, help="es, en… (recommended: speeds up and avoids mistakes)")
    ap.add_argument("--model", default=os.environ.get("REELS_WHISPER_MODEL", "small"),
                    help="tiny/base/small/medium/large-v3 (bigger = more accurate, slower)")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        sys.exit(f"No encuentro el video: {src}")
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "audio.wav"
        extract_audio(src, wav)
        try:
            import faster_whisper  # noqa: F401
            engine = "faster-whisper"
            lang, words, segs = run_faster_whisper(wav, args.model, args.language)
        except ImportError:
            try:
                import whisper  # noqa: F401
                engine = "openai-whisper"
                lang, words, segs = run_openai_whisper(wav, args.model, args.language)
            except ImportError:
                sys.exit("No hay transcriptor instalado. Instala uno con:\n  "
                         f"{sys.executable} -m pip install faster-whisper")

    data = {"source": str(src), "engine": engine, "model": args.model, "language": lang,
            "duration": probe_duration(src), "words": words}
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    txt = out.with_suffix(".txt")
    txt.write_text("\n".join(f"[{fmt(s['start'])} - {fmt(s['end'])}] {s['text']}" for s in segs) + "\n", encoding="utf-8")
    print(f"{len(words)} palabras · idioma {lang} · {engine}/{args.model}")
    print(f"JSON: {out}\nTexto: {txt}")


if __name__ == "__main__":
    main()
