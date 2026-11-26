# Ashwood reel · sound design + cinematic bed, synced to the picture (CC0 samples + synthesis)
# run from the lemo-opuscar library root:  .venv/bin/python <project>/tools/sound.py <project>
import sys, os, math
import numpy as np, soundfile as sf
sys.path.insert(0, '.')
from core.audio import sampler as S
from core.audio.sfx import SR, add, lp, hp, bp, whoosh, limit
P = sys.argv[1]; DUR = 14.5; N = int(DUR * SR)
S.seed(5); rng = np.random.default_rng(9)
def T(d): return np.arange(int(d * SR)) / SR
def env(d, a, r, curve=2.0):
    t = T(d); e = np.minimum(1, t / max(a, 1e-3)) * np.clip((d - t) / max(r, 1e-3), 0, 1) ** curve; return e
def noise(d): return rng.standard_normal(int(d * SR))
def pan_st(x, pan):   # mono -> stereo with constant-power pan (scalar or array)
    p = (np.asarray(pan) + 1) * math.pi / 4; return np.stack([x * np.cos(p), x * np.sin(p)], 1)
def put(buf, st, at, g=1.0):
    i = int(at * SR); n = min(len(st), N - i)
    if n > 0: buf[i:i + n] += st[:n] * g

sfx = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)

# --- whooshes: glide in (1.0), pull back (4.0), push to wolf (6.0), aerial (12.1) ---
def swoosh(d, lo, hi, peak=.6):
    t = T(d); n = noise(d); u = np.clip(t / d, 0, 1)
    sweep = np.sin(np.pi * u) ** 2                     # 0 -> 1 -> 0 : how far the band has travelled from lo to hi
    a, b = bp(n, max(60, lo * .6), lo * 1.7), bp(n, hi * .6, min(SR / 2 - 200, hi * 1.7))
    x = a * (1 - sweep) + b * sweep
    e = np.where(u < peak, (u / peak) ** 1.6, ((1 - u) / (1 - peak)) ** 1.3)
    return x * e
for at, d, lo, hi, pan0, pan1, g in [(0.9, 1.15, 300, 2400, -.4, .2, .55), (3.95, 1.1, 2200, 400, .2, -.2, .45), (5.95, 1.15, 350, 2600, -.2, .3, .55), (11.95, 1.3, 180, 1500, 0, 0, .6)]:
    x = swoosh(d, lo, hi); x = x / (np.abs(x).max() + 1e-9)
    put(sfx, pan_st(x, np.linspace(pan0, pan1, len(x))), at, g)

# --- leaves rustle while the branches sway (2.0–4.6) ---
d = 2.8; t = T(d); n = bp(noise(d), 1800, 7000)
flutter = .5 + .5 * np.abs(np.sin(2 * np.pi * .55 * t)) * (.6 + .4 * rng.random(len(t)) ** 3)
x = n * flutter * env(d, .5, .8, 1.5); x /= np.abs(x).max()
put(sfx, pan_st(x, -.35), 1.85, .16)

# --- the 4 keys come out of the tree: metallic chimes ---
key_notes = [('D7', 'A6'), ('F#7', 'D7'), ('A6', 'E7'), ('E7', 'B6')]
for i, te in enumerate([2.15, 2.45, 2.8, 3.15]):
    ev = [(0.0, 'glockenspiel', key_notes[i][0], .9, .40, .25 + .1 * i), (.06, 'glockenspiel', key_notes[i][1], .8, .30, .35 + .1 * i), (.0, 'triangle', 'muted', None, .30, .3)]
    x = S.render(ev, dur=1.6, master=False); put(sfx, x, te - .02, .55)

