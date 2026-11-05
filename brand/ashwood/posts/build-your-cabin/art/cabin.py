import math, random
W, H = 1080, 1350

def pine(x, y, h, col, snow=False, w=None):
    w = w or h * 0.42
    s = ''
    tiers = 4
    for i in range(tiers):
        ty = y - h + i * h * 0.2
        tw = w * (0.45 + 0.55 * (i + 1) / tiers)
        by = ty + h * 0.38
        s += f'<path d="M{x:.1f},{ty:.1f} L{x+tw/2:.1f},{by:.1f} L{x-tw/2:.1f},{by:.1f} Z" fill="{col}"/>'
        if snow:
            s += f'<path d="M{x:.1f},{ty:.1f} L{x+tw*0.22:.1f},{ty+h*0.12:.1f} L{x:.1f},{ty+h*0.09:.1f} L{x-tw*0.22:.1f},{ty+h*0.12:.1f} Z" fill="#EAF2FA"/>'
    s += f'<rect x="{x-h*0.03:.1f}" y="{y-h*0.08:.1f}" width="{h*0.06:.1f}" height="{h*0.1:.1f}" fill="#2a1a10"/>'
    return s

def lights(x0, y0, x1, y1, sag, n, glow='#FFD27A'):
    s = f'<path d="M{x0},{y0} Q{(x0+x1)/2},{max(y0,y1)+sag*2} {x1},{y1}" stroke="#1a1410" stroke-width="3" fill="none"/>'
    for i in range(1, n):
        t = i / n
        x = (1-t)**2*x0 + 2*(1-t)*t*(x0+x1)/2 + t*t*x1
        y = (1-t)**2*y0 + 2*(1-t)*t*(max(y0,y1)+sag*2) + t*t*y1
        s += f'<circle cx="{x:.1f}" cy="{y+12:.1f}" r="22" fill="{glow}" opacity="0.28" filter="url(#g8)"/>'
        s += f'<ellipse cx="{x:.1f}" cy="{y+12:.1f}" rx="7" ry="10" fill="{glow}"/>'
        s += f'<rect x="{x-4:.1f}" y="{y-1:.1f}" width="8" height="6" fill="#2a2a2a"/>'
    return s

DEFS = ('<defs>'
 '<filter id="g8" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="8"/></filter>'
 '<filter id="g3" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3"/></filter>'
 '<filter id="g20" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="20"/></filter>'
 '<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="7"/><feColorMatrix values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.35 0"/></filter>'
 '</defs>')

