# Planazo pitch · original score (CC0 samples only) + soft UI foley, fitted to the picture timeline.
# Run from the library root:  .venv/bin/python <project>/tools/music.py <project>
import sys, json, os
import numpy as np, soundfile as sf
sys.path.insert(0, '.')
from core.audio import sampler as S
from core.audio.sfx import SR, add, limit, lp, hp, bp, click, whoosh, compress

P = sys.argv[1]
TL = json.load(open(os.path.join(P, 'tmp/tl.json')))
B1, B1o = TL['warp']['b1'], TL['warp']['b1o']
unwarp = lambda d: d * B1o / B1 if d < B1 else d + (B1o - B1)
DUR = TL['DUR'] + (B1o - B1)          # 96.0 s
S.seed(7)

BEAT = 0.6                              # 100 BPM
G0 = 16.6                               # bar 0 = logo downbeat
def b(bar, beat=0.0): return G0 + (bar * 4 + beat) * BEAT

stems = {k: [] for k in ['keys', 'guitar', 'bass', 'perc', 'color', 'strings']}
def ev(stem, t, inst, pitch, dur, vel, pan=0.0, gain=1.0, **kw):
    stems[stem].append(dict(t=t, inst=inst, pitch=pitch, dur=dur, vel=vel, pan=pan, gain=gain, **kw))

CH = {  # voicings (keys) and bass roots
    'Dmaj9': (['D3', 'A3', 'C#4', 'E4', 'F#4'], 'D2'), 'Bm9': (['B2', 'F#3', 'A3', 'C#4', 'D4'], 'B1'),
    'Gmaj9': (['G2', 'D3', 'F#3', 'A3', 'B3'], 'G1'), 'Gmaj7': (['G2', 'D3', 'F#3', 'B3'], 'G1'),
    'A7sus4': (['A2', 'E3', 'G3', 'D4'], 'A1'), 'A6': (['A2', 'E3', 'F#3', 'C#4'], 'A1'),
    'Em9': (['E3', 'B3', 'D4', 'F#4', 'G4'], 'E2'), 'F#m7': (['F#2', 'C#3', 'E3', 'A3'], 'F#1'),
    'Bm7': (['B2', 'F#3', 'A3', 'D4'], 'B1'), 'A/C#': (['C#3', 'E3', 'A3', 'C#4'], 'C#2'),
    'Dmaj7': (['D3', 'A3', 'C#4', 'F#4'], 'D2'), 'A/G': (['G2', 'E3', 'A3', 'C#4'], 'G1'),
}
def chord(t, name, dur, vel, inst='upright', strum=0.018, stem='keys'):
    for i, p in enumerate(CH[name][0]): ev(stem, t + i * strum, inst, p, dur, vel * (0.92 + 0.08 * (i % 2)), pan=-0.15 + 0.08 * i)
def bassn(t, p, dur, vel=.55): ev('bass', t, 'jazz_bass', p, dur, vel, 0.0)

# ---------- 0 – 16.6  intro: tired → recharge ----------
for t, name in [(0.25, 'Bm9'), (3.45, 'Gmaj7'), (6.65, 'Em9'), (9.85, 'A7sus4')]:
    chord(t, name, 3.4, .30, strum=0.05)
for t, p in [(1.85, 'F#5'), (5.05, 'E5'), (8.25, 'D5'), (11.45, 'C#5')]:
    ev('keys', t, 'upright', p, 1.6, .26, .2)
for t, p in [(0.0, 'B3'), (0.0, 'D4'), (6.4, 'B3'), (6.4, 'E4')]:
    ev('strings', t, 'violins', p, 6.2, .18, -.2 if p[0] == 'B' else .2, attack=1.2, release=1.2)
# recharge (battery fills ~12.7–15.4 out): rising arpeggio + strings swell + cymbal crescendo
arp = ['D4', 'F#4', 'A4', 'C#5', 'E5', 'F#5', 'A5', 'C#6']
for i in range(16):
    t = 12.75 + i * 0.24
    if t > 16.45: break
    ev('keys', t, 'upright', arp[i % 8] if i < 8 else arp[min(7, i - 8 + 2)], .5, .22 + .022 * i, .25 - .03 * (i % 4))