# --- gust that carries leaves and keys away to the right (4.55–6.3) ---
d = 1.9; t = T(d); n = lp(bp(noise(d), 250, 3500), 2800)
e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.4
x = n * e / np.abs(n * e).max(); put(sfx, pan_st(x, np.linspace(-.6, .95, len(x))), 4.5, .32)
ev = [(k * .17, 'glockenspiel', p, .5, .22, .5 + .1 * k) for k, p in enumerate(['A7', 'F#7', 'D7', 'B6'])]
put(sfx, S.render(ev, dur=1.8, master=False), 4.95, .35)

# --- sun appears on the roof (5.0) and the light sweeps onto the wolf (6.3–7.2): shimmering risers ---
def shimmer(d, f0, f1, g=1.0):
    t = T(d); f = f0 * (f1 / f0) ** (t / d); ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(ph * k + rng.random() * 6) / k for k in (1, 2, 3, 5)) * (1 + .3 * np.sin(2 * np.pi * 7 * t))
    return x * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2 * g
put(sfx, pan_st(shimmer(1.4, 900, 1800) * .25, .5), 4.95, .5)
ev = [(0, 'hand_chimes', 'A5', 2.0, .35, .5), (.12, 'hand_chimes', 'D6', 2.0, .3, .6)]
put(sfx, S.render(ev, dur=2.6, master=False), 5.05, .5)
put(sfx, pan_st(shimmer(1.2, 600, 2400) * .3, np.linspace(-.3, .5, int(1.2 * SR))), 6.15, .55)

# --- the wolf howls (head lifts at 7.55–8.15) ---
def howl(d=1.9, f_lo=430, f_hi=740):
    t = T(d)
    rise = np.clip(t / .55, 0, 1); fall = np.clip((t - 1.25) / (d - 1.25), 0, 1)
    f0 = f_lo + (f_hi - f_lo) * (1 - (1 - rise) ** 2) - 150 * fall ** 1.5
    f0 = f0 * (1 + .012 * np.sin(2 * np.pi * 5.3 * t) * np.clip((t - .5) / .3, 0, 1))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    x = np.sin(ph) + .45 * np.sin(2 * ph + .3) + .18 * np.sin(3 * ph + .9) + .07 * np.sin(4 * ph)
    x = bp(x, 300, 3200) + .9 * bp(x, 700, 1100)        # "oo" formant
    breath = bp(noise(d), 600, 3500) * .06
    e = np.clip(t / .25, 0, 1) ** 1.5 * np.clip((d - t) / .55, 0, 1) ** 1.3
    return (x + breath) * e
h = howl(); h /= np.abs(h).max()
hs = pan_st(h, .15); hs = S.room(hs.astype(np.float32), size=.75, mix=.35)
put(sfx, hs, 7.65, .42)
h2 = howl(1.6, 380, 650); h2 = lp(h2 / np.abs(h2).max(), 1500)
put(sfx, S.room(pan_st(h2, -.6).astype(np.float32), size=.9, mix=.6), 8.45, .12)   # a distant answer

# --- magical swell into the mist (9–12) and nature at the aerial (12.4–14.5) ---
put(sfx, pan_st(shimmer(3.0, 400, 1600) * .22, 0), 9.0, .55)
d = 2.6; t = T(d); w = lp(noise(d), 600) * np.clip(t / 1.0, 0, 1); put(sfx, pan_st(w / np.abs(w).max(), 0), 11.9, .12)
def chirp(d, f0, f1):
    t = T(d); f = f0 + (f1 - f0) * (t / d) ** .6; ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph + 2.5 * np.sin(2 * np.pi * 38 * t)) * np.sin(np.pi * t / d) ** 2
for at, f0, f1, pn in [(13.05, 4200, 5600, .5), (13.22, 4800, 4100, .5), (13.7, 3600, 5200, -.5), (13.86, 5200, 4300, -.5), (14.15, 4400, 6000, .3)]:
    put(sfx, pan_st(chirp(.14, f0, f1), pn), at, .05)
d = 2.0; t = T(d); river = lp(noise(d), 900) * np.clip(t / 1.2, 0, 1); put(sfx, pan_st(river / np.abs(river).max(), 0), 12.5, .05)

