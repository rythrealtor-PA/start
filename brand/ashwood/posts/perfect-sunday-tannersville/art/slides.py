"""Renders 'The Perfect Sunday in …' carousels in Ryth's viral aesthetic-background style.

Each slide is HTML at 1080x1350 over a pre-darkened background photo.
Photo-frame areas are left empty on purpose: Ryth adds the small framed photos in Canva.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BG = os.path.join(HERE, '..', 'bg', 'out')

CSS = """
@font-face{font-family:'Cormorant Garamond';font-style:italic;font-weight:600;src:url('file:///tmp/claude-0/-home-user-start/3fa4be15-9cc7-5df8-89bc-f57fb09eeb27/scratchpad/sunday/fonts/CormorantGaramond-600i.ttf');}
@font-face{font-family:'Cormorant Garamond';font-style:normal;font-weight:600;src:url('file:///tmp/claude-0/-home-user-start/3fa4be15-9cc7-5df8-89bc-f57fb09eeb27/scratchpad/sunday/fonts/CormorantGaramond-600.ttf');}
@font-face{font-family:'Cormorant Garamond';font-style:normal;font-weight:700;src:url('file:///tmp/claude-0/-home-user-start/3fa4be15-9cc7-5df8-89bc-f57fb09eeb27/scratchpad/sunday/fonts/CormorantGaramond-700.ttf');}
@font-face{font-family:'Montserrat';font-style:normal;font-weight:500;src:url('file:///tmp/claude-0/-home-user-start/3fa4be15-9cc7-5df8-89bc-f57fb09eeb27/scratchpad/sunday/fonts/Montserrat-500.ttf');}
@font-face{font-family:'Montserrat';font-style:normal;font-weight:600;src:url('file:///tmp/claude-0/-home-user-start/3fa4be15-9cc7-5df8-89bc-f57fb09eeb27/scratchpad/sunday/fonts/Montserrat-600.ttf');}
@font-face{font-family:'Montserrat';font-style:normal;font-weight:700;src:url('file:///tmp/claude-0/-home-user-start/3fa4be15-9cc7-5df8-89bc-f57fb09eeb27/scratchpad/sunday/fonts/Montserrat-700.ttf');}
@font-face{font-family:'Montserrat';font-style:normal;font-weight:800;src:url('file:///tmp/claude-0/-home-user-start/3fa4be15-9cc7-5df8-89bc-f57fb09eeb27/scratchpad/sunday/fonts/Montserrat-800.ttf');}
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:1080px; height:1350px; overflow:hidden; background:#000; }
.slide { position:relative; width:1080px; height:1350px; background-size:cover; background-position:center; }
.serif { font-family:'Cormorant Garamond', Georgia, serif; font-weight:700; color:#F3F8FF; }
.emoji { font-family:'Noto Color Emoji'; font-weight:400; }
.cover { position:absolute; left:40px; right:40px; text-align:center; }
.cover .l1 { font-size:150px; line-height:.9; letter-spacing:-3px; font-weight:600; }
.cover .big { font-size:178px; line-height:.88; letter-spacing:-4px; }
.cover .sub { font-size:64px; line-height:1.1; font-weight:600; margin-top:26px; letter-spacing:-.5px; }
.cover .kick { font-family:'Montserrat'; font-weight:700; font-size:26px; letter-spacing:7px; color:#E9E2D0; margin-bottom:26px; }
.tbox { position:absolute; left:30px; top:30px; padding:6px 34px 16px; background:rgba(12,12,12,.74); border-radius:24px;
        font-size:124px; line-height:1.05; letter-spacing:-3px; white-space:nowrap; }
.lab { position:absolute; font-size:64px; line-height:1.24; letter-spacing:-.5px; }
.lab span.t { background:rgba(12,12,12,.70); padding:2px 18px 6px; border-radius:16px;
        -webkit-box-decoration-break:clone; box-decoration-break:clone; }
.right { text-align:right; }
.h5 { position:absolute; left:50px; right:50px; top:105px; text-align:center; font-size:104px; line-height:.95; letter-spacing:-2.5px; }
.row { position:absolute; left:70px; display:flex; align-items:center; gap:22px; }
.chk { width:104px; height:104px; border-radius:50%; background:#fff; display:flex; align-items:center; justify-content:center; flex:none; }
.rtxt { background:rgba(12,12,12,.72); border-radius:24px; padding:8px 30px 16px; font-size:70px; line-height:1.05; letter-spacing:-1px; white-space:nowrap; }
.close { position:absolute; left:60px; right:60px; text-align:center; font-size:76px; line-height:1.0; letter-spacing:-1.5px; font-weight:600; }
.credit { position:absolute; right:34px; bottom:22px; font-family:'Montserrat'; font-weight:600; font-size:19px; color:rgba(243,248,255,.72); letter-spacing:.3px; }
"""

CHECK = '<svg width="58" height="58" viewBox="0 0 24 24"><path d="M4.5 12.5l5 5L19.5 7" fill="none" stroke="#1b1b1b" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def emo(s):
    """Wrap emoji characters so they render with the color emoji font."""
    out = []
    for ch in s:
        cp = ord(ch)
        if cp >= 0x2190 and not (0x2000 <= cp <= 0x206F) and ch not in '–—’“”…·':
            out.append(f'<span class="emoji">{ch}</span>')
        else:
            out.append(ch)
    return ''.join(out)


def label(text, x, y, w, align='left'):
    side = f'left:{x}px;' if align == 'left' else f'right:{x}px;'
    cls = 'lab serif' + (' right' if align == 'right' else '')
    lines = '<br>'.join(f'<span class="t">{emo(t)}</span>' for t in text.split('\n'))
    return f'<div class="{cls}" style="{side}top:{y}px;width:{w}px">{lines}</div>'


def page(bg, inner):
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f'<body><div class="slide" style="background-image:url(\'file://{os.path.join(BG, bg)}\')">{inner}</div></body></html>')


def cover(bg, kick, l1, big, sub, top):
    big_html = '<br>'.join(big)
    return page(bg, f'<div class="cover serif" style="top:{top}px">'
                    f'<div class="kick">{kick}</div>'
                    f'<div class="l1">{l1}</div><div class="big">{big_html}</div><div class="sub">{sub}</div></div>')


def day(bg, title, labels):
    inner = f'<div class="tbox serif">{title}</div>' + ''.join(label(*l) for l in labels)
    return page(bg, inner)


def locals_slide(bg, heading, items, closing, credit):
    inner = f'<div class="h5 serif">{heading}</div>'
    for i, it in enumerate(items):
        inner += (f'<div class="row" style="top:{430 + i * 150}px"><div class="chk">{CHECK}</div>'
                  f'<div class="rtxt serif">{it}</div></div>')
    inner += f'<div class="close serif" style="top:900px">{closing}</div>'
    inner += f'<div class="credit">{credit}</div>'
    return page(bg, inner)


CREDIT = 'Ryth William · Realtor · Ashwood Real Estate · (570) 534-4404 · Equal Housing Opportunity'

SLIDES = {
    # ---------- Tannersville ----------
    'tann-1': cover('tann-1-cover-dark.jpg', 'POCONO MOUNTAINS', 'The Perfect<br>Sunday in',
                    ['Tannersville'], 'according to residents', 255),
    'tann-2': day('tann-2-morning-dark.jpg', '1.Sun Morning', [
        ('🍳 Brunch at The Morning\nToast inside Barley Creek', 60, 250, 760),
        ('🍺 The first Pocono\nmicrobrewery since\nProhibition (1995)', 90, 560, 640),
    ]),
    'tann-3': day('tann-3-afternoon-dark.jpg', '2.Sun Afternoon', [
        ('⛷️ Ski or snow tube at\nCamelback Mountain', 60, 250, 760),
        ('🛍️ Not a skier? Shop The\nCrossings Premium Outlets', 70, 520, 800, 'right'),
    ]),
    'tann-4': day('tann-4-night-dark.jpg', '3.Sun Night', [
        ('🥩 Dinner at the Legendary\nTannersville Inn', 70, 250, 820, 'right'),
        ('🕯️ A Pocono tradition\nsince 1825', 60, 540, 640),
    ]),
    'tann-5': locals_slide('tann-5-locals-dark.jpg', 'Why Locals Love<br>Tannersville?',
                           ['Ski slopes minutes away', 'Brunch, brews &amp; outlets', 'Mountain views daily'],
                           'Thinking of living in the<br>Poconos? Sundays here<br>feel different', CREDIT),
    # ---------- Jim Thorpe & Lehighton ----------
    'jt-1': cover('jt-1-cover-dark.jpg', 'POCONO MOUNTAINS', 'The Perfect<br>Sunday in',
                  ['Jim Thorpe', '&amp; Lehighton'], 'according to residents', 215),
    'jt-2': day('jt-2-morning-dark.jpg', '1.Sun Morning', [
        ('🍳 Breakfast at Broadway\nGrille, Inn at Jim Thorpe', 60, 250, 800),
        ('🏘️ Stroll Broadway &\nRace Street’s shops', 90, 560, 640),
    ]),
    'jt-3': day('jt-3-afternoon-dark.jpg', '2.Sun Afternoon', [
        ('🥾 Hike to Wild Creek Falls\nBeltzville State Park,\nLehighton', 60, 250, 800),
        ('💧 Short trail, big\nwaterfall', 70, 600, 640, 'right'),
    ]),
    'jt-4': day('jt-4-night-dark.jpg', '3.Sun Night', [
        ('🍷 Dinner at Moya\non Race Street', 70, 250, 700, 'right'),
        ('🍺 Nightcap at Molly\nMaguire’s Pub,\nHazard Square', 60, 520, 700),
    ]),
    'jt-5': locals_slide('jt-5-locals-dark.jpg', '<span style="font-size:88px">Why Locals Love<br>Jim Thorpe &amp; Lehighton?</span>',
                         ['Walkable Victorian downtown', 'Waterfalls &amp; state parks', 'Real small-town community'],
                         'Thinking of living in the<br>Poconos? Sundays here<br>feel different', CREDIT),
}

if __name__ == '__main__':
    for name, html in SLIDES.items():
        with open(os.path.join(HERE, f'{name}.html'), 'w') as f:
            f.write(html)
    print(' '.join(SLIDES))
