#!/usr/bin/env python3
"""Voiceover generation with Chatterbox TTS (free, open source, by Resemble AI).

Examples
--------
  # Default voice, from a script file
  python video-tools/tts.py --file script.txt --out out/voiceover.wav

  # Clone a voice from a ~10 second reference clip of YOUR OWN voice
  python video-tools/tts.py --text "Welcome to the open house!" --voice me.wav --out vo.wav

  # Faster "turbo" model (English only, needs --voice); supports tags like [laugh] [chuckle]
  python video-tools/tts.py --model turbo --voice me.wav --file script.txt --out vo.wav

  # Spanish (or any of 23 languages) with the multilingual model
  python video-tools/tts.py --model multilingual --lang es --text "Hola a todos" --out vo_es.wav

Long scripts are split into sentences, generated one by one, and joined with a
short pause, which keeps quality high and avoids the model rushing or cutting off.
Only clone voices you own or have permission to use. Chatterbox adds an inaudible
watermark to everything it generates.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def pick_device(requested: str) -> str:
    import torch

    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def split_script(text: str, max_chars: int) -> list[str]:
    """Split into sentence-sized chunks no longer than max_chars."""
    text = re.sub(r"[ \t]+", " ", text.strip())
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n{2,}", text) if s.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + 1 + len(sentence) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def load_model(kind: str, device: str):
    if kind == "turbo":
        from chatterbox.tts_turbo import ChatterboxTurboTTS

        return ChatterboxTurboTTS.from_pretrained(device=device)
    if kind == "multilingual":
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        return ChatterboxMultilingualTTS.from_pretrained(device=device)
    from chatterbox.tts import ChatterboxTTS

    return ChatterboxTTS.from_pretrained(device=device)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="Text to speak")
    src.add_argument("--file", type=Path, help="Text file with the script")
    p.add_argument("--out", type=Path, default=Path("voiceover.wav"), help="Output .wav path")
    p.add_argument("--model", choices=["standard", "turbo", "multilingual"], default="standard")
    p.add_argument("--voice", type=Path, help="Reference clip (~10s wav) to clone the voice from")
    p.add_argument("--lang", default="en", help="Language id for --model multilingual (en, es, fr, ...)")
    p.add_argument("--exaggeration", type=float, default=0.5, help="Emotion intensity, 0.25-2.0 (standard/multilingual)")
    p.add_argument("--cfg-weight", type=float, default=0.5, help="Pacing; lower (~0.3) = slower, more deliberate")
    p.add_argument("--pause", type=float, default=0.35, help="Seconds of silence between sentences")
    p.add_argument("--max-chars", type=int, default=300, help="Max characters per generated chunk")
    p.add_argument("--device", default="auto", help="auto, cuda, mps or cpu")
    args = p.parse_args()

    if args.model == "turbo" and not args.voice:
        p.error("--model turbo needs --voice (a ~10 second reference clip)")
    if args.voice and not args.voice.exists():
        p.error(f"voice clip not found: {args.voice}")

    text = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
    chunks = split_script(text, args.max_chars)
    if not chunks:
        p.error("script is empty")

    import torch
    import torchaudio as ta

    device = pick_device(args.device)
    print(f"[tts] loading Chatterbox {args.model} on {device} ...", file=sys.stderr)
    model = load_model(args.model, device)

    kwargs: dict = {}
    if args.voice:
        kwargs["audio_prompt_path"] = str(args.voice)
    if args.model != "turbo":
        kwargs["exaggeration"] = args.exaggeration
        kwargs["cfg_weight"] = args.cfg_weight
    if args.model == "multilingual":
        kwargs["language_id"] = args.lang

    silence = torch.zeros(1, int(model.sr * args.pause))
    pieces = []
    for i, chunk in enumerate(chunks, 1):
        print(f"[tts] {i}/{len(chunks)}: {chunk[:70]}{'...' if len(chunk) > 70 else ''}", file=sys.stderr)
        wav = model.generate(chunk, **kwargs).detach().cpu()
        if wav.dim() == 1:
            wav = wav.unsqueeze(0)
        pieces.extend([wav, silence])

    audio = torch.cat(pieces[:-1], dim=-1)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    ta.save(str(args.out), audio, model.sr)
    print(f"[tts] wrote {args.out} ({audio.shape[-1] / model.sr:.1f}s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