def forest_bg(cover=False):
    rnd = random.Random(4)
    s = (f'<linearGradient id="nb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#10302A"/><stop offset="0.55" stop-color="#0C241E"/><stop offset="1" stop-color="#071611"/></linearGradient>'
         f'<radialGradient id="warm" cx="0.5" cy="0.55" r="0.6"><stop offset="0" stop-color="#F4B860" stop-opacity="0.16"/><stop offset="1" stop-color="#F4B860" stop-opacity="0"/></radialGradient>')
    b = f'<defs>{s}</defs><rect width="{W}" height="{H}" fill="url(#nb)"/><rect width="{W}" height="{H}" fill="url(#warm)"/>'
    for _ in range(70):
        b += f'<circle cx="{rnd.uniform(0,W):.0f}" cy="{rnd.uniform(0,420):.0f}" r="{rnd.uniform(0.8,2.2):.1f}" fill="#FFF6DA" opacity="{rnd.uniform(0.25,0.8):.2f}"/>'
    # far forest
    for x in range(-40, W + 60, 46):
        b += pine(x + rnd.uniform(-10,10), 1265 + rnd.uniform(-20,10), rnd.uniform(180, 260), "#0B2219")
    for x in range(-60, W + 80, 70):
        b += pine(x + rnd.uniform(-15,15), 1300 + rnd.uniform(-10,10), rnd.uniform(240, 330), "#06150F")
    # tall framing pines
    for x, h in ((-30, 900), (60, 640), (1110, 940), (1010, 620)):
        b += pine(x, 1300, h, "#05120D", w=h*0.36)
    b += lights(-30, -8, 1110, -8, 26, 16)
    for _ in range(32):
        x, y = rnd.uniform(60, W-60), rnd.uniform(420, 1180)
        r = rnd.uniform(2, 4.5)
        b += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r*4:.1f}" fill="#FFE38A" opacity="{rnd.uniform(0.15,0.3):.2f}" filter="url(#g3)"/><circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#FFF1B0" opacity="{rnd.uniform(0.6,0.95):.2f}"/>'
    if cover:
        c = "#F3E6CC"
        st = f'stroke="{c}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"'
        dash = f'stroke="{c}" stroke-width="3" fill="none" stroke-dasharray="14 12" opacity="0.7"'
        g = '<g transform="translate(540,0)" opacity="0.92">'
        g += f'<path d="M-230,1120 L-230,880 L0,700 L230,880 L230,1120 Z" {st}/>'
        g += f'<path d="M-270,905 L0,675 L270,905" {st}/>'
        g += f'<rect x="110" y="740" width="50" height="95" {st}/>'
        g += f'<rect x="-50" y="1000" width="100" height="120" {st}/>'
        g += f'<rect x="-175" y="930" width="95" height="85" {st}/><rect x="80" y="930" width="95" height="85" {st}/>'
        g += f'<path d="M-175,972 L-80,972 M-127,930 L-127,1015 M80,972 L175,972 M127,930 L127,1015" {st} stroke-width="3"/>'
        g += f'<path d="M-300,1150 L300,1150" {dash}/><path d="M-300,1135 L-300,1165 M300,1135 L300,1165" stroke="{c}" stroke-width="3"/>'
        g += f'<path d="M-330,700 L-330,1120" {dash}/>'
        g += f'<text x="0" y="1210" fill="{c}" font-family="Georgia, serif" font-size="30" text-anchor="middle" opacity="0.8" font-style="italic">your cabin, your way</text>'
        g += f'<text x="0" y="905" fill="#FFC56B" font-family="Georgia, serif" font-size="120" font-weight="bold" text-anchor="middle">?</text>'
        g += '</g>'
        b += g
    b += f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity="0.25"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}{b}</svg>'

# ---------- option illustrations 872 x 1060 ----------
IW, IH = 872, 1060
def frame(body, defs=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{IW}" height="{IH}" viewBox="0 0 {IW} {IH}">{DEFS}<defs>{defs}'
            f'<clipPath id="rc"><rect width="{IW}" height="{IH}" rx="40"/></clipPath></defs><g clip-path="url(#rc)">{body}'
            f'<rect width="{IW}" height="{IH}" filter="url(#grain)" opacity="0.18"/></g></svg>')

def dusk(id_, top, bot):
    return f'<linearGradient id="{id_}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient>'

def hills_row(rnd, y, col, n=20, hmin=120, hmax=220, snow=False):
    s = ''
    for i in range(n):
        x = -40 + i * (IW + 80) / n + rnd.uniform(-12, 12)
        s += pine(x, y + rnd.uniform(-10, 10), rnd.uniform(hmin, hmax), col, snow)
    return s

