"""Backgrounds for 'What $600K buys you: New Jersey vs. the Poconos' (1080x1350).
Style: shopping receipts on a split NJ (slate city) / PA (forest mountains) world.
Values on the receipts stay editable in Canva; row labels, leaders and decoration are baked."""
import base64, math, random

W, H = 1080, 1350


def font_face(name, file, weight=400):
    data = base64.b64encode(open(f'fonts/{file}', 'rb').read()).decode()
    return f"@font-face{{font-family:'{name}';src:url(data:font/ttf;base64,{data});font-weight:{weight};}}"


FONTS = font_face('Mono', 'JetBrainsMono-800.ttf', 800) + font_face('Mono7', 'JetBrainsMono-700.ttf', 700) + font_face('Marker', 'PermanentMarker-400.ttf')
NJ = ('#1E2530', '#38414F', '#F2C230')     # slate night, steel, taxi yellow
PA = ('#123526', '#2C6B4C', '#F4A340')     # forest, pine, sunrise orange


def defs():
    return f'''<defs><style>{FONTS}</style>
<linearGradient id="nj" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#151B24"/><stop offset="1" stop-color="#3A4352"/></linearGradient>
<linearGradient id="pa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0E2A1F"/><stop offset="1" stop-color="#2F6B4D"/></linearGradient>
<linearGradient id="mix" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#1E2530"/><stop offset="1" stop-color="#14382A"/></linearGradient>
<filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="12"/></filter>
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.05 0"/></filter>
<pattern id="paperTex" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="#FBFAF6"/><rect width="1" height="1" fill="#EFEDE6"/></pattern>
</defs>'''


def skyline(x0, x1, base_y, seed, color='#0F141B', windows='#F2C230'):
    rnd = random.Random(seed)
    out, x = '', x0
    while x < x1:
        w = rnd.randint(46, 96); h = rnd.randint(110, 330)
        out += f'<rect x="{x}" y="{base_y-h}" width="{w}" height="{h+2}" fill="{color}"/>'
        for wy in range(base_y - h + 16, base_y - 14, 26):
            for wx in range(x + 9, x + w - 12, 18):
                if rnd.random() < 0.28:
                    out += f'<rect x="{wx}" y="{wy}" width="8" height="12" fill="{windows}" opacity="{rnd.uniform(0.35, 0.9):.2f}"/>'
        x += w + rnd.randint(2, 10)
    return out


def mountains(x0, x1, base_y, seed):
    rnd = random.Random(seed)
    out = ''
    for layer, (col, hmin, hmax) in enumerate([('#3E7D5C', 160, 260), ('#25553F', 110, 200), ('#123526', 60, 140)]):
        pts, x = [(x0, base_y)], x0
        while x < x1:
            pts.append((x, base_y - rnd.randint(hmin, hmax) + layer * 30)); x += rnd.randint(90, 170)
        pts += [(x1, base_y - rnd.randint(hmin, hmax)), (x1, base_y + 400), (x0, base_y + 400)]
        out += f'<polygon points="{" ".join(f"{a},{b}" for a, b in pts)}" fill="{col}"/>'
    for i in range(int((x1 - x0) / 34)):  # pines on the front ridge
        px = x0 + 10 + i * 34 + rnd.randint(-8, 8); ph = rnd.randint(40, 80); py = base_y + 10 - rnd.randint(0, 30)
        out += f'<polygon points="{px},{py-ph} {px-ph*0.32},{py} {px+ph*0.32},{py}" fill="#0B2219"/>'
    return out


def sun(cx, cy, r, color):
    return f'<circle cx="{cx}" cy="{cy}" r="{r*2.2}" fill="{color}" opacity="0.12"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="0.9"/>'


def zigzag_paper(x, y, w, h, tooth=14):
    top = ' '.join(f'L{x + i * tooth + tooth / 2},{y - tooth / 2 if i % 2 == 0 else y}' for i in range(int(w / tooth) + 1))
    bot = ' '.join(f'L{x + w - i * tooth - tooth / 2},{y + h + (tooth / 2 if i % 2 == 0 else 0)}' for i in range(int(w / tooth) + 1))
    d = f'M{x},{y} {top} L{x+w},{y} L{x+w},{y+h} {bot} L{x},{y+h} Z'
    return (f'<path d="{d}" fill="#000" opacity="0.45" transform="translate(10 16)" filter="url(#sh)"/>'
            f'<path d="{d}" fill="url(#paperTex)"/>')


def mono(x, y, text, size=24, color='#2A2A2A', anchor='start', ls=1.5, weight='Mono'):
    return f'<text x="{x}" y="{y}" font-family="{weight}" font-size="{size}" letter-spacing="{ls}" fill="{color}" text-anchor="{anchor}">{text}</text>'


