#!/usr/bin/env python3
"""Estimate how long a script takes to say out loud, section by section.

Usage:
  python3 estimar_duracion.py GUION.md [--lang en|es] [--wps 2.5] [--target 45] [--json]

Reads the "## Texto para grabar" section of the script (or the whole file if there is none).
Section markers are lines like [HOOK], [PUNTO 1], [CIERRE]. "(pausa)" adds 0.5 s.
Numbers are counted the way they are spoken ("$400,000" ~ "four hundred thousand dollars").
Default speaking rate: English 2.5 words/s (~150 wpm), Spanish 2.7 words/s.
Prints start-end times per section so they can be copied into the timed script table.
Exit code 1 if --target is given and the estimate goes over it by more than 10%.
"""
import argparse
import json
import re
import sys
from pathlib import Path

RATES = {"en": 2.5, "es": 2.7}
MARKER = re.compile(r"^\s*\[([^\]]{1,40})\]\s*$")
PAUSE = re.compile(r"\((?:pausa|pause)\)", re.I)
NUMBER = re.compile(r"[$€£]?\d[\d,.]*%?[kKmM]?")


def extract_spoken(text):
    m = re.search(r"^##\s*Texto para grabar.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    body = m.group(1) if m else text
    return body.replace("```", "")


def small_number_words(n):
    """Words needed to say 0-999 ("four hundred" = 2, "forty-five" = 1, "eighteen" = 1)."""
    words = 0
    if n >= 100:
        words += 2
        n %= 100
    if n:
        words += 1
    return words


def number_words(token):
    """Approximate spoken words: "$400,000" -> "four hundred thousand dollars" = 4."""
    t = token.strip(".,!?;:\"'")
    integer = re.sub(r"\D", "", re.split(r"\.(?=\d{1,2}\b)", t)[0])
    if not integer:
        return 1
    groups = []
    while integer:
        groups.insert(0, int(integer[-3:]))
        integer = integer[:-3]
    n = 0
    for i, g in enumerate(groups):
        if g:
            n += small_number_words(g)
            if i < len(groups) - 1:
                n += 1  # thousand / million
    n = max(n, 1)
    n += 1 if t[0] in "$€£" else 0
    n += 1 if t.endswith("%") else 0
    n += 1 if t[-1:] in "kKmM" else 0
    return n


def spoken_words(line):
    count = 0
    for tok in line.split():
        if NUMBER.fullmatch(tok.strip(".,!?;:\"'")):
            count += number_words(tok)
        elif re.search(r"\w", tok):
            count += 1
    return count


def parse(body):
    sections = []
    current = {"name": "INICIO", "words": 0, "pauses": 0}
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("|") or line.startswith(">"):
            continue
        m = MARKER.match(line)
        if m:
            if current["words"] or current["pauses"]:
                sections.append(current)
            current = {"name": m.group(1).strip().upper(), "words": 0, "pauses": 0}
            continue
        pauses = len(PAUSE.findall(line))
        line = PAUSE.sub(" ", line)
        current["pauses"] += pauses
        current["words"] += spoken_words(line)
    if current["words"] or current["pauses"]:
        sections.append(current)
    return sections


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--lang", choices=sorted(RATES), default="en")
    ap.add_argument("--wps", type=float, help="words per second (overrides --lang)")
    ap.add_argument("--target", type=float, help="target duration in seconds")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        sys.exit(f"No encuentro el archivo: {path}")
    rate = args.wps or RATES[args.lang]
    sections = parse(extract_spoken(path.read_text(encoding="utf-8")))
    if not sections:
        sys.exit("No encontré texto hablado. ¿Tiene la sección '## Texto para grabar'?")

    t = 0.0
    for s in sections:
        s["start"] = round(t, 1)
        t += s["words"] / rate + 0.5 * s["pauses"]
        s["end"] = round(t, 1)
        s["seconds"] = round(s["end"] - s["start"], 1)
    total = round(t, 1)
    words = sum(s["words"] for s in sections)
    over = args.target is not None and total > args.target * 1.1

    if args.json:
        print(json.dumps({"rate_wps": rate, "total_seconds": total, "total_words": words,
                          "target": args.target, "over_target": over, "sections": sections},
                         ensure_ascii=False, indent=1))
    else:
        print(f"{'Sección':<14}{'Palabras':>9}{'Tiempo':>16}{'Seg':>7}")
        for s in sections:
            print(f"{s['name'][:13]:<14}{s['words']:>9}{s['start']:>8.1f}–{s['end']:<6.1f}{s['seconds']:>7.1f}")
        print(f"{'TOTAL':<14}{words:>9}{'':>16}{total:>7.1f}   ({rate} palabras/s)")
        if args.target is not None:
            if over:
                cut = round((total - args.target) * rate)
                print(f"⚠ Se pasa del objetivo de {args.target:.0f} s: recorta unas {cut} palabras (mejor del cuerpo que del hook).")
            elif total < args.target * 0.6:
                print(f"Queda bastante por debajo de {args.target:.0f} s: está bien si el mensaje está completo.")
            else:
                print(f"Dentro del objetivo de {args.target:.0f} s.")
    sys.exit(1 if over else 0)


if __name__ == "__main__":
    main()
