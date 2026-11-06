"""Weekend in the Poconos: time-of-day gradient backgrounds + photo placeholders."""
import random, math
W, H = 1080, 1350
DEFS = ('<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="7"/>'
        '<feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.06 0"/></filter>'
        '<filter id="shadow" x="-10%" y="-10%" width="120%" height="120%"><feDropShadow dx="0" dy="14" stdDeviation="18" flood-color="#000" flood-opacity="0.35"/></filter>'
        '<filter id="glow"><feGaussianBlur stdDeviation="30"/></filter>')

def grad(stops):
    s = '<linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
    for off, c in stops: s += f'<stop offset="{off}" stop-color="{c}"/>'
    return s + '</linearGradient>'

def stars(n, ymax, seed, big=False):
    r = random.Random(seed); s = ''
    for _ in range(n):
        x, y = r.uniform(30, W-30), r.uniform(20, ymax)
        rad = r.choice([1, 1.2, 1.5, 2, 2.4] if big else [1, 1.2, 1.6])
        s += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rad}" fill="#fff" opacity="{r.uniform(.35,.95):.2f}"/>'
    return s

def ridge(y, amp, col, seed, op=1):
    r = random.Random(seed); pts = []; x = -20
    while x < W + 40:
        pts.append((x, y - r.uniform(0, amp))); x += r.uniform(60, 140)
    d = f'M-20,{H} ' + ' '.join(f'L{px:.0f},{py:.0f}' for px, py in pts) + f' L{W+40},{H} Z'
    return f'<path d="{d}" fill="{col}" opacity="{op}"/>'

def pines(y, col, seed, n=26):
    r = random.Random(seed); s = ''
    for _ in range(n):
        x = r.uniform(-20, W+20); h = r.uniform(70, 150); w = h * 0.42
        s += f'<path d="M{x:.0f},{y-h:.0f} L{x+w/2:.0f},{y:.0f} L{x-w/2:.0f},{y:.0f} Z" fill="{col}"/>'
    return s

def clouds(seed, ymax, col='#fff', op=0.18):
    r = random.Random(seed); s = f'<g opacity="{op}" filter="url(#glow)">'
    for _ in range(5):
        x, y = r.uniform(0, W), r.uniform(40, ymax)
        s += f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r.uniform(140,260):.0f}" ry="{r.uniform(30,55):.0f}" fill="{col}"/>'
    return s + '</g>'

def frame(y, h):
    # white print border + shadow behind the photo area (photo sits at x80..1000)
    return (f'<rect x="74" y="{y-6}" width="932" height="{h+12}" rx="4" fill="none" stroke="#000" stroke-opacity="0.25" stroke-width="12" filter="url(#shadow)"/>'
            f'<rect x="74" y="{y-6}" width="932" height="{h+12}" rx="4" fill="none" stroke="#FFFFFF" stroke-width="12"/>')

def timeline(active):
    xs = [240 + i * 150 for i in range(5)]
    s = f'<line x1="{xs[0]}" y1="1222" x2="{xs[-1]}" y2="1222" stroke="#FFFFFF" stroke-opacity="0.35" stroke-width="3"/>'
    if active is not None and active > 0:
        s += f'<line x1="{xs[0]}" y1="1222" x2="{xs[active]}" y2="1222" stroke="#FFFFFF" stroke-width="3"/>'
    for i, x in enumerate(xs):
        if active is None or i > active:
            s += f'<circle cx="{x}" cy="1222" r="7" fill="none" stroke="#FFFFFF" stroke-opacity="0.6" stroke-width="2.5"/>'
        elif i == active:
            s += f'<circle cx="{x}" cy="1222" r="14" fill="#FFFFFF" opacity="0.25"/><circle cx="{x}" cy="1222" r="9" fill="#FFFFFF"/>'
        else:
            s += f'<circle cx="{x}" cy="1222" r="7" fill="#FFFFFF"/>'
    return s

