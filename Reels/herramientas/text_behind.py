#!/usr/bin/env python3
"""Texto detrás de la persona (estilos 2, 4 y 5 de marca/estilos-edicion.md).

Uso:
  python3 text_behind.py --input v1_corte.mp4 --spec capas.json --output v3_texto.mp4 \
      [--ass-in subs.ass --ass-out subs_final.ass]

capas.json:
{
  "fonts":  {"heavy": "/ruta/Inter-Black.otf", "serif": "/ruta/Playfair-Italic.ttf"},   (opcional)
  "max_width": 960,
  "overlays": [
    {"style": "hook", "start": 0.0, "end": 3.0, "y": 560, "hide_captions": false,
     "lines": [{"t": "Fire your", "font": "serif", "color": "#B8862E", "size": 150},
               {"t": "REALTOR",   "font": "heavy", "color": "#161616", "fit": true, "max_size": 330}]}
  ]
}
- "y" = centro vertical del bloque de texto (en un cuadro de 1080x1920). Ponlo a la altura de la cabeza
  para que la cabeza tape parte del texto.
- "fit": la línea se agranda hasta ocupar max_width (con tope max_size).
- "hide_captions": true quita los subtítulos mientras dura la capa (estilo 2: el texto grande ya es lo que dice).
La persona se recorta en cada cuadro con MODNet (matte.py) y se pone encima del texto.
"""
import argparse, json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from matte import Matter  # noqa: E402

REELS = os.path.dirname(HERE)
DEFAULT_FONTS = {
    "heavy": "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    "bold": "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
    "serif": os.path.join(REELS, "marca/fuentes/PlayfairDisplay-ExtraBoldItalic.ttf"),
    "serif_light": os.path.join(REELS, "marca/fuentes/PlayfairDisplay-SemiBoldItalic.ttf"),
}
IN_D, OUT_D, STAGGER = 0.30, 0.22, 0.07


def hex2rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def render_line(line, fonts, max_w):
    path = fonts[line.get("font", "heavy")]
    size = int(line.get("size", 120))
    if line.get("fit"):
        size = int(line.get("max_size", 340))
        while size > 40:
            f = ImageFont.truetype(path, size)
            if f.getbbox(line["t"])[2] - f.getbbox(line["t"])[0] <= max_w: break
            size -= 4
    f = ImageFont.truetype(path, size)
    x0, y0, x1, y1 = f.getbbox(line["t"])
    pad = 40
    img = Image.new("RGBA", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((pad - x0, pad - y0), line["t"], font=f, fill=hex2rgb(line["color"]) + (255,))
    # sombra suave para que se lea sobre fondos claros
    sh_op = line.get("shadow", 0.28)
    if sh_op > 0:
        a = img.split()[3].filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * sh_op))
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.putalpha(a)
        base = Image.new("RGBA", img.size, (0, 0, 0, 0)); base.alpha_composite(sh, (0, 6))
        base.alpha_composite(img); img = base
    return img, pad


def render_image(item, base_dir):
    """Foto como tarjeta (estilos 1 y 3): esquinas redondeadas, borde blanco opcional y sombra suave."""
    path = item["image"] if os.path.isabs(item["image"]) else os.path.join(base_dir, item["image"])
    im = Image.open(path).convert("RGB")
    w = int(item.get("width", 820)); h = int(im.size[1] * w / im.size[0])
    if item.get("height"):  # recorte centrado a una altura fija
        h = int(item["height"]); s = max(w / im.size[0], h / im.size[1])
        im = im.resize((int(im.size[0] * s) + 1, int(im.size[1] * s) + 1), Image.LANCZOS)
        l, t = (im.size[0] - w) // 2, (im.size[1] - h) // 2; im = im.crop((l, t, l + w, t + h))
    else:
        im = im.resize((w, h), Image.LANCZOS)
    b, r, pad = int(item.get("border", 10)), int(item.get("radius", 28)), 50
    card = Image.new("RGBA", (w + 2 * b, h + 2 * b), (255, 255, 255, 255))
    card.paste(im, (b, b))
    mask = Image.new("L", card.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, *card.size), r, fill=255)
    card.putalpha(mask)
    out = Image.new("RGBA", (card.size[0] + 2 * pad, card.size[1] + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sh.putalpha(Image.new("L", out.size, 0)); sa = sh.split()[3]
    sa.paste(mask.point(lambda v: int(v * item.get("shadow", 0.35))), (pad, pad + 10))
    sh.putalpha(sa.filter(ImageFilter.GaussianBlur(18)))
    out.alpha_composite(sh); out.alpha_composite(card, (pad, pad))
    if item.get("rotate"): out = out.rotate(item["rotate"], resample=Image.BICUBIC, expand=True)
    return out, pad


def build(ov, fonts, max_w, head_top=None, base_dir="."):
    imgs = [render_image(l, base_dir) if "image" in l else render_line(l, fonts, max_w) for l in ov["lines"]]
    gap = ov.get("gap", -50)  # negativo: líneas pegadas, estilo editorial
    heights = [im.size[1] + (gap if i < len(imgs) - 1 else 0) for i, (im, _) in enumerate(imgs)]
    total = sum(heights)
    if ov.get("y", "auto") == "auto" and head_top is not None:
        # la cabeza tapa solo la parte de abajo del bloque ("overlap" px, contando el margen de la última línea)
        last_pad = imgs[-1][1]
        bottom = head_top + ov.get("overlap", 110) + last_pad
        top = max(ov.get("min_top", 200), bottom - total)
    else:
        y = ov.get("y", 560)
        top = (y if isinstance(y, (int, float)) else 560) - total / 2
    placed = []
    for (im, pad), h in zip(imgs, heights):
        placed.append((im, top)); top += h
    return placed


def ease_out(x): return 1 - (1 - x) ** 3


def frame_layer(ov, placed, t, W, H):
    s, e = ov["start"], ov["end"]
    if t < s or t > e: return None
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0)); any_ = False
    for i, (im, top) in enumerate(placed):
        ls = s + i * STAGGER
        if t < ls: continue
        k_in = min(1.0, (t - ls) / IN_D); k_out = min(1.0, max(0.0, (e - t) / OUT_D))
        a = ease_out(k_in) * k_out
        if a <= 0.01: continue
        scale = (0.90 + 0.10 * ease_out(k_in)) * (1.0 + 0.04 * (1 - k_out))
        dy = 40 * (1 - ease_out(k_in))
        w, h = im.size; nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        li = im.resize((nw, nh), Image.BILINEAR) if scale != 1 else im.copy()
        if a < 1: li.putalpha(li.split()[3].point(lambda v: int(v * a)))
        cx, cy = W / 2, top + h / 2 + dy
        canvas.alpha_composite(li, (int(cx - nw / 2), int(cy - nh / 2))); any_ = True
    return canvas if any_ else None