for p in ['A3', 'D4', 'F#4']:
    ev('strings', 12.6, 'violins', p, 4.1, .30, 0.0, attack=2.6, release=.4)
ev('color', 13.9, 'sus_cymbal', 'roll', 2.7, .32, 0.0, attack=2.2, release=.15)

# ---------- bar 0–1 (16.6–21.4): logo / brand ----------
chord(b(0), 'Dmaj9', 2.3, .58, strum=.01)
for i, p in enumerate(['D6', 'F#6', 'A6', 'D7']): ev('color', b(0) + .08 + i * .09, 'glockenspiel', p, 1.6, .42 - .04 * i, .3 - .2 * i)
ev('color', b(0), 'hand_chimes', 'A5', 2.5, .4, -.3)
ev('color', b(0), 'triangle', 'open', 2.0, .3, .4)
chord(b(1), 'Bm9', 2.3, .44)
for bar in (0, 1):
    root = CH['Dmaj9' if bar == 0 else 'Bm9'][1]
    bassn(b(bar), root, 1.1); bassn(b(bar, 2.5), root, .5, .45); bassn(b(bar, 3), root[:-1] + str(int(root[-1]) + 1), .5, .4)

# ---------- groove helpers ----------
def groove(bar, level=1.0, claps=False, hats=False):
    t0 = b(bar)
    ev('perc', t0, 'cajon', 'bass', None, .62 * level, 0)
    ev('perc', t0 + 1.5 * BEAT, 'cajon', 'bass', None, .45 * level, 0)
    ev('perc', t0 + 2 * BEAT, 'cajon', 'slap', None, .42 * level, .05)
    ev('perc', t0 + 3.5 * BEAT, 'cajon', 'tone', None, .30 * level, -.05)
    for k in range(8):
        ev('perc', t0 + k * BEAT / 2, 'shaker', 'down' if k % 2 == 0 else 'up', None, (.30 if k % 2 == 0 else .2) * level, .35)
    if claps:
        for k in (1, 3): ev('perc', t0 + k * BEAT, 'claps', 'group', None, .32 * level, -.1)
    if hats:
        for k in range(8): ev('perc', t0 + k * BEAT / 2 + .3 * 0, 'hihat', 'closed', None, .14 * level, -.3)
def comp(bar, name, vel=.40, half=False):
    t0 = b(bar)
    chord(t0, name, 1.0, vel, strum=.012)
    chord(t0 + 1.5 * BEAT, name, .5, vel * .78, strum=.01)
    if not half: chord(t0 + 3 * BEAT, name, .55, vel * .7, strum=.01)
def guitar_arp(bar, name, vel=.34, beats=4):
    notes = CH[name][0]; ns = [notes[0], notes[1 % len(notes)], notes[2 % len(notes)], notes[-1]]
    pat = [0, 2, 1, 3, 2, 1, 3, 2]
    for k in range(int(beats * 2)):
        n = ns[pat[k % 8]]; n = n[:-1] + str(int(n[-1]) + 1)
        ev('guitar', b(bar) + k * BEAT / 2, 'guitar_nylon', n, .9, vel * (1.0 if k % 2 == 0 else .82), .3)
def bassline(bar, name, vel=.55, busy=True):
    r = CH[name][1]; up = r[:-1] + str(int(r[-1]) + 1)
    bassn(b(bar), r, 1.0, vel)
    if busy: bassn(b(bar, 1.5), r, .4, vel * .75); bassn(b(bar, 2), up if 'm' not in name else r, .5, vel * .8)
    bassn(b(bar, 3), r, .45, vel * .8); bassn(b(bar, 3.5), up, .3, vel * .7)

# bars 0–1: light groove under the logo
for bar in (0, 1): groove(bar, .65)

# ---------- bars 2–4 (21.4–28.6): indecision ----------
for bar, name in [(2, 'Gmaj7'), (3, 'A7sus4')]:
    chord(b(bar), name, 2.2, .36); bassn(b(bar), CH[name][1], 1.2, .45)