def receipt(x, y, w, header, rows, row_h, total_label='PRICE / SQ FT', foot=True):
    """Returns (svg, layout) — layout gives y of each row value and the total, for placing Canva text."""
    h = 92 + len(rows) * row_h + 40 + 110 + (60 if foot else 20)
    out = zigzag_paper(x, y, w, h)
    out += mono(x + w / 2, y + 44, f'* {header} *', 26, '#222', 'middle', 4)
    out += mono(x + w / 2, y + 74, '$600K BUDGET RECEIPT', 17, '#777', 'middle', 3, 'Mono7')
    out += f'<line x1="{x+30}" y1="{y+92}" x2="{x+w-30}" y2="{y+92}" stroke="#999" stroke-width="2" stroke-dasharray="6 6"/>'
    lay = {'rows': [], 'x0': x + 40, 'x1': x + w - 40}
    for i, lab in enumerate(rows):
        ry = y + 92 + 18 + i * row_h
        out += mono(x + 40, ry + row_h * 0.62, lab, 24, '#333')
        out += f'<line x1="{x+40+len(lab)*16.5+12}" y1="{ry+row_h*0.62-6}" x2="{x+w-250}" y2="{ry+row_h*0.62-6}" stroke="#BBB" stroke-width="2.5" stroke-dasharray="2 8" stroke-linecap="round"/>'
        lay['rows'].append(ry)
    ty = y + 92 + 18 + len(rows) * row_h + 14
    out += f'<line x1="{x+30}" y1="{ty}" x2="{x+w-30}" y2="{ty}" stroke="#222" stroke-width="3"/>'
    out += mono(x + 40, ty + 62, total_label, 28, '#111', ls=2)
    lay['total'] = ty + 18
    if foot:
        by = ty + 112
        bars = ''.join(f'<rect x="{x + w/2 - 120 + i*6}" y="{by}" width="{[2,4,1,3][i%4]}" height="34" fill="#222"/>' for i in range(40))
        out += bars
    lay['bottom'] = y + h
    return out, lay


def page(bg, inner):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{defs()}{bg}{inner}<rect width="{W}" height="{H}" filter="url(#grain)"/></svg>'


def nj_bg(seed):
    return f'<rect width="{W}" height="{H}" fill="url(#nj)"/>' + skyline(-20, W + 20, 1270, seed)


def pa_bg(seed):
    return f'<rect width="{W}" height="{H}" fill="url(#pa)"/>' + sun(880, 330, 70, '#F4A340') + mountains(-40, W + 40, 1180, seed)


layouts = {}


def nj_slide(name, header, rows, seed):
    rec, lay = receipt(170, 530, 740, header, rows, 58)
    layouts[name] = lay
    open(f'{name}.svg', 'w').write(page(nj_bg(seed), rec))


def pa_slide(name, header, rows, seed):
    # two photo frames + receipt
    frames = ''
    for fx in (70, 555):
        frames += f'<rect x="{fx+8}" y="{300+12}" width="455" height="290" fill="#000" opacity="0.45" filter="url(#sh)"/><rect x="{fx-7}" y="293" width="469" height="304" fill="#F7F3EA"/>'
    rec, lay = receipt(170, 640, 740, header, rows, 48, foot=False)
    layouts[name] = lay
    open(f'{name}.svg', 'w').write(page(pa_bg(seed), frames + rec))


def cover():
    bg = (f'<rect width="{W}" height="{H}" fill="url(#nj)"/>'
          f'<polygon points="{W/2+60},0 {W},0 {W},{H} {W/2-60},{H}" fill="url(#pa)"/>'
          + skyline(-20, W / 2 - 40, 1265, 5)
          + sun(900, 1010, 64, '#F4A340')
          + f'<g clip-path="url(#right)">{mountains(W/2-80, W+40, 1180, 9)}</g>')
    bg = bg.replace('<g clip-path="url(#right)">', '<clipPath id="right"><polygon points="{0},0 {1},0 {1},{2} {3},{2}"/></clipPath><g clip-path="url(#right)">'.format(W/2+60, W, H, W/2-60))
    tags = (f'<rect x="70" y="520" width="250" height="56" rx="28" fill="{NJ[2]}"/>' + mono(195, 558, 'NEW JERSEY', 24, '#1E2530', 'middle', 3)
            + f'<rect x="760" y="520" width="250" height="56" rx="28" fill="{PA[2]}"/>' + mono(885, 558, 'POCONOS, PA', 24, '#123526', 'middle', 3))
    vs = (f'<circle cx="540" cy="760" r="62" fill="#FBFAF6"/>' + f'<text x="540" y="783" text-anchor="middle" font-family="Marker" font-size="58" fill="#C0392B">VS</text>')
    open('k600-cover.svg', 'w').write(page(bg, tags + vs))