def svg(w, h, body, defs=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{DEFS}{defs}</defs>{body}</svg>'

def slide(name, stops, sky, back, front, photo_y, photo_h, active):
    body = f'<rect width="{W}" height="{H}" fill="url(#g)"/>' + sky
    body += ridge(1150, 120, back, 3, 0.85) + ridge(1185, 70, front, 9) + pines(1235, front, 21)
    body += f'<rect x="0" y="1180" width="{W}" height="{H-1180}" fill="{front}"/>'
    body += frame(photo_y, photo_h) + (timeline(active) if active != 'none' else '')
    body += f'<rect width="{W}" height="{H}" filter="url(#grain)"/>'
    open(f'{name}.svg', 'w').write(svg(W, H, body, grad(stops)))

moon = lambda x, y, r: (f'<circle cx="{x}" cy="{y}" r="{r*2.2}" fill="#FFF6D8" opacity="0.10" filter="url(#glow)"/>'
                        f'<circle cx="{x}" cy="{y}" r="{r}" fill="#FFF6D8"/><circle cx="{x+r*0.45}" cy="{y-r*0.25}" r="{r*0.9}" fill="#1D1947"/>')
sun = lambda x, y, r, c: f'<circle cx="{x}" cy="{y}" r="{r*2.4}" fill="{c}" opacity="0.35" filter="url(#glow)"/><circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>'

# photo areas: cover 500..1140 (640), moments 385..1085 (700), cta 400..830 (430)
slide('wk-cover', [(0, '#2B1B4A'), (0.45, '#7A2E5C'), (0.8, '#E0644A'), (1, '#F4A25A')],
      stars(40, 380, 1) + sun(150, 150, 55, '#FFC27A'), '#5A2346', '#1A0F24', 500, 640, 'none')
slide('wk-1', [(0, '#16143D'), (0.5, '#3F2770'), (1, '#C2577A')],
      stars(70, 420, 2) + moon(900, 150, 46), '#3A1F5C', '#120C26', 385, 700, 0)
slide('wk-2', [(0, '#17507F'), (0.55, '#3A8BCB'), (1, '#9BD0EE')],
      clouds(4, 420) + sun(900, 140, 60, '#FFE29A'), '#1E5E4A', '#0D2A20', 385, 700, 1)
slide('wk-3', [(0, '#0C5A5C'), (0.55, '#1E9488'), (1, '#8ED3B6')],
      clouds(8, 380, op=0.14) + sun(170, 130, 55, '#FFF1B0'), '#145247', '#0A2622', 385, 700, 2)
slide('wk-4', [(0, '#03081C'), (0.6, '#0C1838'), (1, '#1E2C5E')],
      stars(160, 1050, 5, big=True) + moon(880, 160, 50).replace('#1D1947', '#050B21'), '#141F45', '#04081A', 385, 700, 3)
slide('wk-5', [(0, '#6E2C0E'), (0.5, '#C2602B'), (1, '#F2A64E')],
      sun(830, 150, 70, '#FFD58A'), '#6B3216', '#2A1208', 385, 700, 4)
slide('wk-cta', [(0, '#2E1747'), (0.5, '#A8445B'), (1, '#F08A4B')],
      stars(45, 330, 6) + sun(540, 1080, 120, '#FFC27A'), '#5C2448', '#1A0D22', 400, 430, 4)

def placeholder(name, w, h, hint):
    body = (f'<rect x="0" y="0" width="{w}" height="{h}" fill="#FFFFFF" fill-opacity="0.16"/>'
            f'<rect x="18" y="18" width="{w-36}" height="{h-36}" fill="none" stroke="#FFFFFF" stroke-opacity="0.7" stroke-width="3" stroke-dasharray="14 10" rx="10"/>')
    cx, cy = w / 2, h / 2 - 70
    body += (f'<g transform="translate({cx-48},{cy-36})" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linejoin="round">'
             f'<rect x="0" y="14" width="96" height="62" rx="10"/><path d="M28,14 L36,0 L60,0 L68,14"/><circle cx="48" cy="45" r="18"/></g>')
    body += (f'<text x="{cx}" y="{cy+95}" text-anchor="middle" font-family="Inter" font-weight="800" font-size="34" letter-spacing="3" fill="#FFFFFF">ADD YOUR PHOTO</text>'
             f'<text x="{cx}" y="{cy+145}" text-anchor="middle" font-family="Inter" font-weight="500" font-size="30" fill="#FFFFFF" fill-opacity="0.9">{hint}</text>'
             f'<text x="{cx}" y="{cy+190}" text-anchor="middle" font-family="Inter" font-weight="400" font-size="22" fill="#FFFFFF" fill-opacity="0.7">Drag a photo onto this box to replace it</text>')
    open(f'{name}.svg', 'w').write(svg(w, h, body))

placeholder('ph-cover', 920, 640, 'Idea: lake or mountain view at sunset')
placeholder('ph-1', 920, 700, 'Idea: fire pit + string lights at dusk')
placeholder('ph-2', 920, 700, 'Idea: coffee mug on a deck in the trees')
placeholder('ph-3', 920, 700, 'Idea: kayak on a lake, a trail, or ski slopes')
placeholder('ph-4', 920, 700, 'Idea: cozy downtown restaurant or starry sky')
placeholder('ph-5', 920, 700, 'Idea: brunch table or a forest trail')
placeholder('ph-cta', 920, 430, 'Idea: your best Poconos home photo')
print('ok')
