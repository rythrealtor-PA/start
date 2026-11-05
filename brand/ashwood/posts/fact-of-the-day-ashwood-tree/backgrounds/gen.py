import math, random, sys
W, H = 1080, 1350
PAL = ["#F4C04E", "#EBA03A", "#E2832B", "#D0632A", "#B9461F", "#9E3519", "#F6D27A", "#C9572A"]
SUNLIT = ["#FFD86E", "#F7C04A", "#F2A83A", "#EE9330"]
SHADE = ["#B5441E", "#963217", "#7D2A14", "#A83C1A", "#C2561F"]

def shade(hexc, f):
    h = hexc.lstrip('#'); r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    if f < 1: r, g, b = r*f, g*f, b*f
    else: r, g, b = r+(255-r)*(f-1), g+(255-g)*(f-1), b+(255-b)*(f-1)
    return "#%02x%02x%02x" % (int(max(0,min(255,r))), int(max(0,min(255,g))), int(max(0,min(255,b))))

def leaf(x, y, L, rot, color, opacity=1.0, rib=True, blur=None):
    Wd = 0.30 * L
    d = f"M0,0 C{0.28*L:.1f},{-Wd:.1f} {0.72*L:.1f},{-0.78*Wd:.1f} {L:.1f},0 C{0.72*L:.1f},{0.78*Wd:.1f} {0.28*L:.1f},{Wd:.1f} 0,0 Z"
    f = f' filter="url(#{blur})"' if blur else ''
    s = f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f})" opacity="{opacity:.2f}"{f}>'
    s += f'<path d="{d}" fill="{color}"/>'
    s += f'<path d="M0,0 C{0.28*L:.1f},{-Wd:.1f} {0.72*L:.1f},{-0.78*Wd:.1f} {L:.1f},0 Z" fill="{shade(color,1.18)}" opacity="0.55"/>'
    if rib:
        s += f'<path d="M{-0.18*L:.1f},0 L{0.92*L:.1f},0" stroke="{shade(color,0.6)}" stroke-width="{max(0.8,0.035*L):.1f}" stroke-linecap="round"/>'
    return s + '</g>'

def compound(x, y, L, rot, color, opacity=1.0):
    # ash compound leaf: rachis with paired leaflets + terminal leaflet
    s = f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f})" opacity="{opacity:.2f}">'
    s += f'<path d="M0,0 Q{L*0.5:.1f},{-L*0.06:.1f} {L:.1f},0" stroke="{shade(color,0.55)}" stroke-width="{L*0.018:.1f}" fill="none" stroke-linecap="round"/>'
    n = 3
    for i in range(n):
        t = 0.3 + i * 0.23
        px = L * t; ll = L * 0.36
        s += leaf(px, -L*0.02, ll, -55 + random.uniform(-6, 6), shade(color, random.uniform(0.92, 1.08)), 1, False)
        s += leaf(px, -L*0.02, ll, 55 + random.uniform(-6, 6), shade(color, random.uniform(0.92, 1.08)), 1, False)
    s += leaf(L, 0, L*0.4, random.uniform(-8, 8), color, 1, False)
    return s + '</g>'

def key(x, y, sc, rot, opacity=1.0):
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f}) scale({sc:.2f}) translate(-40,0)" opacity="{opacity:.2f}" filter="url(#keyglow)">'
            '<path fill-rule="evenodd" fill="url(#gold)" stroke="#7A4D12" stroke-width="1.1" d="'
            'M0,0 a15,15 0 1,0 30,0 a15,15 0 1,0 -30,0 Z M9,0 a6,6 0 1,1 12,0 a6,6 0 1,1 -12,0 Z"/>'
            '<path fill="url(#gold)" stroke="#7A4D12" stroke-width="1.1" d="M27,-4 L82,-4 Q85,-4 85,-1 L85,4 L80,4 L80,11 L76,11 L76,8 L72,8 L72,12 L67,12 L67,8 L63,8 L63,11 L59,11 L59,4 L27,4 Z"/>'
            '<rect x="27" y="-7" width="6" height="14" rx="1.5" fill="url(#gold)" stroke="#7A4D12" stroke-width="1"/>'
            '<path d="M31,-1.5 L80,-1.5" stroke="#FFF3C4" stroke-width="1.2" opacity="0.7"/>'
            '</g>')

def ridge(base, amps, seed):
    rnd = random.Random(seed)
    comps = [(a, rnd.uniform(0.002, 0.012) * (i + 1) * 0.6, rnd.uniform(0, 6.28)) for i, a in enumerate(amps)]
    pts = []
    for x in range(-20, W + 21, 10):
        y = base + sum(a * math.sin(f * x + p) for a, f, p in comps)
        pts.append((x, y))
    return pts

