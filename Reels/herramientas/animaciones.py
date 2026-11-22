#!/usr/bin/env python3
"""Animaciones explicativas (overlay encima del video, debajo de la cara y arriba de los subtítulos).

Uso:
  python3 animaciones.py --scene roof --seconds 4.2 --out carpeta_pngs
  python3 animaciones.py --scene disagree --seconds 5.6 --out carpeta_pngs
Genera PNG con transparencia (panel de 940x330) a 30 fps. Luego se ponen sobre el video con ffmpeg overlay.

Colores claros sobre panel oscuro semitransparente: se lee bien sobre ropa oscura o fondos oscuros.
"""
import argparse, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PW, PH, S = 940, 330, 2           # tamaño del panel y supersampling
CREAM, GOLD, BLUE = (245, 240, 230), (232, 176, 75), (142, 201, 255)
RED, GREEN, GREY = (255, 138, 128), (124, 227, 161), (190, 196, 205)
FONT_B = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_M = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"


def font(path, size): return ImageFont.truetype(path, int(size * S))
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def ease(x): return 1 - (1 - x) ** 3
def back(x):  # entrada con pequeño rebote
    c1, c3 = 1.70158, 2.70158; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def P(x): return int(x * S)


def panel(alpha):
    im = Image.new("RGBA", (PW * S, PH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, PW * S - 1, PH * S - 1), P(34), fill=(12, 16, 26, int(150 * alpha)),
                        outline=(255, 255, 255, int(40 * alpha)), width=P(2))
    return im


def layer(): return Image.new("RGBA", (PW * S, PH * S), (0, 0, 0, 0))


def put(base, lay, a):
    if a <= 0: return
    if a < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
    base.alpha_composite(lay)


def text(d, xy, s, f, fill, anchor="mm"):
    d.text((P(xy[0]), P(xy[1])), s, font=f, fill=fill, anchor=anchor)


def pop_scale(lay, sc, cx, cy):
    """Escala una capa alrededor de (cx, cy) para efecto pop."""
    if abs(sc - 1) < 1e-3: return lay
    w, h = lay.size; nw, nh = max(1, int(w * sc)), max(1, int(h * sc))
    r = lay.resize((nw, nh), Image.BICUBIC); out = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    ox, oy = int(P(cx) * (1 - sc)), int(P(cy) * (1 - sc))
    out.paste(r, (ox, oy), r); return out


# ---------- dibujos ----------
def house(d, cx, cy, col, crack=0.0):
    w, h = 150, 110
    d.rectangle((P(cx - w / 2), P(cy - h / 2 + 30), P(cx + w / 2), P(cy + h / 2 + 30)), outline=col, width=P(6))
    d.polygon([(P(cx - w / 2 - 22), P(cy - h / 2 + 32)), (P(cx), P(cy - h / 2 - 50)), (P(cx + w / 2 + 22), P(cy - h / 2 + 32))],
              outline=col, width=P(6))
    d.rectangle((P(cx - 18), P(cy + 30), P(cx + 18), P(cy + h / 2 + 30)), outline=col, width=P(5))
    if crack > 0:  # grieta en el techo
        pts = [(cx + 30, cy - 52), (cx + 40, cy - 40), (cx + 32, cy - 30), (cx + 44, cy - 18)]
        n = max(2, int(len(pts) * crack + 0.999))
        d.line([(P(x), P(y)) for x, y in pts[:n]], fill=GOLD, width=P(5))


def cloud(d, cx, cy, col):
    for dx, dy, r in [(-38, 6, 26), (-8, -10, 34), (28, 0, 28), (52, 10, 20)]:
        d.ellipse((P(cx + dx - r), P(cy + dy - r), P(cx + dx + r), P(cy + dy + r)), fill=col)


def drop(d, x, y, col, s=1.0):
    d.ellipse((P(x - 7 * s), P(y - 4 * s), P(x + 7 * s), P(y + 12 * s)), fill=col)
    d.polygon([(P(x - 6 * s), P(y + 1 * s)), (P(x), P(y - 12 * s)), (P(x + 6 * s), P(y + 1 * s))], fill=col)