def log_cabin():
    rnd = random.Random(1)
    d = dusk('sk', '#1F3B63', '#F0A35E')
    b = f'<rect width="{IW}" height="{IH}" fill="url(#sk)"/>'
    b += '<circle cx="660" cy="430" r="70" fill="#FFD9A0" opacity="0.5" filter="url(#g20)"/>'
    b += hills_row(rnd, 640, '#2B3F3A', 22, 140, 230)
    b += f'<rect y="610" width="{IW}" height="{IH-610}" fill="#2E4128"/>'
    b += '<path d="M300,1060 Q400,930 436,850 L476,850 Q470,930 580,1060 Z" fill="#6E6150" opacity="0.8"/>'
    # cabin
    x0, x1, yt, yb = 176, 696, 560, 850
    logs = ''
    y = yt; i = 0
    while y < yb:
        col = '#8B5A2B' if i % 2 == 0 else '#7A4D24'
        logs += f'<rect x="{x0}" y="{y}" width="{x1-x0}" height="30" rx="13" fill="{col}"/><path d="M{x0+10},{y+27} L{x1-10},{y+27}" stroke="#5B3818" stroke-width="3"/>'
        logs += f'<circle cx="{x0-6}" cy="{y+15}" r="15" fill="#B07D4A"/><circle cx="{x0-6}" cy="{y+15}" r="8" fill="none" stroke="#7A4D24" stroke-width="2"/>'
        logs += f'<circle cx="{x1+6}" cy="{y+15}" r="15" fill="#B07D4A"/><circle cx="{x1+6}" cy="{y+15}" r="8" fill="none" stroke="#7A4D24" stroke-width="2"/>'
        y += 30; i += 1
    b += logs
    b += f'<path d="M{x0-50},{yt+10} L436,380 L{x1+50},{yt+10} L{x1+50},{yt+40} L436,410 L{x0-50},{yt+40} Z" fill="#3A2618"/>'
    b += f'<path d="M{x0-30},{yt+30} L436,404 L{x1+30},{yt+30} L436,404 Z" fill="#2A1A10"/>'
    b += f'<path d="M{x0+20},{yt+5} L436,420 L{x1-20},{yt+5} Z" fill="#8B5A2B"/>'
    b += '<path d="M396,500 L476,500 L476,545 L396,545 Z" fill="#FFC56B"/><path d="M436,500 L436,545 M396,522 L476,522" stroke="#5B3818" stroke-width="4"/>'
    # chimney + smoke
    b += '<rect x="560" y="380" width="62" height="160" fill="#7D7468"/>'
    for yy in range(392, 540, 26):
        b += f'<path d="M560,{yy} L622,{yy}" stroke="#5E574D" stroke-width="3"/>'
    for i, (cx, cy, r) in enumerate([(600, 350, 18), (615, 312, 24), (640, 268, 30), (670, 220, 36)]):
        b += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#E8E2DA" opacity="{0.45 - i*0.08:.2f}" filter="url(#g3)"/>'
    # windows + door
    for wx in (230, 532):
        b += f'<rect x="{wx}" y="640" width="110" height="95" fill="#FFC56B"/><rect x="{wx}" y="640" width="110" height="95" fill="none" stroke="#4A2E16" stroke-width="8"/>'
        b += f'<path d="M{wx+55},640 L{wx+55},735 M{wx},687 L{wx+110},687" stroke="#4A2E16" stroke-width="6"/>'
        b += f'<ellipse cx="{wx+55}" cy="690" rx="90" ry="70" fill="#FFB347" opacity="0.18" filter="url(#g20)"/>'
    b += '<rect x="391" y="680" width="90" height="170" rx="6" fill="#5A361A"/><circle cx="465" cy="770" r="6" fill="#E3B266"/>'
    # porch
    b += f'<rect x="{x0-40}" y="850" width="{x1-x0+80}" height="34" fill="#5C3A1E"/>'
    for px in (x0-30, 436, x1+20):
        b += f'<rect x="{px}" y="600" width="14" height="250" fill="#4A2E16"/>'
    for cx in (290, 600):
        b += f'<path d="M{cx-35},850 L{cx-30},780 L{cx+30},780 L{cx+35},850" stroke="#2A1A10" stroke-width="8" fill="none"/><path d="M{cx-30},780 L{cx-40},730 M{cx+30},780 L{cx+20},730 M{cx-40},730 L{cx+20},730" stroke="#2A1A10" stroke-width="8"/>'
        b += f'<path d="M{cx-50},858 Q{cx},876 {cx+50},858" stroke="#2A1A10" stroke-width="7" fill="none"/>'
    b += pine(70, 900, 520, '#1C2E22') + pine(800, 920, 560, '#1C2E22') + pine(-10, 1000, 380, '#152419')
    return frame(b, d)

