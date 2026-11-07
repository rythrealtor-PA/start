"""Backgrounds for the 'Meet the wolf in our logo' carousel (1080x1350).
Style: logo study on warm paper with a drafting grid, navy line art, gold callouts.
Logo shapes are vector traces of the Ashwood serif logo (logo-vec.json, 1261x649 space)."""
import json, re, math

V = json.load(open('logo-vec.json'))
WOLF, HOUSE, WIN = V['wolf'], V['house'], V['window']
word_subs = re.findall(r'M[^M]*', V['word'])
ASHWOOD = ' '.join(s for s in word_subs if float(re.match(r'M[\d.]+,([\d.]+)', s).group(1)) < 540)
REALEST = ' '.join(s for s in word_subs if float(re.match(r'M[\d.]+,([\d.]+)', s).group(1)) >= 540)
ZIG = V['zig']

W, H = 1080, 1350
NAVY, STEEL, GOLD, GOLD_D, PAPER = '#08233B', '#798597', '#E7A845', '#B9802A', '#F4F1EA'
MONO = "font-family:'JetBrains Mono',monospace;font-weight:600"


def grid():
    g = []
    for x in range(0, W + 1, 30):
        major = x % 150 == 0
        g.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="{"#DCD5C6" if major else "#E9E4D9"}" stroke-width="{1.2 if major else 1}"/>')
    for y in range(0, H + 1, 30):
        major = y % 150 == 0
        g.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{"#DCD5C6" if major else "#E9E4D9"}" stroke-width="{1.2 if major else 1}"/>')
    return ''.join(g)