def hill(pts, color, opacity=1):
    d = f"M{pts[0][0]},{H+10} " + " ".join(f"L{x},{y:.1f}" for x, y in pts) + f" L{pts[-1][0]},{H+10} Z"
    return f'<path d="{d}" fill="{color}" opacity="{opacity}"/>'

def forest(pts, colors, rmin, rmax, depth, n, seed, pine=0.12, dark="#2a1208"):
    rnd = random.Random(seed); s = ''
    for _ in range(n):
        i = rnd.randrange(len(pts) - 1); x0, y0 = pts[i]; x1, y1 = pts[i+1]
        t = rnd.random(); x = x0 + (x1-x0)*t; y = y0 + (y1-y0)*t + rnd.uniform(-rmax*0.4, depth)
        if rnd.random() < pine:
            h = rnd.uniform(rmax*2.2, rmax*3.2); w = h*0.42
            s += f'<path d="M{x:.1f},{y-h:.1f} L{x+w/2:.1f},{y:.1f} L{x-w/2:.1f},{y:.1f} Z" fill="{dark}"/>'
        else:
            r = rnd.uniform(rmin, rmax); c = rnd.choice(colors)
            dk = 1 - min(0.45, max(0, (y - y0) / (depth * 3 + 1)) * 0.45)
            c = shade(c, dk)
            s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}"/>'
            s += f'<circle cx="{x - r*0.28:.1f}" cy="{y - r*0.32:.1f}" r="{r*0.55:.1f}" fill="{shade(c, 1.22)}" opacity="0.55"/>'
    return s

def branches(x, y, ang, length, width, depth, rnd, out):
    if depth == 0 or length < 8: return
    x2 = x + length * math.cos(math.radians(ang)); y2 = y - length * math.sin(math.radians(ang))
    cx = (x + x2)/2 + rnd.uniform(-length*0.15, length*0.15); cy = (y + y2)/2 + rnd.uniform(-length*0.1, length*0.1)
    out.append(f'<path d="M{x:.1f},{y:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}" stroke="#2A140B" stroke-width="{width:.1f}" stroke-linecap="round" fill="none"/>')
    for da in (rnd.uniform(18, 38), -rnd.uniform(18, 38)) + ((rnd.uniform(-8, 8),) if rnd.random() < 0.4 else ()):
        branches(x2, y2, ang + da, length * rnd.uniform(0.62, 0.78), width * 0.66, depth - 1, rnd, out)

def tree(cx, cy, rx, ry, ground, seed, leafmin=14, leafmax=26, density=1.0):
    rnd = random.Random(seed); out = []
    # crown shadow mass
    for _ in range(14):
        a = rnd.uniform(0, 6.28); rr = rnd.uniform(0, 0.55)
        out.append(f'<ellipse cx="{cx + rx*rr*math.cos(a):.1f}" cy="{cy + ry*rr*math.sin(a) + ry*0.12:.1f}" rx="{rx*rnd.uniform(0.35,0.55):.1f}" ry="{ry*rnd.uniform(0.3,0.5):.1f}" fill="#5E1F0E" opacity="0.55" filter="url(#soft)"/>')
    # trunk (twisted, like the logo tree)
    tw = rx * 0.13; top = cy + ry * 0.35
    out.append(f'<path d="M{cx-tw*1.4:.1f},{ground:.1f} C{cx-tw*0.6:.1f},{ground-(ground-top)*0.35:.1f} {cx-tw*1.1:.1f},{top+(ground-top)*0.3:.1f} {cx-tw*0.45:.1f},{top:.1f} '
               f'L{cx+tw*0.45:.1f},{top:.1f} C{cx+tw*0.9:.1f},{top+(ground-top)*0.35:.1f} {cx+tw*0.5:.1f},{ground-(ground-top)*0.3:.1f} {cx+tw*1.5:.1f},{ground:.1f} Z" fill="#2A140B"/>')
    out.append(f'<path d="M{cx-tw*2.6:.1f},{ground+2:.1f} Q{cx-tw*1.2:.1f},{ground-tw*0.6:.1f} {cx-tw*0.9:.1f},{ground-tw*1.6:.1f} L{cx+tw*0.9:.1f},{ground-tw*1.6:.1f} Q{cx+tw*1.3:.1f},{ground-tw*0.6:.1f} {cx+tw*2.8:.1f},{ground+2:.1f} Z" fill="#2A140B"/>')
    out.append(f'<path d="M{cx-tw*0.2:.1f},{ground-4:.1f} C{cx+tw*0.3:.1f},{ground-(ground-top)*0.4:.1f} {cx-tw*0.4:.1f},{top+(ground-top)*0.4:.1f} {cx+tw*0.1:.1f},{top+6:.1f}" stroke="#4A2614" stroke-width="{tw*0.18:.1f}" fill="none" opacity="0.8"/>')
    for ang in (60, 82, 100, 122, 140, 35, 155):
        branches(cx, top, ang, ry * rnd.uniform(0.42, 0.55), tw * 0.55, 4, rnd, out)
    # leaves
    n = int(rx * ry * math.pi / 150 * density)
    for _ in range(n):
        while True:
            u, v = rnd.uniform(-1, 1), rnd.uniform(-1, 1)
            edge = 1 + 0.12*math.sin(math.atan2(v, u)*7 + seed)
            if u*u + v*v <= edge*edge: break
        x = cx + u*rx; y = cy + v*ry
        if v > 0.35 and abs(u) < 0.35 and rnd.random() < 0.65: continue  # let branches show under the crown
        light = (-v*0.6 - u*0.25)
        col = rnd.choice(SUNLIT) if light > 0.25 and rnd.random() < 0.8 else (rnd.choice(SHADE) if light < -0.25 and rnd.random() < 0.75 else rnd.choice(PAL))
        out.append(leaf(x, y, rnd.uniform(leafmin, leafmax), rnd.uniform(0, 360), col, 1, False))
    return ''.join(out)