def aframe():
    rnd = random.Random(2)
    d = dusk('sk', '#1B2C4E', '#E9955A') + '<linearGradient id="gl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE2A8"/><stop offset="1" stop-color="#F29A44"/></linearGradient>'
    b = f'<rect width="{IW}" height="{IH}" fill="url(#sk)"/>'
    b += hills_row(rnd, 650, '#24353A', 22, 150, 240)
    b += f'<rect y="620" width="{IW}" height="{IH-620}" fill="#26381F"/>'
    b += '<ellipse cx="436" cy="760" rx="380" ry="200" fill="#FFB347" opacity="0.22" filter="url(#g20)"/>'
    b += '<path d="M156,880 L436,250 L716,880 Z" fill="#141414"/>'
    b += '<path d="M226,870 L436,368 L646,870 Z" fill="url(#gl)"/>'
    for y in (520, 680):
        t = (y - 368) / (870 - 368)
        hw = 210 * t
        b += f'<path d="M{436-hw:.0f},{y} L{436+hw:.0f},{y}" stroke="#141414" stroke-width="8"/>'
    b += '<path d="M436,368 L436,870 M330,620 L330,870 M542,620 L542,870" stroke="#141414" stroke-width="8"/>'
    b += '<path d="M436,440 L436,500" stroke="#3A2A1A" stroke-width="3"/><circle cx="436" cy="510" r="14" fill="#FFF3D0"/>'
    b += '<path d="M300,860 L380,860 L380,800 Q340,780 300,800 Z" fill="#7A4A2A" opacity="0.6"/>'
    b += '<rect x="120" y="870" width="632" height="30" fill="#5C3A1E"/>'
    for x in range(130, 760, 40):
        b += f'<rect x="{x}" y="830" width="8" height="40" fill="#3E2614"/>'
    b += '<rect x="120" y="826" width="632" height="10" fill="#3E2614"/>'
    b += pine(70, 930, 560, '#152419') + pine(820, 940, 600, '#152419') + pine(740, 1010, 360, '#0F1B12')
    return frame(b, d)

def hottub():
    rnd = random.Random(3)
    d = dusk('sk', '#0E1A36', '#2C4A75') + '<radialGradient id="wt" cx="0.5" cy="0.4" r="0.6"><stop offset="0" stop-color="#8FF3F0"/><stop offset="1" stop-color="#1A8FA6"/></radialGradient>'
    b = f'<rect width="{IW}" height="{IH}" fill="url(#sk)"/>'
    for _ in range(60):
        b += f'<circle cx="{rnd.uniform(0,IW):.0f}" cy="{rnd.uniform(0,420):.0f}" r="{rnd.uniform(0.8,2.2):.1f}" fill="#fff" opacity="{rnd.uniform(0.3,0.9):.2f}"/>'
    b += hills_row(rnd, 560, '#16302A', 16, 200, 300, True)
    b += f'<rect y="540" width="{IW}" height="200" fill="#D6E3F0"/>'
    b += hills_row(random.Random(9), 660, '#10261F', 9, 260, 360, True)
    b += lights(-20, 90, IW + 20, 90, 50, 11)
    b += '<path d="M0,700 L872,700 L872,1060 L0,1060 Z" fill="#6E4A2A"/>'
    for y in range(720, 1060, 40):
        b += f'<path d="M0,{y} L872,{y}" stroke="#4E321B" stroke-width="4"/>'
    b += '<ellipse cx="436" cy="820" rx="330" ry="130" fill="#4A2E18"/><ellipse cx="436" cy="805" rx="330" ry="125" fill="#6B4425"/>'
    b += '<ellipse cx="436" cy="800" rx="290" ry="100" fill="url(#wt)"/>'
    b += '<ellipse cx="436" cy="800" rx="300" ry="120" fill="#7FF0F0" opacity="0.25" filter="url(#g20)"/>'
    for i in range(5):
        x = 300 + i * 70
        b += f'<path d="M{x},760 C{x-30},700 {x+30},660 {x},600 C{x-30},550 {x+20},520 {x},480" stroke="#FFFFFF" stroke-width="18" fill="none" opacity="0.22" filter="url(#g8)"/>'
    for i in range(8):
        b += f'<circle cx="{330+i*30}" cy="{800+ (i%3)*10}" r="5" fill="#E8FFFF" opacity="0.6"/>'
    b += '<rect x="690" y="760" width="120" height="16" rx="8" fill="#F2F2F2"/><rect x="700" y="740" width="100" height="22" rx="8" fill="#C9D6E3"/>'
    return frame(b, d)