def base(inner, defs=''):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
<filter id="paper" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="4"/><feColorMatrix values="0 0 0 0 0.35  0 0 0 0 0.30  0 0 0 0 0.22  0 0 0 0.07 0"/></filter>
<radialGradient id="vig" cx="0.5" cy="0.45" r="0.75"><stop offset="0.6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#3A2E1A" stop-opacity="0.10"/></radialGradient>
<radialGradient id="sun" cx="0.4" cy="0.38" r="0.7"><stop offset="0" stop-color="#FFE7AE"/><stop offset="0.6" stop-color="#F6BF5E"/><stop offset="1" stop-color="#E39A3B"/></radialGradient>
<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
<filter id="soft2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2"/></filter>
{defs}
</defs>
<rect width="{W}" height="{H}" fill="{PAPER}"/>
{grid()}
<rect width="{W}" height="{H}" filter="url(#paper)"/>
{inner}
<rect width="{W}" height="{H}" fill="url(#vig)"/>
</svg>'''


def g(s, cx_logo, cy_logo, cx, cy, body):
    tx, ty = cx - cx_logo * s, cy - cy_logo * s
    return f'<g transform="translate({tx:.2f},{ty:.2f}) scale({s})">{body}</g>', (lambda x, y: (tx + x * s, ty + y * s))


def full_logo(window_fill=STEEL):
    return (f'<path d="{HOUSE}" fill="{NAVY}" fill-rule="evenodd"/>'
            f'<path d="{WIN}" fill="{window_fill}"/>'
            f'<path d="{ASHWOOD}" fill="{NAVY}" fill-rule="evenodd"/>'
            f'<path d="{REALEST}" fill="{STEEL}" fill-rule="evenodd"/>'
            f'<path d="{WOLF}" fill="{STEEL}" fill-rule="evenodd"/>')


def label(x, y, text, size=21, color=GOLD_D, anchor='start'):
    return f'<text x="{x}" y="{y}" style="{MONO}" font-size="{size}" letter-spacing="2.5" fill="{color}" text-anchor="{anchor}">{text}</text>'


def cross(x, y, c='#BDB4A2'):
    return f'<path d="M{x-9},{y} H{x+9} M{x},{y-9} V{y+9}" stroke="{c}" stroke-width="2"/>'


def frame_marks(y0=470, y1=1225):
    return cross(60, y0) + cross(1020, y0) + cross(60, y1) + cross(1020, y1)


def sun(cx, cy, r, rays=True):
    out = f'<circle cx="{cx}" cy="{cy}" r="{r*1.9}" fill="#F6C46B" opacity="0.28" filter="url(#soft)"/>'
    if rays:
        for i in range(12):
            a = i * math.pi / 6
            out += (f'<line x1="{cx + (r+16)*math.cos(a):.1f}" y1="{cy + (r+16)*math.sin(a):.1f}" '
                    f'x2="{cx + (r+40)*math.cos(a):.1f}" y2="{cy + (r+40)*math.sin(a):.1f}" stroke="{GOLD}" stroke-width="5" stroke-linecap="round"/>')
    out += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#sun)"/>'
    return out


def arrow(x0, y0, x1, y1, color=GOLD_D, dash='3 12', w=4):
    a = math.atan2(y1 - y0, x1 - x0); h = 16
    hx1, hy1 = x1 - h * math.cos(a - 0.5), y1 - h * math.sin(a - 0.5)
    hx2, hy2 = x1 - h * math.cos(a + 0.5), y1 - h * math.sin(a + 0.5)
    return (f'<path d="M{x0:.1f},{y0:.1f} L{x1:.1f},{y1:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-dasharray="{dash}" fill="none"/>'
            f'<path d="M{hx1:.1f},{hy1:.1f} L{x1:.1f},{y1:.1f} L{hx2:.1f},{hy2:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" fill="none"/>')


def leader(pts, color=GOLD_D):
    d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    x, y = pts[-1]
    return (f'<path d="{d}" stroke="{color}" stroke-width="2.5" fill="none"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{PAPER}" stroke="{color}" stroke-width="3"/>')


slides = {}

# 1 — cover: full logo, wolf circled
body, P = g(0.66, 630.5, 0, 540, 500, full_logo())
cx, cy = P(673, 138)
r = 104
ring = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{GOLD}" stroke-width="5" stroke-dasharray="14 10" stroke-linecap="round"/>'
lx, ly = cx + r * math.cos(-0.6), cy + r * math.sin(-0.6)
slides['wolf-1'] = base(body + ring + leader([(860, 470), (760, 470), (lx, ly)]) + label(870, 478, 'THE WOLF') + frame_marks(455, 1225))

# 2 — direction: wolf faces the sunrise, back to the sunset
body, P = g(2.55, 673, 137.5, 420, 905, f'<path d="{WOLF}" fill="{STEEL}" fill-rule="evenodd"/>')
sx, sy = P(772, 30)
art = (sun(905, 600, 74)
       + label(905, 742, 'SUNRISE · EAST', 20, GOLD_D, 'middle')
       + arrow(sx + 26, sy - 8, 805, 615)
       + f'<line x1="60" y1="1175" x2="330" y2="1175" stroke="#C9C0AE" stroke-width="2" stroke-dasharray="6 8"/>'
       + f'<path d="M140,1175 A50,50 0 0 1 240,1175 Z" fill="#D8CFBD"/>'
       + label(190, 1212, 'SUNSET · WEST', 18, '#A39A88', 'middle'))
slides['wolf-2'] = base(art + body + label(60, 505, 'FIG. 01 — DIRECTION', 18, '#A39A88') + frame_marks())

# 3 — fade: wolf fades, the home (your story) glows
fade = ('<linearGradient id="fade" gradientUnits="userSpaceOnUse" x1="0" y1="40" x2="0" y2="236">'
        f'<stop offset="0" stop-color="{STEEL}" stop-opacity="0.95"/><stop offset="1" stop-color="{STEEL}" stop-opacity="0.12"/></linearGradient>')
inner = (f'<path d="{HOUSE}" fill="{NAVY}" fill-rule="evenodd"/>'
         f'<path d="{WIN}" fill="#F6C46B" filter="url(#soft2)"/>'
         f'<path d="{WIN}" fill="#F4B54E"/>'
         f'<path d="{WOLF}" fill="url(#fade)" fill-rule="evenodd"/>')
body, P = g(1.95, 607, 182, 540, 870, inner)
wx, wy = P(588, 120)
gx, gy = P(647, 276)
glow = f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="120" fill="#F6C46B" opacity="0.35" filter="url(#soft)"/>'
art = (glow + body
       + leader([(330, 560), (420, 560), (wx - 4, wy)]) + label(70, 568, 'US', 22) + label(70, 598, 'A SMALL PART', 18, '#A39A88')
       + leader([(930, 1190), (830, 1190), (gx + 30, gy + 30)]) + label(1020, 1170, 'YOU', 22, GOLD_D, 'end') + label(1020, 1220, 'THE MAIN STORY', 18, '#A39A88', 'end'))
slides['wolf-3'] = base(art + label(60, 505, 'FIG. 02 — THE FADE', 18, '#A39A88') + cross(60, 470) + cross(1020, 470), defs=fade)

# 4 — mane: the mountains are the Poconos
zig = ' '.join(f'{x},{y}' for x, y in ZIG)
inner = (f'<path d="{WOLF}" fill="{STEEL}" fill-rule="evenodd"/>'
         f'<polyline points="{zig}" fill="none" stroke="#F6C46B" stroke-width="5" stroke-linejoin="round" stroke-linecap="round" filter="url(#soft2)" opacity="0.9"/>'
         f'<polyline points="{zig}" fill="none" stroke="{GOLD}" stroke-width="2.8" stroke-linejoin="round" stroke-linecap="round"/>')
body, P = g(3.15, 669, 150, 540, 840, inner)
L0, R0 = P(*ZIG[0]), P(*ZIG[-1])
left = [(L0[0], L0[1]), (L0[0] - 70, L0[1] + 55), (L0[0] - 130, L0[1] + 5), (L0[0] - 200, L0[1] + 70), (0, L0[1] + 30)]
right = [(R0[0], R0[1]), (R0[0] + 70, R0[1] - 55), (R0[0] + 130, R0[1] - 10), (R0[0] + 190, R0[1] - 70), (W, R0[1] - 25)]
rng = lambda pts: f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{GOLD}" stroke-width="3" stroke-dasharray="8 9" stroke-linejoin="round" opacity="0.75"/>'
px, py = P(*ZIG[2])
art = (rng(left) + rng(right) + body
       + leader([(540, 1175), (540, 1100), (px, py + 18)])
       + label(540, 1212, 'THE POCONOS, PA', 22, GOLD_D, 'middle'))
slides['wolf-4'] = base(art + label(60, 505, 'FIG. 03 — THE MANE', 18, '#A39A88') + cross(60, 470) + cross(1020, 470))

# 5 — CTA: full logo with a small rising sun ahead of the wolf
body, P = g(0.6, 630.5, 0, 540, 360, full_logo())
sx, sy = P(800, 30)
slides['wolf-5'] = base(sun(sx + 82, sy + 22, 26, rays=True) + body + frame_marks(330, 790))

for n, svg in slides.items():
    open(f'{n}.svg', 'w').write(svg)
print('ok', list(slides))