def cabin(x, y, sc=1.0):
    return (f'<g transform="translate({x},{y}) scale({sc})">'
            '<circle cx="18" cy="-118" r="10" fill="#E8D8C8" opacity="0.18" filter="url(#soft)"/><circle cx="30" cy="-140" r="14" fill="#E8D8C8" opacity="0.12" filter="url(#soft)"/><circle cx="44" cy="-166" r="18" fill="#E8D8C8" opacity="0.08" filter="url(#soft)"/>'
            '<rect x="10" y="-112" width="14" height="34" fill="#1A0904"/>'
            '<path d="M-70,-50 L0,-108 L70,-50 Z" fill="#1A0904"/>'
            '<rect x="-56" y="-54" width="112" height="56" fill="#220C06"/>'
            '<circle cx="-22" cy="-28" r="30" fill="#FFB347" opacity="0.35" filter="url(#glow)"/>'
            '<rect x="-34" y="-40" width="24" height="22" fill="#FFC46B"/><path d="M-22,-40 L-22,-18 M-34,-29 L-10,-29" stroke="#220C06" stroke-width="2.5"/>'
            '<rect x="14" y="-36" width="20" height="36" fill="#3A1A0C"/>'
            '</g>')

def defs():
    return ('<defs>'
            '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#2E0F0A"/><stop offset="0.32" stop-color="#6B2614"/>'
            '<stop offset="0.58" stop-color="#B4501F"/><stop offset="0.74" stop-color="#E08A35"/><stop offset="0.86" stop-color="#F2B355"/></linearGradient>'
            '<radialGradient id="sun"><stop offset="0" stop-color="#FFE3A3" stop-opacity="0.85"/><stop offset="0.35" stop-color="#FFC56B" stop-opacity="0.35"/><stop offset="1" stop-color="#FFC56B" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="vig" cx="0.5" cy="0.45" r="0.75"><stop offset="0.55" stop-color="#140603" stop-opacity="0"/><stop offset="1" stop-color="#140603" stop-opacity="0.75"/></radialGradient>'
            '<radialGradient id="textbg"><stop offset="0" stop-color="#240B05" stop-opacity="0.62"/><stop offset="0.6" stop-color="#240B05" stop-opacity="0.38"/><stop offset="1" stop-color="#240B05" stop-opacity="0"/></radialGradient>'
            '<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFEBA8"/><stop offset="0.5" stop-color="#E9B44C"/><stop offset="1" stop-color="#B07A22"/></linearGradient>'
            '<filter id="keyglow" x="-50%" y="-80%" width="200%" height="260%"><feDropShadow dx="0" dy="0" stdDeviation="5" flood-color="#FFD27A" flood-opacity="0.75"/></filter>'
            '<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>'
            '<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="10"/></filter>'
            '<filter id="b2"><feGaussianBlur stdDeviation="2"/></filter><filter id="b4" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>'
            '<filter id="big" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="60"/></filter>'
            '<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3"/><feColorMatrix values="0 0 0 0 0.1  0 0 0 0 0.05  0 0 0 0 0.02  0 0 0 0.5 0"/></filter>'
            '</defs>')