def firepit():
    rnd = random.Random(5)
    d = dusk('sk', '#081127', '#1A2747') + '<radialGradient id="fg" cx="0.5" cy="0.7" r="0.55"><stop offset="0" stop-color="#FF9A3C" stop-opacity="0.55"/><stop offset="1" stop-color="#FF9A3C" stop-opacity="0"/></radialGradient>'
    b = f'<rect width="{IW}" height="{IH}" fill="url(#sk)"/>'
    for _ in range(90):
        b += f'<circle cx="{rnd.uniform(0,IW):.0f}" cy="{rnd.uniform(0,520):.0f}" r="{rnd.uniform(0.8,2.4):.1f}" fill="#fff" opacity="{rnd.uniform(0.3,0.95):.2f}"/>'
    b += hills_row(rnd, 640, '#0F1D17', 14, 260, 380)
    b += f'<rect y="620" width="{IW}" height="{IH-620}" fill="#1B2617"/>'
    b += f'<rect width="{IW}" height="{IH}" fill="url(#fg)"/>'
    for x, h in ((40, 1000), (840, 980)):
        b += f'<rect x="{x-22}" y="0" width="44" height="{h}" fill="#0B0F0A"/>'
    # stones
    for i in range(16):
        a = i / 16 * math.tau
        x = 436 + math.cos(a) * 170; y = 830 + math.sin(a) * 60
        b += f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="42" ry="28" fill="#6E655C"/><ellipse cx="{x:.0f}" cy="{y-8:.0f}" rx="30" ry="12" fill="#E39A5A" opacity="0.5"/>'
    b += '<ellipse cx="436" cy="830" rx="140" ry="44" fill="#2A1A10"/>'
    for (w, h, col) in ((150, 330, '#FF6A1A'), (110, 270, '#FF9A2E'), (70, 200, '#FFD35A'), (34, 130, '#FFF2B0')):
        b += f'<path d="M{436-w},830 C{436-w},{830-h*0.5} {436-w*0.3},{830-h*0.6} {436},{830-h} C{436+w*0.3},{830-h*0.6} {436+w},{830-h*0.5} {436+w},830 Z" fill="{col}"/>'
    b += '<ellipse cx="436" cy="700" rx="260" ry="220" fill="#FF8A2A" opacity="0.25" filter="url(#g20)"/>'
    for _ in range(26):
        b += f'<circle cx="{436 + rnd.uniform(-120,120):.0f}" cy="{rnd.uniform(260,520):.0f}" r="{rnd.uniform(2,4):.1f}" fill="#FFD27A" opacity="{rnd.uniform(0.5,1):.2f}"/>'
    for side in (-1, 1):
        cx = 436 + side * 330
        b += f'<g transform="translate({cx},880) scale({side},1)">'
        b += '<path d="M-60,100 L-40,-40 M40,100 L60,-10 M-70,20 L80,20" stroke="#1A100A" stroke-width="16" stroke-linecap="round"/>'
        b += '<path d="M-60,-120 L-30,-120 L-20,10 L-50,10 Z M-20,-130 L10,-130 L10,10 L-20,10 Z M15,-120 L45,-120 L40,10 L12,10 Z" fill="#2A1A10"/>'
        b += '<path d="M-60,-120 L45,-120" stroke="#E07A3A" stroke-width="4" opacity="0.6"/></g>'
    b += '<path d="M600,700 L470,620" stroke="#5A3A1E" stroke-width="6" stroke-linecap="round"/><ellipse cx="466" cy="616" rx="12" ry="9" fill="#FFF6E6"/>'
    return frame(b, d)

def railing(col='#4A2E16'):
    s = f'<rect y="880" width="{IW}" height="180" fill="#6E4A2A"/>'
    for y in range(900, 1060, 36):
        s += f'<path d="M0,{y} L{IW},{y}" stroke="#4E321B" stroke-width="4"/>'
    s += f'<rect y="720" width="{IW}" height="22" fill="{col}"/><rect y="860" width="{IW}" height="20" fill="{col}"/>'
    for x in range(20, IW, 70):
        s += f'<rect x="{x}" y="742" width="16" height="118" fill="{col}"/>'
    return s