# --- cinematic bed (D major sunrise): strings + chimes + piano ---
def chord(t0, notes, d, v, inst='violins', pan=0, **kw): return [dict(t=t0, inst=inst, pitch=p, dur=d, vel=v, pan=pan + .15 * (i % 3 - 1), **kw) for i, p in enumerate(notes)]
ev = []
ev += chord(0.0, ['D3', 'A3'], 4.2, .28, 'cellos', attack=1.5, release=1.0)
ev += chord(0.3, ['F#4', 'A4', 'D5'], 4.0, .20, 'violins', attack=1.8, release=1.0)
ev += chord(4.0, ['B2', 'F#3'], 3.2, .28, 'cellos', attack=.6, release=.8)
ev += chord(4.0, ['D4', 'F#4', 'B4'], 3.0, .20, 'violins', attack=.6, release=.8)
ev += chord(7.0, ['E3', 'B3'], 2.2, .30, 'cellos', attack=.4, release=.8)
ev += chord(7.0, ['G4', 'B4', 'D5'], 2.2, .22, 'violins', attack=.5, release=.8)
ev += chord(9.0, ['G2', 'D3'], 1.6, .32, 'cellos', attack=.4, release=.6)
ev += chord(9.0, ['B4', 'D5', 'G5'], 1.6, .24, 'violins', attack=.4, release=.6)
ev += chord(10.6, ['A2', 'E3'], 1.6, .36, 'cellos', attack=.3, release=.5)
ev += chord(10.6, ['C#5', 'E5', 'A5'], 1.6, .28, 'violins', attack=.3, release=.5)
ev += chord(12.2, ['D2', 'A2', 'D3'], 2.4, .42, 'cellos', attack=.15, release=1.2)
ev += chord(12.2, ['F#4', 'A4', 'D5', 'F#5'], 2.3, .32, 'violins', attack=.2, release=1.2)
ev += [dict(t=12.2, inst='horn', pitch=p, dur=2.0, vel=.34, pan=-.2, attack=.3, release=1.0) for p in ('D4', 'A4')]
ev += [dict(t=11.0, inst='sus_cymbal', pitch='roll', dur=1.25, vel=.22, pan=0, attack=.9, release=.2)]
for i, (t0, p) in enumerate([(1.0, 'A5'), (2.0, 'F#5'), (3.0, 'D6'), (5.1, 'B5'), (6.2, 'D6'), (9.1, 'G5'), (10.7, 'A5'), (12.25, 'D6'), (12.5, 'A6')]):
    ev.append(dict(t=t0, inst='upright', pitch=p, dur=1.4, vel=.30, pan=.25))
mus = S.render(ev, dur=DUR, master=False)
mus = np.vstack([mus, np.zeros((max(0, N - len(mus)), 2), np.float32)])[:N]
mus = S.room(mus.astype(np.float32), size=.6, mix=.25)
tt = np.arange(N) / SR
mus *= (np.clip((DUR - tt) / 1.0, 0, 1) * np.clip(tt / .4, 0, 1))[:, None]
sfx *= np.clip((DUR - tt) / .6, 0, 1)[:, None]
mus = mus / (np.abs(mus).max() + 1e-9) * .55
sfx = sfx / (np.abs(sfx).max() + 1e-9) * .85
mix = limit(mus * .75 + sfx, .95)
os.makedirs(os.path.join(P, 'out'), exist_ok=True)
sf.write(os.path.join(P, 'out/mix.wav'), mix.astype(np.float32), SR, subtype='PCM_24')
sf.write(os.path.join(P, 'out/music.wav'), mus.astype(np.float32), SR, subtype='PCM_24')
sf.write(os.path.join(P, 'out/sfx.wav'), sfx.astype(np.float32), SR, subtype='PCM_24')
print('ok', DUR)