def person_layer(col, nose=True):
    """Silueta de busto mirando a la derecha (para girarla se refleja)."""
    w, h = 200, 260
    im = Image.new("RGBA", (P(w), P(h)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = w / 2
    d.ellipse((P(cx - 38), P(40), P(cx + 38), P(116)), fill=col)                          # cabeza
    if nose: d.polygon([(P(cx + 34), P(70)), (P(cx + 50), P(86)), (P(cx + 34), P(94))], fill=col)  # nariz
    d.rounded_rectangle((P(cx - 70), P(128), P(cx + 70), P(258)), P(60), fill=col)      # hombros/cuerpo
    d.rectangle((P(cx - 70), P(200), P(cx + 70), P(260)), fill=col)
    return im


def place_person(base, pl, cx, bottom, facing):
    """facing: 1 = mira a la derecha, -1 = izquierda, valores intermedios = girando."""
    w, h = pl.size; f = abs(facing)
    if f < 0.04: return
    img = pl if facing > 0 else pl.transpose(Image.FLIP_LEFT_RIGHT)
    img = img.resize((max(1, int(w * f)), h), Image.BICUBIC)
    base.alpha_composite(img, (int(P(cx) - img.size[0] / 2), int(P(bottom) - h)))


def bubble(d, cx, cy, s, f, col, tail="left"):
    tw = f.getlength(s) / S; w, h = tw + 44, 58
    d.rounded_rectangle((P(cx - w / 2), P(cy - h / 2), P(cx + w / 2), P(cy + h / 2)), P(24), fill=col)
    tx = cx - w / 2 + 26 if tail == "left" else cx + w / 2 - 26
    d.polygon([(P(tx - 10), P(cy + h / 2 - 2)), (P(tx + 10), P(cy + h / 2 - 2)), (P(tx - (14 if tail == "left" else -14)), P(cy + h / 2 + 18))], fill=col)
    text(d, (cx, cy + 1), s, f, (20, 24, 32, 255))


def money_bag(d, cx, cy, col, f):
    d.ellipse((P(cx - 36), P(cy - 22), P(cx + 36), P(cy + 42)), fill=col)
    d.polygon([(P(cx - 16), P(cy - 20)), (P(cx - 24), P(cy - 44)), (P(cx + 24), P(cy - 44)), (P(cx + 16), P(cy - 20))], fill=col)
    d.line((P(cx - 18), P(cy - 22), P(cx + 18), P(cy - 22)), fill=(20, 24, 32, 255), width=P(4))
    text(d, (cx, cy + 12), "$", f, (20, 24, 32, 255))


def check(d, cx, cy, r, col):
    d.ellipse((P(cx - r), P(cy - r), P(cx + r), P(cy + r)), fill=col)
    d.line([(P(cx - r * 0.45), P(cy)), (P(cx - r * 0.1), P(cy + r * 0.38)), (P(cx + r * 0.5), P(cy - r * 0.35))],
           fill=(20, 24, 32, 255), width=P(max(3, r * 0.22)), joint="curve")


def cross(d, cx, cy, r, col):
    d.ellipse((P(cx - r), P(cy - r), P(cx + r), P(cy + r)), fill=col)
    k = r * 0.42
    d.line((P(cx - k), P(cy - k), P(cx + k), P(cy + k)), fill=(20, 24, 32, 255), width=P(r * 0.22))
    d.line((P(cx - k), P(cy + k), P(cx + k), P(cy - k)), fill=(20, 24, 32, 255), width=P(r * 0.22))


# ---------- escena 1: "has the roof ever leaked?" -> el vendedor debe decirlo ----------
def scene_roof(t, T):
    a_in, a_out = ease(prog(t, 0, 0.3)), 1 - ease(prog(t, T - 0.3, T))
    A = a_in * a_out
    base = panel(A)
    fT, fS = font(FONT_B, 30), font(FONT_M, 24)
    # casa + nube + lluvia
    L = layer(); d = ImageDraw.Draw(L)
    hx, hy = 210, 190
    house(d, hx, hy, CREAM + (255,), crack=prog(t, 0.9, 1.3))
    cloud(d, hx - 10, 62, GREY + (255,))
    if t > 0.6:
        for k in range(6):  # gotas que caen sobre el techo
            ph = ((t - 0.6) * 1.6 + k / 6) % 1.0
            x = hx - 70 + k * 26; y = 80 + ph * 50
            if y < 128 + abs(x - hx) * 0.55: drop(d, x, y, BLUE + (255,), 0.8)
    if t > 1.2:  # gota que entra por la grieta y charco adentro
        ph = ((t - 1.2) * 1.2) % 1.0
        drop(d, hx + 40, 160 + ph * 70, BLUE + (255,), 1.0)
        pw = 18 + 26 * ease(prog(t, 1.3, 2.4))
        d.ellipse((P(hx + 40 - pw), P(268), P(hx + 40 + pw), P(280)), fill=BLUE + (230,))
    put(base, L, A * ease(prog(t, 0.15, 0.6)))
    # pregunta
    Q = layer(); dq = ImageDraw.Draw(Q); text(dq, (520, 36), "Has the roof ever leaked?", font(FONT_B, 30), CREAM + (255,))
    put(base, pop_scale(Q, 0.85 + 0.15 * back(prog(t, 0.35, 0.75)), 520, 36), A * prog(t, 0.35, 0.6) * (1 - prog(t, 2.2, 2.45)))
    # flecha
    ar = ease(prog(t, 1.9, 2.3))
    if ar > 0:
        Ar = layer(); da = ImageDraw.Draw(Ar); x0, x1, y = 350, 350 + 110 * ar, 180
        da.line((P(x0), P(y), P(x1), P(y)), fill=GOLD + (255,), width=P(6))
        if ar > 0.95: da.polygon([(P(x1 + 4), P(y)), (P(x1 - 16), P(y - 13)), (P(x1 - 16), P(y + 13))], fill=GOLD + (255,))
        put(base, Ar, A)
    # vendedor + globo
    sp = prog(t, 2.2, 2.6)
    if sp > 0:
        Pl = layer(); place_person(Pl, person_layer(GOLD + (255,)), 560, 300, -1)
        put(base, Pl, A * ease(sp))
        text(ImageDraw.Draw(base), (560, 316), "SELLER", font(FONT_B, 20), GOLD + (int(255 * A * ease(sp)),))
    bp = prog(t, 2.45, 2.8)
    if bp > 0:
        B = layer(); bubble(ImageDraw.Draw(B), 640, 48, "Yes, it leaked.", fS, CREAM + (255,), tail="left")
        put(base, pop_scale(B, 0.7 + 0.3 * back(bp), 600, 78), A * ease(bp))
    # documento de disclosure con check
    dp = prog(t, 2.9, 3.3)
    if dp > 0:
        D = layer(); dd = ImageDraw.Draw(D); x0, y0 = 700, 120
        dd.rounded_rectangle((P(x0), P(y0), P(x0 + 170), P(y0 + 180)), P(14), fill=CREAM + (255,))
        text(dd, (x0 + 85, y0 + 26), "DISCLOSURE", font(FONT_B, 20), (20, 24, 32, 255))
        for k in range(3):
            dd.line((P(x0 + 22), P(y0 + 62 + k * 30), P(x0 + 148), P(y0 + 62 + k * 30)), fill=(150, 156, 166, 255), width=P(5))
        put(base, pop_scale(D, 0.7 + 0.3 * back(dp), x0 + 85, y0 + 90), A * ease(dp))
        cp = prog(t, 3.2, 3.5)
        if cp > 0:
            C = layer(); check(ImageDraw.Draw(C), x0 + 160, y0 + 168, 28, GREEN + (255,))
            put(base, pop_scale(C, 0.5 + 0.5 * back(cp), x0 + 160, y0 + 168), A * ease(cp))
    return base


# ---------- escena 2: comprador y vendedor no se ponen de acuerdo ----------
def scene_disagree(t, T):
    a_in, a_out = ease(prog(t, 0, 0.3)), 1 - ease(prog(t, T - 0.35, T))
    A = a_in * a_out
    base = panel(A)
    fS, fL = font(FONT_B, 26), font(FONT_B, 20)
    bx, sx, bottom = 230, 710, 292
    # giro: de mirarse (buyer -> derecha, seller -> izquierda) a darse la espalda
    tp = ease(prog(t, 2.1, 2.6))
    f_b = math.cos(tp * math.pi)          # 1 -> -1
    f_s = -math.cos(tp * math.pi)         # -1 -> 1
    lean = 6 * math.sin(t * 9) if t < 2.1 else 0  # se inclinan al discutir
    L = layer()
    place_person(L, person_layer(BLUE + (255,)), bx + lean, bottom, f_b)
    place_person(L, person_layer(GOLD + (255,)), sx - lean, bottom, f_s)
    put(base, L, A * ease(prog(t, 0.1, 0.45)))
    dl = ImageDraw.Draw(base)
    text(dl, (bx, 312), "BUYER", fL, BLUE + (int(255 * A),))
    text(dl, (sx, 312), "SELLER", fL, GOLD + (int(255 * A),))
    # discusión: globos alternados
    lines = [(0.45, "buyer", "Fix the roof!"), (0.95, "seller", "No way!"), (1.45, "buyer", "Lower the price!"), (1.85, "seller", "No!")]
    for k, (st, who, s) in enumerate(lines):
        en = lines[k + 1][0] + 0.25 if k + 1 < len(lines) else 2.15
        p_in, p_out = prog(t, st, st + 0.25), 1 - prog(t, en, en + 0.15)
        a = ease(p_in) * p_out
        if a <= 0: continue
        B = layer(); cx = bx + 120 if who == "buyer" else sx - 120
        bubble(ImageDraw.Draw(B), cx, 60, s, fS, CREAM + (255,), tail="left" if who == "buyer" else "right")
        put(base, pop_scale(B, 0.7 + 0.3 * back(p_in), cx, 80), A * a)
    # chispa entre los dos
    zp = prog(t, 1.1, 2.1)
    if 0 < zp < 1:
        Z = layer(); dz = ImageDraw.Draw(Z); cx, cy = (bx + sx) / 2, 170
        j = 6 * math.sin(t * 40)
        pts = [(cx - 40, cy - 40 + j), (cx + 4, cy - 6), (cx - 10, cy + 2), (cx + 36, cy + 42 - j)]
        dz.line([(P(x), P(y)) for x, y in pts], fill=RED + (255,), width=P(8), joint="curve")
        put(base, Z, A * (1 - prog(t, 1.95, 2.1)))
    # "No agreement"
    np_ = prog(t, 2.5, 2.85)
    if np_ > 0:
        N = layer(); dn = ImageDraw.Draw(N); cx, cy = (bx + sx) / 2, 92
        cross(dn, cx - 118, cy, 24, RED + (255,))
        text(dn, (cx + 22, cy), "No agreement", fS, RED + (255,))
        put(base, pop_scale(N, 0.7 + 0.3 * back(np_), cx, cy), A * ease(np_) * (1 - prog(t, 3.3, 3.5)))
    # earnest money vuelve al comprador
    mp = prog(t, 3.3, 4.3)
    if mp > 0:
        M = layer(); dm = ImageDraw.Draw(M)
        x0, y0, x1, y1 = (bx + sx) / 2, 190, bx + 105, 205
        e = ease(mp); x = x0 + (x1 - x0) * e; y = y0 + (y1 - y0) * e - 70 * math.sin(math.pi * e)
        money_bag(dm, x, y, GREEN + (255,), font(FONT_B, 34))
        put(base, M, A * ease(prog(t, 3.3, 3.5)))
        lp = prog(t, 3.5, 3.85)
        if lp > 0:
            Lb = layer(); text(ImageDraw.Draw(Lb), ((bx + sx) / 2, 92), "Earnest money back", fS, GREEN + (255,))
            put(base, pop_scale(Lb, 0.8 + 0.2 * back(lp), (bx + sx) / 2, 92), A * ease(lp))
    return base


SCENES = {"roof": scene_roof, "disagree": scene_disagree}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True, choices=SCENES)
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    n = int(round(a.seconds * a.fps))
    for i in range(n):
        im = SCENES[a.scene](i / a.fps, a.seconds).resize((PW, PH), Image.LANCZOS)
        im.save(os.path.join(a.out, f"{i:04d}.png"))
    print(f"{n} cuadros -> {a.out}")


if __name__ == "__main__":
    main()
