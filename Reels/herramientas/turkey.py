#!/usr/bin/env python3
"""Turkey animado que se asoma por los costados del video, saluda con el ala y parpadea.

Uso:
  python3 turkey.py --input video.mp4 --output salida.mp4 [--first 6 --gap 6 --show 8 --size 560 --y 1000]
  python3 turkey.py --preview carpeta   (solo dibuja cuadros de prueba)

Ciclo: espera `first` s, aparece `show` s (izquierda), se va, pasan `gap` s, aparece del otro lado, etc.
Dibujo original (inspirado en el estilo cartoon de la referencia), sin sonido.
"""
import argparse, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw

S = 2           # supersampling
BOX = 600       # lienzo base del turkey (mira a la derecha)
OUT = (92, 44, 18, 255)        # contorno café oscuro
BROWN, BROWN2, BROWN3 = (139, 74, 43, 255), (165, 92, 52, 255), (112, 58, 32, 255)
WHITE, PINK, PINK2 = (255, 255, 255, 255), (244, 112, 126, 255), (226, 88, 104, 255)
RED, BEAK, BEAK2, BLACK = (214, 40, 52, 255), (247, 184, 41, 255), (226, 150, 25, 255), (30, 22, 20, 255)
LW = 7


def P(v): return v * S


def ell(d, cx, cy, rx, ry, fill, outline=OUT, w=LW):
    d.ellipse((P(cx - rx), P(cy - ry), P(cx + rx), P(cy + ry)), fill=fill, outline=outline, width=P(w) if outline else 0)


def poly(d, pts, fill, outline=OUT, w=LW):
    d.polygon([(P(x), P(y)) for x, y in pts], fill=fill, outline=outline, width=P(w) if outline else 0)


def feather(d, cx, cy, ang, r0, r1, half, fill):
    a = math.radians(ang); pts = []
    for k in range(11):  # pluma redondeada
        t = -half + 2 * half * k / 10
        r = r1 - (abs(t) / half) ** 2 * 18
        pts.append((cx + r * math.cos(a + math.radians(t)), cy + r * math.sin(a + math.radians(t))))
    pts = [(cx + r0 * math.cos(a - math.radians(half * 0.6)), cy + r0 * math.sin(a - math.radians(half * 0.6)))] + pts + \
          [(cx + r0 * math.cos(a + math.radians(half * 0.6)), cy + r0 * math.sin(a + math.radians(half * 0.6)))]
    poly(d, pts, fill)


