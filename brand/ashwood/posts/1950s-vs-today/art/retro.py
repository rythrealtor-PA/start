import math, random
W, H = 1080, 1350
CREAM, PAPER, NAVY, CORAL, TEAL, MUST = '#F3E6CC', '#EFDDBA', '#1F2A44', '#D9583B', '#2C7A7B', '#E8B04A'
DEFS = ('<defs>'
 '<filter id="paper"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="11"/><feColorMatrix values="0 0 0 0 0.45  0 0 0 0 0.33  0 0 0 0 0.18  0 0 0 0.22 0"/></filter>'
 '<filter id="fiber"><feTurbulence type="fractalNoise" baseFrequency="0.012 0.25" numOctaves="2" seed="3"/><feColorMatrix values="0 0 0 0 0.5  0 0 0 0 0.38  0 0 0 0 0.2  0 0 0 0.10 0"/></filter>'
 '<radialGradient id="vig" cx="0.5" cy="0.5" r="0.75"><stop offset="0.6" stop-color="#8A6A3A" stop-opacity="0"/><stop offset="1" stop-color="#8A6A3A" stop-opacity="0.35"/></radialGradient>'
 '<pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="8" cy="8" r="3" fill="#D9583B"/></pattern>'
 '</defs>')

def base():
    s = f'<rect width="{W}" height="{H}" fill="{PAPER}"/>'
    s += f'<rect width="{W}" height="{H}" filter="url(#fiber)"/><rect width="{W}" height="{H}" filter="url(#paper)"/>'
    return s

def border():
    return (f'<rect x="26" y="26" width="{W-52}" height="{1265-40}" fill="none" stroke="{NAVY}" stroke-width="4" rx="6"/>'
            f'<rect x="40" y="40" width="{W-80}" height="{1265-68}" fill="none" stroke="{CORAL}" stroke-width="2" rx="4" stroke-dasharray="2 0"/>')

def sunburst(cx, cy, n=36, col=MUST, op=0.22):
    s = f'<g opacity="{op}">'
    for i in range(n):
        if i % 2: continue
        a0 = i / n * math.tau; a1 = (i + 1) / n * math.tau
        R = 1600
        s += f'<path d="M{cx},{cy} L{cx+R*math.cos(a0):.0f},{cy+R*math.sin(a0):.0f} L{cx+R*math.cos(a1):.0f},{cy+R*math.sin(a1):.0f} Z" fill="{col}"/>'
    return s + '</g>'

def halftone_corner(x, y, w, h, flip=False):
    # dots fade toward the inside
    s = ''
    for i in range(0, w, 18):
        for j in range(0, h, 18):
            t = 1 - ((i / w) + (j / h)) / 1.4
            if t <= 0: continue
            r = 4.2 * t
            px = x + (w - i if flip else i); py = y + j
            s += f'<circle cx="{px}" cy="{py}" r="{r:.1f}" fill="{CORAL}" opacity="0.55"/>'
    return s

def retro_scene(y0):
    # flat 1950s travel-poster mountains + lake, from y0 down to 1265
    s = f'<circle cx="760" cy="{y0+70}" r="120" fill="{CORAL}"/>'
    for k in range(4):
        s += f'<rect x="630" y="{y0+90+k*22}" width="260" height="{6+k*2}" fill="{PAPER}"/>'
    s += f'<path d="M40,{y0+260} L230,{y0+40} L360,{y0+190} L520,{y0+10} L720,{y0+230} L860,{y0+120} L1040,{y0+260} L1040,{y0+300} L40,{y0+300} Z" fill="{TEAL}"/>'
    s += f'<path d="M230,{y0+40} L270,{y0+90} L245,{y0+85} L215,{y0+110} L200,{y0+75} Z M520,{y0+10} L565,{y0+62} L535,{y0+56} L505,{y0+80} L490,{y0+45} Z" fill="{CREAM}"/>'
    s += f'<path d="M40,{y0+300} L180,{y0+200} L330,{y0+290} L480,{y0+210} L650,{y0+300} L820,{y0+220} L1040,{y0+300} L1040,{y0+330} L40,{y0+330} Z" fill="{NAVY}"/>'
    s += f'<rect x="40" y="{y0+330}" width="1000" height="{1225-(y0+330)}" fill="#5FA3A3"/>'
    for k in range(6):
        y = y0 + 350 + k * 22
        s += f'<path d="M{600+k*12},{y} L{920-k*14},{y}" stroke="{CORAL}" stroke-width="5" opacity="{0.8-k*0.1:.2f}"/>'
    for x, h in ((90, 210), (150, 160), (960, 230), (1010, 170)):
        s += f'<path d="M{x},{1225-h} L{x+40},{1225} L{x-40},{1225} Z" fill="{NAVY}"/>'
    # canoe
    s += f'<path d="M300,{y0+420} Q380,{y0+445} 460,{y0+420} Q380,{y0+432} 300,{y0+420} Z" fill="{CORAL}"/>'
    return s

def stamp(x, y, label):
    s = f'<g transform="translate({x},{y}) rotate(8)">'
    s += f'<rect x="-70" y="-85" width="140" height="170" fill="{CREAM}" stroke="{NAVY}" stroke-width="3" stroke-dasharray="6 5"/>'
    s += f'<rect x="-55" y="-70" width="110" height="110" fill="{TEAL}"/><path d="M-55,40 L-20,-10 L5,15 L25,-15 L55,40 Z" fill="{NAVY}"/><circle cx="25" cy="-45" r="14" fill="{MUST}"/>'
    s += f'<text x="0" y="68" font-family="Georgia, serif" font-size="20" font-weight="bold" fill="{NAVY}" text-anchor="middle">{label}</text></g>'
    s += f'<g transform="translate({x-60},{y+20}) rotate(-12)" opacity="0.75"><circle r="62" fill="none" stroke="{CORAL}" stroke-width="4"/><circle r="50" fill="none" stroke="{CORAL}" stroke-width="2"/>'
    s += f'<text y="-8" font-family="Georgia, serif" font-size="16" font-weight="bold" fill="{CORAL}" text-anchor="middle">POCONO MTS</text><text y="16" font-family="Georgia, serif" font-size="16" font-weight="bold" fill="{CORAL}" text-anchor="middle">PA</text></g>'
    return s

def finish():
    return f'<rect width="{W}" height="{H}" fill="url(#vig)"/>'

def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}{body}</svg>'

cover = base() + sunburst(540, 520) + retro_scene(940) + border() + stamp(915, 162, '1950s') + halftone_corner(46, 46, 220, 160) + finish()
content = base() + border() + halftone_corner(46, 46, 200, 140) + halftone_corner(W-246, 46, 200, 140, True) + finish()
cta = base() + sunburst(540, 980, col=MUST, op=0.16) + retro_scene(860) + border() + halftone_corner(46, 46, 200, 140) + finish()
for n, b in (('retro-cover', cover), ('retro-content', content), ('retro-cta', cta)):
    open(f'{n}.svg', 'w').write(svg(b))
print('ok')
