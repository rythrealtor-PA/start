"""Poconos Tier List: dark topographic-map background with a tier-color stripe."""
import math, random
W, H = 1080, 1350
TIERS = ['#FF7F7F', '#FFBF7F', '#FFDF7F', '#BFFF7F']

def loops(cx, cy, seed, rmax=950):
    r = random.Random(seed); ph = [r.uniform(0, 6.28) for _ in range(4)]; s = ''
    rr = 50
    while rr < rmax:
        pts = []
        for i in range(73):
            t = i / 72 * math.tau
            k = 1 + 0.13 * math.sin(3 * t + ph[0] + rr / 260) + 0.07 * math.sin(5 * t + ph[1]) + 0.04 * math.sin(9 * t + ph[2] + rr / 120)
            pts.append((cx + rr * k * math.cos(t), cy + rr * 0.82 * k * math.sin(t)))
        d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + ' Z'
        op = 0.55 if int(rr / 38) % 5 == 0 else 0.28
        sw = 2.2 if int(rr / 38) % 5 == 0 else 1.4
        s += f'<path d="{d}" fill="none" stroke="#3A4250" stroke-opacity="{op}" stroke-width="{sw}"/>'
        rr += 38
    return s

body = f'<rect width="{W}" height="{H}" fill="#14161B"/>'
body += '<g>' + loops(180, 260, 1, 700) + loops(930, 1050, 2, 800) + '</g>'
body += '<radialGradient id="v" cx="0.5" cy="0.45" r="0.75"><stop offset="0.55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.55"/></radialGradient>'
body += f'<rect width="{W}" height="{H}" fill="url(#v)"/>'
for i, c in enumerate(TIERS):
    body += f'<rect x="{i*W/4:.0f}" y="0" width="{W/4+1:.0f}" height="12" fill="{c}"/>'
body += ('<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="5"/>'
         '<feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.05 0"/></filter>'
         f'<rect width="{W}" height="{H}" filter="url(#grain)"/>')
open('tier-bg.svg', 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{body}</svg>')
print('ok')