def falling(rnd, n, avoid, sizes=(26, 58), keys=0, keysize=(0.9, 1.35), region=(0, 0, W, 1240), compound_n=0):
    s = []
    def ok(x, y):
        return all(not (ax0 < x < ax1 and ay0 < y < ay1) for ax0, ay0, ax1, ay1 in avoid)
    placed = 0; tries = 0
    while placed < n and tries < 5000:
        tries += 1
        x = rnd.uniform(region[0], region[2]); y = rnd.uniform(region[1], region[3])
        if not ok(x, y): continue
        L = rnd.uniform(*sizes)
        blur = 'b4' if L > sizes[1]*0.9 and rnd.random() < 0.5 else ('b2' if L < sizes[0]*1.15 and rnd.random() < 0.4 else None)
        s.append(leaf(x, y, L, rnd.uniform(0, 360), rnd.choice(PAL), rnd.uniform(0.85, 1), True, blur)); placed += 1
    placed = 0; tries = 0
    while placed < compound_n and tries < 5000:
        tries += 1
        x = rnd.uniform(region[0], region[2]); y = rnd.uniform(region[1], region[3])
        if not ok(x, y): continue
        s.append(compound(x, y, rnd.uniform(90, 130), rnd.uniform(0, 360), rnd.choice(PAL), 0.95)); placed += 1
    placed = 0; tries = 0; kpos = []
    while placed < keys and tries < 5000:
        tries += 1
        x = rnd.uniform(region[0]+70, region[2]-70); y = rnd.uniform(region[1], region[3])
        if not ok(x, y) or any((x-a)**2 + (y-b)**2 < 170**2 for a, b in kpos): continue
        kpos.append((x, y))
        s.append(key(x, y, rnd.uniform(*keysize), rnd.uniform(-70, 70) + rnd.choice([0, 180]))); placed += 1
    return ''.join(s)

def bokeh(rnd, n, ymax=900):
    return ''.join(f'<circle cx="{rnd.uniform(0,W):.0f}" cy="{rnd.uniform(0,ymax):.0f}" r="{rnd.uniform(6,34):.0f}" fill="{rnd.choice(["#FFD98C","#FFC872","#FFE7B5"])}" opacity="{rnd.uniform(0.06,0.2):.2f}" filter="url(#b{rnd.choice([2,4])})"/>' for _ in range(n))

def rays():
    return ('<g opacity="0.07" filter="url(#b4)">' +
            ''.join(f'<path d="M{x},-50 L{x+120},-50 L{x+520},{H} L{x+330},{H} Z" fill="#FFE9B8"/>' for x in (-200, 60, 320)) + '</g>')

def landscape(seed, base_shift=0, cabin_at=None):
    s = ''
    far = ridge(905 + base_shift, [26, 14, 8], seed + 1); mid = ridge(975 + base_shift, [24, 12, 7], seed + 2)
    near = ridge(1055 + base_shift, [22, 10, 6], seed + 3); front = ridge(1150 + base_shift, [18, 9, 5], seed + 4)
    s += hill(far, "#A2482A", 0.75)
    s += forest(far, ["#B4532A", "#C2652F", "#A04224", "#8F3A1E"], 6, 11, 30, 420, seed+11, 0.05, "#5a2414")
    s += hill(mid, "#76301A")
    s += forest(mid, ["#C26A2B", "#D88A34", "#A8441F", "#E3A13F", "#8E3318"], 7, 15, 45, 560, seed+12, 0.04, "#3b1a0c")
    s += hill(near, "#4E1E10")
    s += forest(near, ["#A8521F", "#C9752C", "#8A3416", "#D8963A", "#6E2A12"], 8, 17, 55, 520, seed+13, 0.06, "#24100a")
    s += hill(front, "#2B0F08")
    s += forest(front, ["#6B2A12", "#7E3416", "#5A220F"], 10, 18, 14, 160, seed+14, 0.08, "#160704")
    if cabin_at:
        cx = cabin_at; i = min(range(len(front)), key=lambda k: abs(front[k][0]-cx)); s += cabin(cx, front[i][1] + 14, 1.15)
    rnd = random.Random(seed + 77)
    for _ in range(90):
        x = rnd.uniform(0, W); y = rnd.uniform(1190, 1340)
        s += leaf(x, y, rnd.uniform(14, 26), rnd.uniform(0, 360), shade(rnd.choice(PAL), rnd.uniform(0.45, 0.7)), 0.9, False)
    return s