def probe(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height,r_frame_rate", "-of", "csv=p=0", path], text=True).strip()
    w, h, r = out.split(","); n, d = r.split("/")
    return int(w), int(h), float(n) / float(d)


def head_top(path, start, end, matter, samples=5):
    """Punto más alto de la persona (y en px) durante la capa: usa el más alto de varios cuadros."""
    W, H, _ = probe(path); tops = []
    for k in range(samples):
        t = start + (end - start) * (k + 0.5) / samples
        raw = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                                       "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
        if len(raw) < W * H * 3: continue
        m = matter(np.frombuffer(raw, np.uint8).reshape(H, W, 3))
        rows = np.where((m > 0.5).sum(1) > W * 0.03)[0]
        if len(rows): tops.append(int(rows[0]))
    return min(tops) if tops else None


def filter_ass(src, dst, windows):
    def ts(x):
        h, m, s = x.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)
    keep = []
    for line in open(src, encoding="utf-8"):
        if line.startswith("Dialogue:"):
            p = line.split(",", 3); a, b = ts(p[1]), ts(p[2]); mid = (a + b) / 2
            if any(ws <= mid <= we for ws, we in windows): continue
        keep.append(line)
    open(dst, "w", encoding="utf-8").writelines(keep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True); ap.add_argument("--spec", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--ass-in"); ap.add_argument("--ass-out")
    ap.add_argument("--crf", default="17")
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    fonts = dict(DEFAULT_FONTS, **spec.get("fonts", {}))
    W, H, fps = probe(a.input)
    max_w = spec.get("max_width", 960)
    matter = Matter()
    ovs = []
    for ov in spec["overlays"]:
        ht = head_top(a.input, ov["start"], ov["end"], matter) if ov.get("y", "auto") == "auto" else None
        if ht is not None: print(f"  capa {ov['start']:.2f}s: cabeza en y={ht}")
        ovs.append((ov, build(ov, fonts, max_w, ht, os.path.dirname(os.path.abspath(a.spec)))))

    if a.ass_in and a.ass_out:
        filter_ass(a.ass_in, a.ass_out, [(o["start"], o["end"]) for o in spec["overlays"] if o.get("hide_captions")])
        print("Subtítulos filtrados:", a.ass_out)

    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.input, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(fps), "-i", "-", "-i", a.input, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264",
                            "-crf", a.crf, "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest",
                            a.output], stdin=subprocess.PIPE)
    prev = None; i = 0; fsz = W * H * 3
    while True:
        buf = dec.stdout.read(fsz)
        if len(buf) < fsz: break
        t = i / fps; i += 1
        frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        layers = [l for l in (frame_layer(o, p, t, W, H) for o, p in ovs) if l is not None]
        if not layers:
            prev = None; enc.stdin.write(buf); continue
        m = matter(frame)
        if prev is not None and prev.shape == m.shape: m = 0.65 * m + 0.35 * prev  # menos parpadeo
        prev = m
        text = layers[0]
        for l in layers[1:]: text.alpha_composite(l)
        tx = np.asarray(text, np.float32)
        at = (tx[..., 3:4] / 255.0) * (1.0 - m[..., None])
        out = frame.astype(np.float32) * (1 - at) + tx[..., :3] * at
        enc.stdin.write(out.clip(0, 255).astype(np.uint8).tobytes())
        if i % 60 == 0: print(f"  {t:5.1f}s", flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()
    print("Listo:", a.output)


if __name__ == "__main__":
    main()