def math_slide():
    bg = f'<rect width="{W}" height="{H}" fill="url(#mix)"/>' + skyline(-20, 520, 1270, 21, '#121820') + f'<g opacity="0.9">{mountains(520, W+40, 1200, 23)}</g>'
    card = f'<rect x="70" y="440" width="940" height="640" rx="26" fill="#FBFAF6"/>'
    data = [('HOBOKEN, NJ', 936, NJ[1], '1 bed · 636 sq ft'), ('NUTLEY, NJ', 434, NJ[1], '3 bed · 1,380 sq ft'),
            ('E. STROUDSBURG, PA', 182, PA[1], '3 bed · 3,235 sq ft'), ('MOUNT POCONO, PA', 143, PA[1], '4 bed · 4,056 sq ft')]
    out = card + mono(110, 500, 'PRICE PER SQUARE FOOT', 24, '#666', ls=4)
    maxw = 560
    for i, (lab, v, col, sub) in enumerate(data):
        y = 545 + i * 128
        bw = maxw * v / 936
        out += mono(110, y + 26, lab, 24, '#222', ls=2)
        out += mono(110, y + 54, sub, 19, '#888', ls=1, weight='Mono7')
        out += f'<rect x="110" y="{y+70}" width="{bw:.0f}" height="34" rx="6" fill="{col}"/>'
        out += mono(110 + bw + 16, y + 98, f'${v}', 34, '#111', ls=1)
    out += mono(540, 1062, 'List price ÷ listed square feet · Nov 2026', 17, '#999', 'middle', 1, 'Mono7')
    open('k600-math.svg', 'w').write(page(bg, out))


def cta():
    bg = pa_bg(31)
    rec, lay = receipt(150, 330, 780, 'THE POCONOS', [], 40, total_label='', foot=True)
    open('k600-cta.svg', 'w').write(page(bg, f'<rect x="110" y="300" width="860" height="700" rx="26" fill="#FBFAF6"/>'))


def placeholder(fn, hint):
    w, h = 910, 580
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs><style>{FONTS}</style></defs>
<rect width="{w}" height="{h}" fill="#DCD6CA"/>
<rect x="18" y="18" width="{w-36}" height="{h-36}" fill="none" stroke="#8F8670" stroke-width="5" stroke-dasharray="22 14" rx="10"/>
<g transform="translate({w/2-60},170)"><rect x="0" y="24" width="120" height="86" rx="14" fill="none" stroke="#6F6652" stroke-width="7"/>
<path d="M36,24 L46,6 H74 L84,24" fill="none" stroke="#6F6652" stroke-width="7" stroke-linejoin="round"/><circle cx="60" cy="67" r="24" fill="none" stroke="#6F6652" stroke-width="7"/></g>
<text x="{w/2}" y="360" text-anchor="middle" font-family="Mono" font-size="40" letter-spacing="4" fill="#4F4836">ADD HOME PHOTO</text>
<text x="{w/2}" y="415" text-anchor="middle" font-family="Mono7" font-size="30" fill="#4F4836">{hint}</text>
<text x="{w/2}" y="495" text-anchor="middle" font-family="Mono7" font-size="22" fill="#7E765F">Drag a photo onto this box to replace it</text></svg>'''
    open(fn, 'w').write(svg)


if __name__ == '__main__':
    import json
    cover()
    nj_slide('k600-nj1', 'NEW JERSEY · HOBOKEN', ['PRICE', 'BEDS', 'BATHS', 'SQ FT', 'HOA FEE', 'PARKING'], 41)
    pa_slide('k600-pa1', 'POCONOS · MOUNT POCONO', ['PRICE', 'BEDS', 'BATHS', 'SQ FT', 'LOT', 'BUILT', 'TAXES / YR'], 43)
    nj_slide('k600-nj2', 'NEW JERSEY · NUTLEY', ['PRICE', 'BEDS', 'BATHS', 'SQ FT', 'LOT', 'BUILT', 'TAXES / YR'], 47)
    pa_slide('k600-pa2', 'POCONOS · E. STROUDSBURG', ['PRICE', 'BEDS', 'BATHS', 'SQ FT', 'LOT', 'BUILT', 'TAXES / YR'], 53)
    math_slide()
    cta()
    placeholder('ph-home-1.svg', 'Front of the house')
    placeholder('ph-home-2.svg', 'Best interior or the view')
    json.dump(layouts, open('k600-layout.json', 'w'), indent=1)
    print(json.dumps(layouts))