def birds(pts):
    return ''.join(f'<path d="M{x-14*s:.1f},{y-4*s:.1f} Q{x-6*s:.1f},{y-10*s:.1f} {x:.1f},{y:.1f} Q{x+6*s:.1f},{y-10*s:.1f} {x+14*s:.1f},{y-4*s:.1f}" stroke="#2A0E07" stroke-width="{2.4*s:.1f}" fill="none" stroke-linecap="round" opacity="0.75"/>' for x, y, s in pts)

def frame(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{defs()}{body}</svg>'

def base_sky(rnd, sun_xy=(540, 880), sun_r=620):
    return (f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
            f'<circle cx="{sun_xy[0]}" cy="{sun_xy[1]}" r="{sun_r}" fill="url(#sun)"/>' + rays() + bokeh(rnd, 26))

def finish():
    return (f'<rect width="{W}" height="{H}" fill="url(#vig)"/>'
            f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity="0.35"/>')

def slide1():
    rnd = random.Random(11)
    b = base_sky(rnd)
    b += birds([(700, 250, 2.0), (770, 215, 1.6), (820, 262, 1.4), (880, 232, 1.1), (330, 300, 1.2)])
    b += landscape(5, 0, cabin_at=800)
    b += tree(30, 560, 290, 240, 1130, 3, 15, 27)
    b += tree(1070, 700, 260, 215, 1160, 7, 15, 27)
    b += '<ellipse cx="540" cy="650" rx="470" ry="320" fill="url(#textbg)"/>'
    crowns = [(-280, 300, 340, 820), (790, 470, 1340, 930), (680, 980, 960, 1200)]
    avoid = [(170, 360, 910, 950), (380, 30, 700, 190)] + crowns
    b += falling(rnd, 30, [(170, 360, 910, 950), (380, 30, 700, 190)], (24, 60), keys=0, compound_n=4)
    b += falling(random.Random(7), 0, avoid, keys=6, region=(0, 40, W, 1180))
    b += falling(random.Random(99), 10, [(380, 30, 700, 190)], (12, 20), keys=0, region=(200, 400, 880, 900))
    return frame(b + finish())

def slide2():
    rnd = random.Random(21)
    b = base_sky(rnd, (540, 700), 560)
    b += landscape(15, 0)
    b += f'<ellipse cx="540" cy="290" rx="520" ry="150" fill="url(#textbg)"/>'
    b += tree(540, 640, 285, 215, 990, 13, 15, 27)
    rr = random.Random(5); P = []
    for side in (-1, 1):
        sx = lambda x: 540 + side * (x - 540)
        for (x, y, L) in ((810, 700, 34), (860, 752, 38), (896, 815, 42)):
            P.append(leaf(sx(x), y, L, rr.uniform(0, 360), rr.choice(PAL), 1, True))
        P.append(leaf(sx(918), 872, 46, 40 if side > 0 else 140, "#F2C14E", 0.5, True, 'b2'))
        P.append(key(sx(926), 892, 0.85, -40 if side > 0 else 220, 0.75))
        P.append(key(sx(942), 960, 1.25, -58 if side > 0 else 238))
    P.append(key(655, 986, 0.95, 8)); P.append(key(430, 990, 0.9, 186))
    b += ''.join(P)
    b += f'<ellipse cx="540" cy="1110" rx="600" ry="150" fill="url(#textbg)"/>'
    b += f'<ellipse cx="540" cy="1110" rx="480" ry="100" fill="url(#textbg)"/>'
    b += falling(rnd, 16, [(120, 180, 960, 1200), (380, 30, 700, 190)], (22, 50), keys=0, compound_n=2)
    return frame(b + finish())

def slide3():
    rnd = random.Random(31)
    b = base_sky(rnd, (540, 760), 600)
    b += landscape(25, 30, cabin_at=250)
    b += tree(-30, 960, 210, 180, 1265, 23, 14, 24)
    b += tree(1110, 930, 210, 185, 1265, 29, 14, 24)
    avoid = [(70, 330, 1010, 960), (380, 30, 700, 190)]
    b += falling(rnd, 26, avoid, (24, 56), keys=5, compound_n=3)
    return frame(b + finish())

out = sys.argv[1]
for name, fn in (("slide1", slide1), ("slide2", slide2), ("slide3", slide3)):
    open(f"{out}/{name}.svg", "w").write(fn())
print("ok")