def lakeview():
    rnd = random.Random(6)
    d = (dusk('sk', '#8DB4D6', '#F7C98E') + '<linearGradient id="lk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E9C49A"/><stop offset="0.4" stop-color="#8FB3C7"/><stop offset="1" stop-color="#3F6F87"/></linearGradient>')
    b = f'<rect width="{IW}" height="{IH}" fill="url(#sk)"/>'
    b += '<circle cx="520" cy="420" r="55" fill="#FFE6B0"/><circle cx="520" cy="420" r="120" fill="#FFE6B0" opacity="0.35" filter="url(#g20)"/>'
    b += '<path d="M0,430 C150,330 260,360 380,400 C520,330 680,320 872,410 L872,470 L0,470 Z" fill="#7C8FA0" opacity="0.7"/>'
    b += hills_row(rnd, 480, '#3D5A4B', 26, 70, 120)
    b += f'<rect y="470" width="{IW}" height="420" fill="url(#lk)"/>'
    for i in range(10):
        y = 490 + i * 22
        b += f'<path d="M{500 - 40 + rnd.uniform(-20,20):.0f},{y} L{540 + rnd.uniform(-20,20):.0f},{y}" stroke="#FFE6B0" stroke-width="5" opacity="{0.8 - i*0.06:.2f}"/>'
    b += '<rect y="470" width="872" height="60" fill="#FFFFFF" opacity="0.25" filter="url(#g8)"/>'
    b += '<path d="M600,700 L872,640 L872,700 L640,740 Z" fill="#8B5E34"/>'
    for x in range(620, 872, 30):
        b += f'<path d="M{x},{705 - (x-600)*0.22:.0f} L{x+10},{745 - (x-600)*0.22:.0f}" stroke="#5C3A1E" stroke-width="3"/>'
    b += '<path d="M640,690 Q720,650 800,660 Q760,690 660,700 Z" fill="#C0392B"/>'
    b += pine(40, 620, 420, '#22362B') + pine(830, 560, 300, '#22362B')
    b += railing()
    return frame(b, d)

def mountainview():
    d = dusk('sk', '#7EA6D2', '#F6B26B')
    b = f'<rect width="{IW}" height="{IH}" fill="url(#sk)"/>'
    b += '<circle cx="300" cy="360" r="50" fill="#FFE2A8"/><circle cx="300" cy="360" r="130" fill="#FFE2A8" opacity="0.35" filter="url(#g20)"/>'
    layers = [(420, '#A7AEBF', 40), (500, '#D98B4A', 55), (580, '#B8552E', 60), (660, '#7A3320', 55), (740, '#4A2418', 50)]
    rnd = random.Random(8)
    for base, col, amp in layers:
        pts = [(x, base + amp * math.sin(x / 140 + rnd.uniform(0, 6)) + rnd.uniform(-8, 8)) for x in range(-20, IW + 40, 40)]
        dpath = f"M-20,{IH} " + " ".join(f"L{x},{y:.0f}" for x, y in pts) + f" L{IW+40},{IH} Z"
        b += f'<path d="{dpath}" fill="{col}"/>'
        if base >= 580:
            for x, y in pts[::1]:
                b += f'<circle cx="{x + rnd.uniform(-10,10):.0f}" cy="{y + 8:.0f}" r="{rnd.uniform(10,18):.0f}" fill="{col}"/>'
    b += railing()
    return frame(b, d)

out = {'cabin-bg-cover': forest_bg(True), 'cabin-bg': forest_bg(False), 'opt-logcabin': log_cabin(), 'opt-aframe': aframe(),
       'opt-hottub': hottub(), 'opt-firepit': firepit(), 'opt-lake': lakeview(), 'opt-mountain': mountainview()}
for k, v in out.items():
    open(f'{k}.svg', 'w').write(v)
print('ok')