chord(b(4), 'F#m7', 1.1, .34); chord(b(4, 2), 'Bm7', 1.1, .36); bassn(b(4), 'F#1', .9, .45); bassn(b(4, 2), 'B1', .9, .45)
pizz = [('E5', 0), ('C#5', .5), ('E5', 1), ('D5', 1.75), ('E5', 2.5), ('C#5', 3), ('B4', 3.5)]
for bar in (2, 3, 4):
    for p, bt in pizz:
        if bar == 4 and bt >= 3: continue
        ev('strings', b(bar, bt), 'violins_pizz', p, .4, .40, .25)
    for k in range(8): ev('perc', b(bar) + k * BEAT / 2, 'shaker', 'down' if k % 2 == 0 else 'up', None, .2, .35)
# pickup into the solution
for i, p in enumerate(['A4', 'B4', 'C#5', 'E5']): ev('color', b(4, 3) + i * .15, 'marimba', p, .4, .38, .2)

# ---------- bars 5–14 (28.6–52.6): the app works (demo groove) ----------
loop = ['Dmaj7', 'Bm7', 'Gmaj9', 'A7sus4']
for bar in range(5, 15):
    name = loop[(bar - 5) % 4]
    groove(bar, .85 if bar < 7 else 1.0, hats=bar >= 9)
    guitar_arp(bar, name, .30 if bar < 7 else .34)
    chord(b(bar), name, 2.2, .26, strum=.02)
    bassline(bar, name, .52)
for bar in (5, 9, 13):
    for i, p in enumerate(['D5', 'E5', 'F#5', 'A5']): ev('color', b(bar) + i * .3, 'marimba', p, .5, .30, -.25)

# ---------- bars 15–18 (52.6–62.2): youth, enjoying ----------
yl = ['Dmaj9', 'A/C#', 'Bm7', 'Gmaj9']
for bar in range(15, 19):
    name = yl[bar - 15]
    groove(bar, 1.0, claps=True, hats=True); guitar_arp(bar, name, .34); comp(bar, name, .30); bassline(bar, name, .55)
for i, p in enumerate(['A5', 'D6', 'F#6']): ev('color', b(15) + i * .12, 'glockenspiel', p, 1.2, .3, .3)

# ---------- bars 19–25 (62.2–79.0): pricing ----------
pl = ['Gmaj7', 'A6', 'F#m7', 'Bm7', 'Gmaj9', 'A7sus4', 'A6']
for bar in range(19, 26):
    name = pl[bar - 19]
    groove(bar, .9 if bar < 25 else .7, hats=bar < 25)
    guitar_arp(bar, name, .30)
    for k in (0, 2.5): ev('color', b(bar, k), 'vibraphone', CH[name][0][-1], 1.2, .26, -.3)
    chord(b(bar), name, 2.2, .24, strum=.02)
    bassline(bar, name, .5, busy=bar < 25)
# price reveal "S/ 9,90" (design 67.8) and checklist ticks (design 69.7 / 70.9 / 71.9)
tp = unwarp(67.8)
for i, p in enumerate(['A6', 'D7']): ev('color', tp + i * .07, 'glockenspiel', p, 1.4, .38, .2)
for d, p in [(69.7, 'A5'), (70.9, 'B5'), (71.9, 'D6')]: ev('color', unwarp(d), 'marimba', p, .5, .34, .3)

# ---------- bars 26–27 (79.0–83.8): headline breakdown ----------
for bt, name in [(0, 'Gmaj9'), (2, 'A6'), (4, 'F#m7'), (6, 'Bm9')]:
    chord(b(26, bt), name, 1.3, .36, strum=.03); bassn(b(26, bt), CH[name][1], 1.2, .38)
    ev('color', b(26, bt), 'vibraphone', CH[name][0][-1].replace('3', '4').replace('2', '4'), 1.3, .22, .3)
for p in ['B3', 'D4', 'F#4']: ev('strings', b(26), 'violins', p, 4.6, .28, 0.0, attack=1.0, release=1.0)
for i, p in enumerate(['F#5', 'E5', 'D5', 'A5']): ev('keys', b(26, 1 + i * 2), 'upright', p, 1.2, .30, .2)
# bar 28 (83.8–86.2): build back
chord(b(28), 'Gmaj7', 1.2, .32); chord(b(28, 2), 'A7sus4', 1.2, .34)
bassn(b(28), 'G1', 1.0, .45); bassn(b(28, 2), 'A1', 1.0, .48)
for k in range(8): ev('perc', b(28) + k * BEAT / 2, 'shaker', 'down' if k % 2 == 0 else 'up', None, .12 + .03 * k, .35)
for k in range(4): ev('perc', b(28, 2) + k * BEAT / 2, 'cajon', 'tone', None, .22 + .08 * k, 0)
guitar_arp(28, 'A7sus4', .26)

