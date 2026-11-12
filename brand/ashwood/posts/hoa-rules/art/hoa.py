"""Backgrounds for 'Not every Poconos community has the same rules' (1080x1350).
Style: community cork bulletin board — pinned index cards, polaroid photo frames, sticky notes.
Text that changes (names, rules) is NOT baked in; it stays editable in Canva."""
import base64, io, math, random
import numpy as np
from PIL import Image, ImageFilter

W, H = 1080, 1350
FONT_DIR = 'fonts'


def font_face(name, file, weight=400):
    data = base64.b64encode(open(f'{FONT_DIR}/{file}', 'rb').read()).decode()
    return f"@font-face{{font-family:'{name}';src:url(data:font/ttf;base64,{data});font-weight:{weight};}}"


FONTS = (font_face('Caveat', 'Caveat-700.ttf', 700) + font_face('Marker', 'PermanentMarker-400.ttf')
         + font_face('Mono', 'JetBrainsMono-800.ttf', 800))


def cork(seed):
    rng = np.random.default_rng(seed)
    w, h = W * 2, H * 2
    base = np.zeros((h, w), np.float32)
    for scale, amp in [(64, 0.35), (16, 0.35), (4, 0.2), (1, 0.12)]:
        n = rng.random((h // scale + 2, w // scale + 2)).astype(np.float32)
        img = Image.fromarray((n * 255).astype(np.uint8)).resize((w + 2 * scale, h + 2 * scale), Image.BICUBIC)
        base += amp * (np.asarray(img, np.float32)[:h, :w] / 255 - 0.5)
    # granules
    spots = rng.random((h, w)) < 0.010
    dark = rng.random((h, w)) < 0.006
    c0 = np.array([186, 136, 82], np.float32)
    img = c0[None, None, :] * (1 + 0.55 * base[..., None])
    img[spots] = img[spots] * 1.18 + 10
    img[dark] = img[dark] * 0.55
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=86)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def pin(x, y, color):
    return (f'<ellipse cx="{x+5}" cy="{y+9}" rx="15" ry="9" fill="#000" opacity="0.28" filter="url(#blur3)"/>'
            f'<circle cx="{x}" cy="{y}" r="15" fill="{color}"/>'
            f'<circle cx="{x}" cy="{y}" r="15" fill="url(#pinShade)"/>'
            f'<circle cx="{x-5}" cy="{y-5}" r="4.5" fill="#fff" opacity="0.75"/>')


def tape(cx, cy, w, h, ang):
    return (f'<g transform="rotate({ang} {cx} {cy})"><rect x="{cx-w/2}" y="{cy-h/2}" width="{w}" height="{h}" '
            f'fill="#F3E9C8" opacity="0.78"/><rect x="{cx-w/2}" y="{cy-h/2}" width="{w}" height="{h}" fill="url(#tapeLines)" opacity="0.25"/></g>')


def paper(x, y, w, h, fill='#FFFDF6', lined=False, ang=0, shadow=True):
    cx, cy = x + w / 2, y + h / 2
    out = f'<g transform="rotate({ang} {cx} {cy})">'
    if shadow:
        out += f'<rect x="{x+8}" y="{y+12}" width="{w}" height="{h}" fill="#2A1A0C" opacity="0.35" filter="url(#blur8)"/>'
    out += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'
    if lined:
        for yy in range(int(y) + 70, int(y + h) - 10, 36):
            out += f'<line x1="{x}" y1="{yy}" x2="{x+w}" y2="{yy}" stroke="#BFD3E6" stroke-width="1.6" opacity="0.55"/>'
        out += f'<line x1="{x+54}" y1="{y}" x2="{x+54}" y2="{y+h}" stroke="#E7A3A3" stroke-width="2" opacity="0.7"/>'
    return out + '</g>'


def polaroid(x, y, w, h, ang=0):
    cx, cy = x + w / 2, y + h / 2
    return (f'<g transform="rotate({ang} {cx} {cy})">'
            f'<rect x="{x+8}" y="{y+12}" width="{w}" height="{h}" fill="#2A1A0C" opacity="0.38" filter="url(#blur8)"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FBFAF5"/>'
            f'<rect x="{x+20}" y="{y+20}" width="{w-40}" height="{h-85}" fill="#D9D3C7"/></g>')


def sticky(x, y, w, h, color, text, ang, size=46):
    lines = text.split('\n')
    t = ''.join(f'<tspan x="{x+w/2}" dy="{0 if i == 0 else size*1.05}">{l}</tspan>' for i, l in enumerate(lines))
    ty = y + h / 2 - (len(lines) - 1) * size * 0.52 + size * 0.32
    return (f'<g transform="rotate({ang} {x+w/2} {y+h/2})">'
            f'<rect x="{x+6}" y="{y+12}" width="{w}" height="{h}" fill="#2A1A0C" opacity="0.32" filter="url(#blur8)"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="26" fill="#000" opacity="0.05"/>'
            f'<text x="{x+w/2}" y="{ty}" text-anchor="middle" font-family="Caveat" font-weight="700" font-size="{size}" fill="#2A2A2A">{t}</text></g>')


def label(x, y, text, color, icon=''):
    return (f'<text x="{x}" y="{y}" font-family="Mono" font-weight="800" font-size="21" letter-spacing="2.2" fill="{color}">{icon}{text}</text>')


def base(inner, seed):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><style>{FONTS}</style>
<filter id="blur8" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="9"/></filter>
<filter id="blur3" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>
<radialGradient id="pinShade" cx="0.35" cy="0.3" r="0.8"><stop offset="0" stop-color="#fff" stop-opacity="0.25"/><stop offset="1" stop-color="#000" stop-opacity="0.35"/></radialGradient>
<pattern id="tapeLines" width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0,6 L6,0" stroke="#9A8A60" stroke-width="1"/></pattern>
<radialGradient id="vig" cx="0.5" cy="0.45" r="0.75"><stop offset="0.55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#1E1006" stop-opacity="0.45"/></radialGradient>
<linearGradient id="wood" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7A4E2B"/><stop offset="1" stop-color="#5C3A1F"/></linearGradient>
</defs>
<image href="{cork(seed)}" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="none"/>
<rect width="{W}" height="{H}" fill="url(#vig)"/>
<rect x="0" y="0" width="{W}" height="22" fill="url(#wood)"/><rect x="0" y="0" width="22" height="{H}" fill="url(#wood)"/><rect x="{W-22}" y="0" width="22" height="{H}" fill="url(#wood)"/>
<rect x="22" y="22" width="{W-44}" height="{H-22}" fill="none" stroke="#3A2412" stroke-width="3" opacity="0.5"/>
{inner}
</svg>'''


PINS = ['#D6402F', '#2F6FB5', '#E9B33A', '#3E9A5C', '#8E4FB0']
LABELS = [('THE HOA', '#1F3A5F'), ('AMENITIES', '#2C7A6B'), ('PARKING', '#B8651B'), ('PETS', '#7A4FA0'), ('SHORT-TERM RENTALS', '#C0392B')]
ROW_Y = [676, 782, 888, 994, 1100]


def community(seed):
    random.seed(seed)
    p = PINS[seed % 5:] + PINS[:seed % 5]
    out = paper(60, 36, 960, 148, '#FFFFFF')                          # header card (name + location editable)
    out += f'<rect x="60" y="36" width="10" height="148" fill="{p[0]}"/>'
    out += pin(92, 58, p[1]) + pin(988, 58, p[2])
    out += polaroid(60, 212, 460, 385, ang=-1.2) + polaroid(560, 212, 460, 385, ang=1.0)
    out += tape(290, 214, 150, 40, random.uniform(-6, 6)) + tape(790, 214, 150, 40, random.uniform(-6, 6))
    out += paper(60, 628, 960, 610, '#FFFDF4', lined=False)
    out += pin(96, 648, p[3]) + pin(984, 648, p[4])
    for (txt, col), y in zip(LABELS, ROW_Y):
        out += f'<rect x="100" y="{y+2}" width="8" height="24" rx="2" fill="{col}"/>'
        out += label(120, y + 22, txt, col)
        out += f'<line x1="100" y1="{y+96}" x2="980" y2="{y+96}" stroke="#E4DCCB" stroke-width="2" stroke-dasharray="2 7" stroke-linecap="round"/>' if y != ROW_Y[-1] else ''
    return base(out, seed)


def cover():
    out = sticky(58, 70, 300, 210, '#FFE66B', 'Can I\nAirbnb it?', -6)
    out += sticky(720, 60, 300, 210, '#FF9FBF', 'Are dogs\nallowed?', 5)
    out += paper(110, 310, 860, 720, '#FFFDF4')
    out += pin(150, 334, '#D6402F') + pin(930, 334, '#2F6FB5')
    # stamp
    out += ('<g transform="rotate(-8 790 950)" opacity="0.85"><rect x="640" y="905" width="300" height="88" rx="10" fill="none" stroke="#C0392B" stroke-width="6"/>'
            '<text x="790" y="964" text-anchor="middle" font-family="Marker" font-size="38" fill="#C0392B">READ FIRST</text></g>')
    out += sticky(70, 1060, 300, 180, '#9FD6FF', 'Street\nparking?', 4, 44)
    out += sticky(700, 1060, 310, 180, '#B8F0A8', 'Lake\naccess?', -5, 44)
    out += sticky(395, 1080, 290, 160, '#FFC48A', 'Gas boats?', 2, 44)
    return base(out, 11)


def cta():
    out = paper(90, 120, 900, 900, '#FFFDF4')
    out += pin(130, 146, '#3E9A5C') + pin(950, 146, '#D6402F')
    out += sticky(70, 1050, 300, 190, '#FFE66B', 'Ask before\nyou buy!', -5, 44)
    out += sticky(710, 1050, 300, 190, '#FF9FBF', 'Rules\nchange!', 4, 44)
    return base(out, 17)


def placeholder(fn, hint):
    w, h = 840, 600  # 2x of 420x300
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs><style>{FONTS}</style></defs>
<rect width="{w}" height="{h}" fill="#E7E1D5"/>
<rect x="18" y="18" width="{w-36}" height="{h-36}" fill="none" stroke="#9E937E" stroke-width="5" stroke-dasharray="22 14" rx="10"/>
<g transform="translate({w/2-60},170)"><rect x="0" y="24" width="120" height="86" rx="14" fill="none" stroke="#7A6F5C" stroke-width="7"/>
<path d="M36,24 L46,6 H74 L84,24" fill="none" stroke="#7A6F5C" stroke-width="7" stroke-linejoin="round"/><circle cx="60" cy="67" r="24" fill="none" stroke="#7A6F5C" stroke-width="7"/></g>
<text x="{w/2}" y="360" text-anchor="middle" font-family="Mono" font-weight="800" font-size="40" letter-spacing="4" fill="#5E5442">ADD HOA PHOTO</text>
<text x="{w/2}" y="420" text-anchor="middle" font-family="Caveat" font-weight="700" font-size="52" fill="#5E5442">{hint}</text>
<text x="{w/2}" y="500" text-anchor="middle" font-family="Mono" font-weight="800" font-size="22" fill="#8A7F6A">Drag a photo onto this box to replace it</text></svg>'''
    open(fn, 'w').write(svg)


if __name__ == '__main__':
    open('hoa-cover.svg', 'w').write(cover())
    for i in range(5):
        open(f'hoa-c{i+1}.svg', 'w').write(community(i + 1))
    open('hoa-cta.svg', 'w').write(cta())
    placeholder('ph-hoa-1.svg', 'the lake, beach or pool')
    placeholder('ph-hoa-2.svg', 'the entrance or clubhouse')
    print('ok')
