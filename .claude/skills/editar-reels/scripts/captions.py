#!/usr/bin/env python3
"""Animated word-by-word captions with highlighted keywords (ASS subtitles), optionally burned in.

Usage:
  python3 captions.py --words palabras_corte.json --output subs.ass \
      [--keywords "Poconos,llaves,$400,000"] [--style marca/estilo.md] [--fontsdir marca/fuentes] \
      [--burn v1_vertical.mp4 --burn-out v2_subs.mp4]

Look:
  - short phrases (max 4 words by default) centered in the safe zone
  - the word being spoken lights up in the accent color
  - keywords are always bigger, in the accent font and color
  - numbers, prices and percentages are treated as keywords automatically (--no-auto-numbers to disable)
  - each phrase pops in with a quick scale animation
Settings come from estilo.md (`clave: valor` lines); command-line flags override them.
"""
import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path

DEFAULTS = {
    "color_texto": "#FFFFFF",
    "color_acento": "#E8B04B",
    "color_borde": "#000000",
    "fuente_principal": "Inter",
    "fuente_acento": "Playfair Display",
    "tamano_texto": "74",
    "max_palabras": "4",
    "mayusculas": "no",
    "posicion_y": "1180",
}


def read_style(path):
    cfg = dict(DEFAULTS)
    if path and Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*([a-z_]+)\s*:\s*(.+?)\s*$", line)
            if m and m.group(1) in DEFAULTS and not m.group(2).startswith("["):
                cfg[m.group(1)] = m.group(2)
    return cfg


def ass_color(hex_color, alpha=0):
    h = hex_color.strip().lstrip("#")
    if len(h) != 6:
        raise SystemExit(f"Color inválido: {hex_color} (usa formato #RRGGBB)")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def norm(text):
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^\w$%]", "", text)


NUMBER_RE = re.compile(r"[$€£]?\d[\d,.]*\s*%?|\d+[kKmM]\b")


def is_number(word):
    return bool(NUMBER_RE.search(word))


def escape(text):
    return text.replace("\\", "").replace("{", "(").replace("}", ")")


def chunk_words(words, max_words, max_gap=0.6):
    chunks, cur = [], []
    for i, w in enumerate(words):
        if cur:
            gap = w["start"] - cur[-1]["end"]
            ends_sentence = re.search(r"[.,;:!?…]$", cur[-1]["w"])
            if len(cur) >= max_words or ends_sentence or gap > max_gap:
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def ts(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def probe_size(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout.strip()
    w, h = out.split(",")[:2]
    return int(w), int(h)


def filter_path(p):
    return str(Path(p).resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--words", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--keywords", default="")
    ap.add_argument("--keywords-file")
    ap.add_argument("--style")
    ap.add_argument("--font")
    ap.add_argument("--accent-font")
    ap.add_argument("--color")
    ap.add_argument("--accent")
    ap.add_argument("--outline-color")
    ap.add_argument("--size", type=int)
    ap.add_argument("--max-words", type=int)
    ap.add_argument("--y", type=int, help="vertical position of the caption center, in a 1920-tall frame")
    ap.add_argument("--upper", action="store_true")
    ap.add_argument("--no-active", action="store_true", help="do not light up the word being spoken")
    ap.add_argument("--no-auto-numbers", action="store_true")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--fontsdir")
    ap.add_argument("--burn", help="video to burn the captions into")
    ap.add_argument("--burn-out")
    args = ap.parse_args()

    cfg = read_style(args.style)
    font = args.font or cfg["fuente_principal"]
    accent_font = args.accent_font or cfg["fuente_acento"]
    color = ass_color(args.color or cfg["color_texto"])
    accent = ass_color(args.accent or cfg["color_acento"])
    outline = ass_color(args.outline_color or cfg["color_borde"])
    max_words = args.max_words or int(cfg["max_palabras"])
    upper = args.upper or cfg["mayusculas"].lower() in ("si", "sí", "yes", "true")

    W, H = args.width, args.height
    if args.burn:
        W, H = probe_size(args.burn)
    scale = H / 1920
    size = round((args.size or int(cfg["tamano_texto"])) * scale)
    y = round((args.y or int(cfg["posicion_y"])) * scale)

    kw_text = args.keywords
    if args.keywords_file:
        kw_text += "," + Path(args.keywords_file).read_text(encoding="utf-8").replace("\n", ",")
    keywords = {norm(tok) for phrase in kw_text.split(",") for tok in phrase.split() if norm(tok)}

    data = json.loads(Path(args.words).read_text(encoding="utf-8"))
    words = []
    for w in data["words"]:
        text = w["w"].strip()
        if not text:
            continue
        if words and not re.search(r"\w", text):
            # stray punctuation token: glue it to the previous word instead of showing it alone
            words[-1] = {**words[-1], "w": words[-1]["w"] + text, "end": max(words[-1]["end"], w["end"])}
            continue
        words.append({**w, "w": text})
    if not words:
        raise SystemExit("La transcripción no tiene palabras.")

    def is_kw(w):
        return norm(w) in keywords or (not args.no_auto_numbers and is_number(w))

    def styled(word, active):
        txt = escape(word.upper() if upper else word)
        if is_kw(word):
            return f"{{\\fn{accent_font}\\c{accent}\\fscx118\\fscy118}}{txt}{{\\r}}"
        if active:
            return f"{{\\c{accent}}}{txt}{{\\r}}"
        return txt

    chunks = chunk_words(words, max_words)
    events = []
    for ci, ch in enumerate(chunks):
        start = ch[0]["start"]
        nxt = chunks[ci + 1][0]["start"] if ci + 1 < len(chunks) else None
        end = ch[-1]["end"] + 0.15
        if nxt is not None and nxt - ch[-1]["end"] < 0.3:
            end = nxt
        if nxt is not None:
            end = min(end, nxt)
        end = max(end, start + 0.35)
        pos = f"{{\\an5\\pos({W // 2},{y})}}"
        pop = "{\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}"
        if args.no_active:
            text = " ".join(styled(w["w"], False) for w in ch)
            events.append((start, end, pos + pop + text))
            continue
        for i, w in enumerate(ch):
            ws = start if i == 0 else w["start"]
            we = ch[i + 1]["start"] if i + 1 < len(ch) else end
            if we <= ws:
                continue
            text = " ".join(styled(x["w"], j == i) for j, x in enumerate(ch))
            events.append((ws, we, pos + (pop if i == 0 else "") + text))

    outline_w = max(2, round(5 * scale))
    shadow = max(1, round(2 * scale))
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},{size},{color},{color},{outline},&H80000000,-1,0,0,0,100,100,0,0,1,{outline_w},{shadow},5,{round(90 * scale)},{round(140 * scale)},0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [f"Dialogue: 0,{ts(s)},{ts(e)},Caption,,0,0,0,,{t}" for s, e, t in events]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(chunks)} frases · {len(events)} eventos · palabras clave: {', '.join(sorted(keywords)) or '(solo números)'}")
    print(f"Subtítulos: {out}")

    if args.burn:
        dst = args.burn_out or str(Path(args.burn).with_name(Path(args.burn).stem + "_subs.mp4"))
        vf = f"ass='{filter_path(out)}'"
        if args.fontsdir and Path(args.fontsdir).exists():
            vf = f"ass='{filter_path(out)}':fontsdir='{filter_path(args.fontsdir)}'"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-stats", "-i", args.burn, "-vf", vf,
                        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                        "-c:a", "copy", "-movflags", "+faststart", dst], check=True)
        print(f"Video con subtítulos: {dst}")


if __name__ == "__main__":
    main()