# ---------- bars 29–31 (86.2–93.4): CTA + end card ----------
for bar, name in [(29, 'Dmaj9'), (30, 'Bm9')]:
    groove(bar, .95, claps=True); guitar_arp(bar, name, .32); comp(bar, name, .32); bassline(bar, name, .55)
groove(31, .8); guitar_arp(31, 'Gmaj9', .30, beats=3); chord(b(31), 'Gmaj9', 1.0, .32); chord(b(31, 2), 'A7sus4', .55, .32)
bassn(b(31), 'G1', 1.0, .5); bassn(b(31, 2), 'A1', .5, .5)
# final push chord on "¡Muchas gracias!" (beat 3 of bar 31 + 1 = 92.8) and ring out
tf = b(31, 3)
chord(tf, 'Dmaj9', 3.2, .52, strum=.02); bassn(tf, 'D2', 3.0, .55)
ev('perc', tf, 'cajon', 'bass', None, .55, 0)
for i, p in enumerate(['D6', 'F#6', 'A6', 'C#7', 'D7']): ev('color', tf + .05 + i * .09, 'glockenspiel', p, 2.0, .36 - .03 * i, -.3 + .15 * i)
ev('color', tf, 'hand_chimes', 'D6', 3.0, .35, .2)
ev('color', tf, 'sus_cymbal', 'hit', 3.0, .22, 0)
for p in ['A3', 'D4', 'F#4']: ev('strings', tf, 'violins', p, 3.0, .22, 0.0, attack=.3, release=.8)

# ---------- render stems ----------
N = int(DUR * SR)
def render(evts):
    if not evts: return np.zeros((N, 2), np.float32)
    x = S.render(evts, dur=DUR, master=False)
    out = np.zeros((N, 2), np.float32); n = min(N, len(x)); out[:n] = x[:n]; return out
gains = {'keys': .80, 'guitar': .62, 'bass': .85, 'perc': .62, 'color': .55, 'strings': .55}
st = {k: render(v) * gains[k] for k, v in stems.items()}
tt = np.arange(N) / SR

# "tired" intro: keys + strings muffled until the battery charges, then open up
tired = np.clip(1 - (tt - 12.4) / 3.0, 0, 1)[:, None]
for k in ('keys', 'strings'):
    muff = np.stack([lp(st[k][:, c], 900) for c in range(2)], 1)
    st[k] = st[k] * (1 - tired) + muff * tired * 1.25

mus = sum(st.values())
mus = S.room(mus, size=.38, mix=.16)
# leave space for the voice: soften 1.2–4 kHz a little, clean the sub
for c in range(2):
    mus[:, c] = hp(mus[:, c], 45) - .28 * bp(mus[:, c], 1200, 4000)
# end fade 94.6 → 96.0
fade = np.clip((DUR - tt) / 1.4, 0, 1)[:, None]; mus *= fade
mus = limit(mus / max(1e-6, np.abs(mus).max()) * .9, .95)
sf.write(os.path.join(P, 'out/musica.wav'), mus.astype(np.float32), SR, subtype='PCM_24')

# ---------- UI foley: soft tap clicks and swipe whooshes (output times) ----------
fx = np.zeros((N, 2), np.float32)
for e in TL['taps']:
    add(fx, click(1.5, .55), unwarp(e['t']) - .01, .30, .1)
for e in TL['swipes']:
    w = whoosh(.32, .5); w = hp(w, 900)
    add(fx, w, unwarp(e['t']), .10, .2)
sf.write(os.path.join(P, 'out/sfx.wav'), fx, SR, subtype='PCM_24')
print('music', DUR, 's  peak', float(np.abs(mus).max()), ' sfx peak', float(np.abs(fx).max()))
print('instruments', sorted({e['inst'] for v in stems.values() for e in v}))