def draw_turkey(wing_deg, blink, mouth=1.0):
    im = Image.new("RGBA", (P(BOX), P(BOX)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # cola en abanico (detrás)
    cx, cy = 235, 330
    angs = list(range(-172, -8, 20))
    for i, a in enumerate(angs): feather(d, cx, cy, a, 40, 235, 11, BROWN2 if i % 2 else BROWN)
    for i, a in enumerate(angs): feather(d, cx, cy, a, 40, 168, 9.5, WHITE)
    for i, a in enumerate(angs): feather(d, cx, cy, a, 40, 145, 9, BROWN3 if i % 2 else BROWN)
    # cuerpo
    ell(d, 275, 405, 158, 130, BROWN)
    for x, y in [(215, 400), (275, 440), (195, 455), (255, 485)]:
        d.arc((P(x - 26), P(y - 15), P(x + 26), P(y + 15)), 20, 160, fill=OUT, width=P(4))
    # cuello curvo rosa
    neck = [(300, 395), (330, 320), (372, 255), (448, 255), (420, 330), (392, 410)]
    poly(d, neck, PINK)
    # collar blanco
    for k in range(8):
        a = math.radians(195 + k * 24); x, y = 345 + 52 * math.cos(a), 398 + 24 * math.sin(a)
        ell(d, x, y, 16, 14, WHITE, w=4)
    ell(d, 345, 400, 46, 18, WHITE, outline=None)
    # cabeza grande
    d.rounded_rectangle((P(330), P(78), P(505), P(262)), P(70), fill=PINK, outline=OUT, width=P(LW))
    ell(d, 350, 222, 16, 11, PINK2, outline=None); ell(d, 470, 228, 12, 9, PINK2, outline=None)  # cachetes
    for ex in (385, 448):  # ojos grandes
        ey = 150
        ell(d, ex, ey, 23, 29, WHITE, w=5)
        ell(d, ex + 4, ey + 5, 13, 16, BLACK, outline=None)
        ell(d, ex + 9, ey - 2, 5, 5, WHITE, outline=None); ell(d, ex, ey + 12, 2.5, 2.5, WHITE, outline=None)
        if blink > 0:
            h = 29 * 2 * blink
            d.rectangle((P(ex - 26), P(ey - 31), P(ex + 26), P(ey - 31 + h)), fill=PINK)
            if blink > 0.85: d.arc((P(ex - 18), P(ey - 10), P(ex + 18), P(ey + 14)), 15, 165, fill=OUT, width=P(5))
            else: d.line((P(ex - 23), P(ey - 31 + h), P(ex + 23), P(ey - 31 + h)), fill=OUT, width=P(5))
    # pico abierto, feliz
    poly(d, [(470, 186), (540, 200), (476, 214)], BEAK, w=5)
    poly(d, [(474, 214), (528, 220 + 10 * mouth), (478, 232 + 6 * mouth)], BEAK2, w=5)
    d.polygon([(P(476), P(214)), (P(520), P(219 + 8 * mouth)), (P(478), P(226 + 4 * mouth))], fill=(150, 40, 40, 255))
    # barbilla roja colgando
    d.rounded_rectangle((P(456), P(212), P(482), P(292)), P(13), fill=RED, outline=OUT, width=P(5))
    # ala: apunta a la derecha y gira alrededor del hombro
    wing = Image.new("RGBA", im.size, (0, 0, 0, 0)); dw = ImageDraw.Draw(wing)
    px, py = 375, 445
    pts = [(px - 20, py - 22), (px + 45, py - 34), (px + 135, py - 16), (px + 185, py + 6), (px + 160, py + 16),
           (px + 172, py + 32), (px + 138, py + 36), (px + 144, py + 54), (px + 100, py + 48), (px + 22, py + 36), (px - 24, py + 16)]
    poly(dw, pts, BROWN2)
    for k in range(3):
        dw.line((P(px + 46 + k * 34), P(py - 6), P(px + 76 + k * 34), P(py + 26)), fill=OUT, width=P(4))
    wing = wing.rotate(wing_deg, center=(P(px), P(py)), resample=Image.BICUBIC)
    im.alpha_composite(wing)
    return im


def ease_out_back(x):
    c1, c3 = 1.70158, 2.70158; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_in(x): return x ** 3


def turkey_frame(t, show, size):
    """t = segundos desde que empieza a aparecer. Devuelve (imagen RGBA, desplazamiento 0..1 de entrada)."""
    enter, leave = 0.6, 0.5
    if t < enter: k = ease_out_back(t / enter)
    elif t > show - leave: k = 1 - ease_in((t - (show - leave)) / leave)
    else: k = 1.0
    # saludo: sube el ala y la mueve
    up = min(1.0, max(0.0, (t - 0.4) / 0.35))
    wave = 26 * math.sin(2 * math.pi * 2.0 * (t - 0.4)) if t > 0.4 else 0
    wing_deg = -35 + up * (75 + 0.8 * wave)
    # parpadeo cada ~2.6 s
    ph = (t + 0.9) % 2.6
    blink = 1 - abs(ph - 0.08) / 0.08 if ph < 0.16 else 0.0
    mouth = 0.6 + 0.4 * abs(math.sin(2 * math.pi * 1.0 * t))
    im = draw_turkey(wing_deg, max(0.0, blink), mouth)
    tilt = 3 * math.sin(2 * math.pi * 0.8 * t)
    im = im.rotate(tilt, center=(P(300), P(500)), resample=Image.BICUBIC)
    bob = 8 * math.sin(2 * math.pi * 1.5 * t)
    return im.resize((size, size), Image.LANCZOS), k, bob


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input"); ap.add_argument("--output"); ap.add_argument("--preview")
    ap.add_argument("--first", type=float, default=6); ap.add_argument("--gap", type=float, default=6)
    ap.add_argument("--show", type=float, default=8); ap.add_argument("--size", type=int, default=560)
    ap.add_argument("--y", type=int, default=1000, help="centro vertical del turkey")
    ap.add_argument("--peek", type=float, default=0.62, help="fracción del ancho del dibujo que se ve")
    ap.add_argument("--crf", default="20")
    a = ap.parse_args()
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        for t in [0.2, 0.6, 1.2, 1.5, 2.0, 3.4, 7.8]:
            im, k, bob = turkey_frame(t, a.show, a.size)
            bg = Image.new("RGBA", im.size, (250, 230, 140, 255)); bg.alpha_composite(im); bg.save(f"{a.preview}/t_{t}.png")
        return
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height,r_frame_rate:format=duration", "-of", "default=nw=1", a.input], text=True)
    info = dict(l.split("=") for l in out.strip().splitlines())
    W, H = int(info["width"]), int(info["height"]); n, dd = info["r_frame_rate"].split("/"); fps = float(n) / float(dd)
    dur = float(info["duration"])
    wins, t0, side = [], a.first, 0
    while t0 + a.show <= dur + 0.01:
        wins.append((t0, side)); t0 += a.show + a.gap; side ^= 1
    print("apariciones:", [(round(s, 1), "izq" if sd == 0 else "der") for s, sd in wins])
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.input, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
                            "-i", "-", "-i", a.input, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-preset", "slow",
                            "-crf", a.crf, "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p", "-c:a", "copy",
                            "-movflags", "+faststart", "-shortest", a.output], stdin=subprocess.PIPE)
    i, fsz = 0, W * H * 3
    while True:
        buf = dec.stdout.read(fsz)
        if len(buf) < fsz: break
        t = i / fps; i += 1
        act = [(s, sd) for s, sd in wins if s <= t < s + a.show]
        if not act: enc.stdin.write(buf); continue
        s, sd = act[0]
        im, k, bob = turkey_frame(t - s, a.show, a.size)
        if sd == 1: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        vis = a.size * a.peek
        x = int(-a.size + vis * k) if sd == 0 else int(W - vis * k)
        y = int(a.y - a.size / 2 + bob)
        fr = Image.frombuffer("RGB", (W, H), buf, "raw", "RGB", 0, 1).convert("RGBA")
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); layer.paste(im, (x, y), im)
        fr.alpha_composite(layer)
        enc.stdin.write(fr.convert("RGB").tobytes())
        if i % 300 == 0: print(f"  {t:6.1f}s", flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()
    print("Listo:", a.output)


if __name__ == "__main__":
    main()
