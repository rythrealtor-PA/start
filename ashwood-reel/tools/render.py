# Ashwood · logo-to-Poconos reel · draft compositor (1080x1920, 30 fps)
# usage: render.py stills t1,t2,... OUTDIR   |   render.py video OUT.mp4
import sys, json, math, subprocess
import numpy as np, cv2

OW, OH, FPS, DUR = 1080, 1920, 30, 14.5
FULL_H = 1984.0                    # a 1116-wide image fills 1080x1920 at this view height
rng = np.random.default_rng(11)

def load(p, flags=cv2.IMREAD_COLOR): return cv2.imread(p, flags)
IMG = {n: load(f'src/i{n:02d}.jpg') for n in (1, 6, 7, 8, 9, 10, 11, 12)}
RELIT = load('assets/relight.png'); PLATE4 = load('assets/plate4.png')
SP = {k: load(f'assets/{k}.png', cv2.IMREAD_UNCHANGED) for k in ('keyA', 'keyB', 'keyC', 'leaf1', 'leaf2', 'leaf3', 'leaf6', 'leaf7')}
AL = json.load(open('tmp/align.json'))
def M3(m): m = np.asarray(m, np.float64); return np.vstack([m, [0, 0, 1]])
M14, M1_10, M10_8 = M3(AL['1->4']['M']), M3(AL['1->10']['M']), M3(AL['10->8']['M'])
# image1->image10 has no rotation (avoids a tilt jump when the camera hands over to image 10)
_s = math.hypot(M1_10[0, 0], M1_10[1, 0]); _p1 = np.array([[690, 845], [680, 635], [990, 955], [810, 415]], float); _p10 = np.array([[620, 1550], [614, 1048], [1060, 1714], [798, 417]], float)
_t = _p10.mean(0) - _s * _p1.mean(0); M1_10 = np.array([[_s, 0, _t[0]], [0, _s, _t[1]], [0, 0, 1.0]])
I3 = np.eye(3)

# ---------- easing / helpers ----------
def cl(x, a=0., b=1.): return max(a, min(b, x))
def ramp(t, a, b): return cl((t - a) / (b - a))
def eio(k): k = cl(k); return k * k * (3 - 2 * k)
def eio3(k): k = cl(k); return 4 * k ** 3 if k < .5 else 1 - (-2 * k + 2) ** 3 / 2
def eout(k): k = cl(k); return 1 - (1 - k) ** 3
def ein(k): k = cl(k); return k ** 2.2
def lerp(a, b, k): return a + (b - a) * k
def vlerp(v0, v1, k):   # view (cx, cy, h): zoom in log space
    return (lerp(v0[0], v1[0], k), lerp(v0[1], v1[1], k), math.exp(lerp(math.log(v0[2]), math.log(v1[2]), k)))
def view_map(v):        # output pixel -> view coords (3x3)
    cx, cy, h = v; s = h / OH
    return np.array([[s, 0, cx - OW / 2 * s], [0, s, cy - OH / 2 * s], [0, 0, 1]])
def xform_view(v, M):   # express a view in another image's coords (similarity M)
    p = M @ np.array([v[0], v[1], 1.0]); sc = math.hypot(M[0, 0], M[1, 0]); return (p[0], p[1], v[2] * sc)
def warp(img, A):       # A: out -> img (3x3)
    return cv2.warpAffine(img, A[:2], (OW, OH), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)

FULL = (558.0, 1000.0, FULL_H)
WOLF_XF = (6.55, 7.05)   # v1 cross-fade into the close-up wolf (render2 turns it off)
# views in image-1 coords for the tree close-up and the wolf close-up
INV14, INV1_10 = np.linalg.inv(M14), np.linalg.inv(M1_10)
TREE_V = xform_view((558, 1000, FULL_H * .97), INV14)   # image 4's frame, a hair tighter (it is rotated 0.76 deg)
WOLF_V = xform_view(FULL, INV1_10)        # image 10's full frame, seen in image 1

# ---------- camera (in image-1 coords until the wolf, then image-10 coords, then image-6 / image-11) ----------
def camA(t):
    if t < 1.0: return vlerp(FULL, (558, 1000, FULL_H * .975), eio(t / 1.0))
    v0 = (558, 1000, FULL_H * .975)
    if t < 2.0: return vlerp(v0, TREE_V, eio3(ramp(t, 1.0, 2.0)))
    tv2 = (TREE_V[0] + 6, TREE_V[1] + 4, TREE_V[2] * .955)
    if t < 4.0: return vlerp(TREE_V, tv2, eio(ramp(t, 2.0, 4.0)))
    if t < 5.0: return vlerp(tv2, FULL, eio3(ramp(t, 4.0, 5.0)))
    if t < 6.0: return vlerp(FULL, (560, 990, FULL_H * .985), eio(ramp(t, 5.0, 6.0)))
    return vlerp((560, 990, FULL_H * .985), WOLF_V, eio3(ramp(t, 6.0, 7.0)))
B9 = (590, 930, 1640)
B97 = (520, 1045, 1390)
B12 = (552, 905, 1150)
def camB(t):            # image-10 coords
    if t < 7.0: return xform_view(camA(t), M1_10)
    if t < 9.0: return vlerp(FULL, B9, eio(ramp(t, 7.0, 9.0)) * .9 + .1 * ramp(t, 7.0, 9.0))
    if t < 9.75: return vlerp(B9, B97, eio(ramp(t, 9.0, 9.75)))
    if t < 12.0: return vlerp(B97, B12, eio(ramp(t, 9.75, 12.0)) * .7 + .3 * ramp(t, 9.75, 12.0))
    return vlerp(B12, BEND, ein(ramp(t, 12.0, 12.9)))
BEND = xform_view((600, 650, 1020), np.linalg.inv(M10_8))
def cam11(t):
    v0, v1 = (590, 1360, 900), (558, 990, FULL_H)
    return vlerp(v0, v1, eout(ramp(t, 12.5, 14.25)))

# ---------- tree sway (image-4 coords) ----------
H4, W4 = PLATE4.shape[:2]
yy4, xx4 = np.mgrid[0:H4, 0:W4].astype(np.float32)
xroof = 796 + (yy4 - 1350) * (-0.392)
treem = ((xx4 < xroof - 14) & (yy4 > 470)).astype(np.float32)
treem = cv2.GaussianBlur(treem, (0, 0), 22)
hfac = np.clip((1700 - yy4) / 950, 0, 1) ** 1.15
SWAYW = (treem * hfac).astype(np.float32)
def sway_maps(A, t, amp):
    gy, gx = np.mgrid[0:OH, 0:OW].astype(np.float32)
    X = A[0, 0] * gx + A[0, 1] * gy + A[0, 2]; Y = A[1, 0] * gx + A[1, 1] * gy + A[1, 2]
    sm = np.clip((Y - 1650) / 150, 0, 1); Y = Y + 42 * sm * sm * (3 - 2 * sm)   # image 4's letters sit 42 px lower than the logo's
    if amp <= 0: return X.astype(np.float32), Y.astype(np.float32)
    w = cv2.remap(SWAYW, X.astype(np.float32), Y.astype(np.float32), cv2.INTER_LINEAR)
    ph = 2 * math.pi * .55 * t
    dx = amp * w * (np.sin(ph + .0045 * X + .0021 * Y) + .35 * np.sin(2 * math.pi * 1.25 * t + .011 * Y + 1.7))
    dy = .35 * amp * w * np.sin(ph + .004 * X + 1.2)
    return (X + dx).astype(np.float32), (Y + dy).astype(np.float32)

# ---------- wolf alive (image-10 coords): mane flow + head lift ----------
H10, W10 = IMG[10].shape[:2]
yy, xx = np.mgrid[0:H10, 0:W10].astype(np.float32)
def ell(cx, cy, rx, ry, ang):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    u = ((xx - cx) * c + (yy - cy) * s) / rx; v = (-(xx - cx) * s + (yy - cy) * c) / ry
    return np.clip(1 - (u * u + v * v), 0, 1) ** .6
MANE = cv2.GaussianBlur(np.maximum(ell(640, 860, 220, 300, -12), ell(720, 640, 150, 170, -30) * .6), (0, 0), 18).astype(np.float32)
HEAD = cv2.GaussianBlur(ell(700, 560, 230, 200, -38), (0, 0), 25).astype(np.float32)
PIV = (560.0, 790.0)
def wolf_maps(A, t, alive):
    gy, gx = np.mgrid[0:OH, 0:OW].astype(np.float32)
    X = (A[0, 0] * gx + A[0, 1] * gy + A[0, 2]).astype(np.float32); Y = (A[1, 0] * gx + A[1, 1] * gy + A[1, 2]).astype(np.float32)
    if alive <= 0: return X, Y
    m = cv2.remap(MANE, X, Y, cv2.INTER_LINEAR) * alive; hd = cv2.remap(HEAD, X, Y, cv2.INTER_LINEAR) * alive
    # fur: strands ripple in the wind (to the right)
    dx = m * (2.6 * np.sin(2 * math.pi * .9 * t - .045 * Y + .012 * X) + 1.4 * np.sin(2 * math.pi * 1.7 * t - .09 * Y + 2.1))
    dy = m * (1.2 * np.sin(2 * math.pi * .7 * t - .05 * X + .02 * Y))
    # howl: the head lifts ~2.4 degrees and settles
    a = math.radians(-2.4) * (eio(ramp(t, 7.55, 8.15)) - eio(ramp(t, 8.75, 9.4)))
    c, s = math.cos(-a), math.sin(-a)
    rx, ry = X - PIV[0], Y - PIV[1]
    hx = PIV[0] + c * rx - s * ry - X; hy = PIV[1] + s * rx + c * ry - Y
    breath = 1 + .006 * math.sin(2 * math.pi * .45 * t)
    bx, by = (X - PIV[0]) * (1 / breath - 1), (Y - PIV[1]) * (1 / breath - 1)
    return (X + dx + hd * hx + m * bx).astype(np.float32), (Y + dy + hd * hy + m * by).astype(np.float32)

# ---------- sprites: 4 keys + golden leaves (paths in image-4 coords, then a breeze in image-1 coords) ----------
def mirror(sp): return np.ascontiguousarray(sp[:, ::-1])
KEYS = [  # sprite, start (img4), target (img4), t_emerge, start rotation offset (deg), extra rotation
    dict(sp=SP['keyA'], p0=(640, 840), p1=(930, 630), te=2.15, r0=-35, r1=0),
    dict(sp=SP['keyC'], p0=(610, 1030), p1=(885, 873), te=2.45, r0=30, r1=0),
    dict(sp=SP['keyB'], p0=(690, 960), p1=(1028, 692), te=2.8, r0=-28, r1=0),
    dict(sp=mirror(SP['keyB']), p0=(800, 1218), p1=(860, 1045), te=3.15, r0=-42, r1=-12, sc=.9),
]
LEAVES = [  # sprite, start (img4), t_detach, fall speed, sway, spin
    dict(sp=SP['leaf2'], p0=(560, 760), te=2.1, v=70, sw=26, ph=0.0),
    dict(sp=SP['leaf3'], p0=(700, 1060), te=2.35, v=58, sw=20, ph=1.3),
    dict(sp=SP['leaf6'], p0=(470, 900), te=2.6, v=64, sw=30, ph=2.1),
    dict(sp=SP['leaf7'], p0=(640, 700), te=2.9, v=52, sw=22, ph=.7),
    dict(sp=SP['leaf1'], p0=(760, 1120), te=3.2, v=60, sw=18, ph=2.8),
    dict(sp=mirror(SP['leaf3']), p0=(520, 1000), te=3.45, v=56, sw=24, ph=1.9),
]
for _i, _d in enumerate(KEYS): _d['i'] = _i
for _i, _d in enumerate(LEAVES): _d['i'] = _i
def to1(p): q = INV14 @ np.array([p[0], p[1], 1.0]); return q[0], q[1]
S41 = 1 / math.hypot(M14[0, 0], M14[1, 0])            # image-4 px -> image-1 px
def breeze(t, delay=0.):   # everything leaves to the right, smoothly accelerating (image-1 px)
    k = ramp(t, 4.55 + delay, 6.25 + delay)
    return 1350 * k ** 1.9, -70 * math.sin(math.pi * k) - 30 * k
def key_state(K, t):
    if t < K['te']: return None
    k = eout(ramp(t, K['te'], K['te'] + 1.25))
    x4 = lerp(K['p0'][0], K['p1'][0], k) + (1 - k) * 40 * math.sin(k * 3)
    y4 = lerp(K['p0'][1], K['p1'][1], k) - math.sin(math.pi * k) * 30
    bob = math.sin(2 * math.pi * .5 * (t - K['te'])) * 6 * k
    x1, y1 = to1((x4, y4 + bob))
    bx, by = breeze(t, delay=.08 * K['i'])
    rot = lerp(K['r0'], K['r1'], k) + 4 * math.sin(2 * math.pi * .4 * t + K['te']) + 25 * ramp(t, 4.8, 6.3) ** 2
    a = eout(ramp(t, K['te'], K['te'] + .35))
    sc = (.55 + .45 * eout(ramp(t, K['te'], K['te'] + .5))) * K.get('sc', 1)
    return (x1 + bx, y1 + by), rot, sc, a
def leaf_state(L, t):
    if t < L['te']: return None
    d = t - L['te']
    x4 = L['p0'][0] + L['sw'] * math.sin(2 * math.pi * .62 * d + L['ph']) + 12 * d
    y4 = L['p0'][1] + L['v'] * d + 8 * math.sin(2 * math.pi * 1.2 * d)
    x1, y1 = to1((x4, y4)); bx, by = breeze(t, delay=.05 * L['i'])
    rot = 28 * math.sin(2 * math.pi * .62 * d + L['ph'] + .8) + 40 * ramp(t, 4.8, 6.3)
    return (x1 + bx, y1 + by), rot, 1.0, eout(ramp(t, L['te'], L['te'] + .3)), .55 + .45 * abs(math.cos(math.radians(rot)))

def paste_sprite(frame, sp, Vout, pos1, rot, sc, alpha, world_scale, gain=1.0, blur_dx=0.0):
    """pos1/world in view coords (image-1 px); sprite px * world_scale = view px; Vout: view->out 3x3"""
    hS, wS = sp.shape[:2]
    k = math.hypot(Vout[0, 0], Vout[1, 0]) * world_scale * sc
    o = Vout @ np.array([pos1[0], pos1[1], 1.0])
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    A = np.array([[k * c, -k * s, 0], [k * s, k * c, 0]], np.float64)
    A[:, 2] = [o[0], o[1]] - A[:, :2] @ np.array([wS / 2, hS / 2])
    r = int(math.hypot(wS, hS) * k / 2) + 4
    x0, y0, x1, y1 = int(o[0]) - r, int(o[1]) - r, int(o[0]) + r, int(o[1]) + r
    X0, Y0, X1, Y1 = max(x0, 0), max(y0, 0), min(x1, OW), min(y1, OH)
    if X1 <= X0 or Y1 <= Y0 or alpha <= 0: return
    A2 = A.copy(); A2[:, 2] -= [X0, Y0]
    roi = cv2.warpAffine(sp, A2, (X1 - X0, Y1 - Y0), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)).astype(np.float32)
    if blur_dx > 1.5:
        kk = int(min(blur_dx, 40)) | 1; roi = cv2.blur(roi, (kk, 1))
    a = roi[..., 3:4] / 255 * alpha
    frame[Y0:Y1, X0:X1] = frame[Y0:Y1, X0:X1] * (1 - a) + np.clip(roi[..., :3] * gain, 0, 255) * a

# ---------- light, mist, dust ----------
def fbm(h, w, seed):
    r = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32); amp = 1.0
    for o in range(4):
        s = 2 ** (o + 5); n = r.random((h // (s * 2) + 2, w // (s * 2) + 2)).astype(np.float32)
        acc += amp * cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC); amp *= .5
    acc -= acc.min(); return acc / acc.max()
MIST = fbm(2600, 1600, 5)
def mist_layer(t, amount):
    if amount <= 0: return None
    ox, oy = int(120 + 38 * t) % 400, int(200 + 10 * t) % 500
    m = MIST[oy:oy + OH, ox:ox + OW]
    m = np.clip((m - .35) * 1.9, 0, 1) * amount
    grad = np.linspace(.55, 1.0, OH, dtype=np.float32)[:, None]
    return (m * grad)[..., None]
NP = 170
PART = dict(x=rng.uniform(0, OW, NP), y=rng.uniform(0, OH, NP), z=rng.uniform(.3, 1.0, NP), ph=rng.uniform(0, 6.28, NP), r=rng.uniform(.8, 2.6, NP))
def dust(frame, t, cam_dx, cam_dy, amount):
    if amount <= 0: return
    lay = np.zeros((OH, OW), np.float32)
    x = (PART['x'] + 18 * t * PART['z'] - cam_dx * PART['z']) % OW
    y = (PART['y'] - 26 * t * PART['z'] - cam_dy * PART['z']) % OH
    tw = .5 + .5 * np.sin(2.3 * t + PART['ph'])
    for i in range(NP):
        cv2.circle(lay, (int(x[i]), int(y[i])), int(PART['r'][i] + .5), float(.35 + .65 * tw[i]) * PART['z'][i], -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 1.6) * amount
    frame += lay[..., None] * np.array([150, 215, 255], np.float32)
def flare(frame, x, y, k, rays=True):
    if k <= 0 or not (-300 < x < OW + 300 and -300 < y < OH + 300): return
    gy, gx = np.ogrid[0:OH, 0:OW]
    d2 = (gx - x) ** 2 + (gy - y) ** 2
    core = np.exp(-d2 / (2 * (30 ** 2))) * 1.0 + np.exp(-d2 / (2 * (130 ** 2))) * .32
    lay = core.astype(np.float32)
    if rays:
        ang = np.arctan2(gy - y, gx - x); rr = np.sqrt(d2) + 1
        lay += (np.abs(np.cos(ang * 3.0)) ** 40 + .6 * np.abs(np.cos(ang * 5 + .4)) ** 60) * np.exp(-rr / 300) * .5
    frame += (lay * k)[..., None] * np.array([120, 205, 255], np.float32)
def glint(frame, x, y, k):
    if k <= 0: return
    r = 70; x0, y0 = int(x) - r, int(y) - r
    if x0 < 0 or y0 < 0 or x0 + 2 * r >= OW or y0 + 2 * r >= OH: return
    gy, gx = np.mgrid[-r:r, -r:r].astype(np.float32)
    d = np.sqrt(gx * gx + gy * gy) + 1
    lay = np.exp(-(d / 5) ** 2) + .35 * np.exp(-(d / 16) ** 2) + (np.exp(-np.abs(gy) / 1.6) + np.exp(-np.abs(gx) / 1.6)) * np.exp(-d / 26) * .7
    frame[y0:y0 + 2 * r, x0:x0 + 2 * r] += (lay * k)[..., None] * np.array([150, 225, 255], np.float32)
def sweep(frame, t, t0, t1):
    k = ramp(t, t0, t1)
    if k <= 0 or k >= 1: return
    gy, gx = np.ogrid[0:OH, 0:OW]
    pos = lerp(-500, 2100, eio(k)); d = (gx * .5 + (OH - gy) * .866) - pos
    band = np.exp(-(d / 230.0) ** 2) * math.sin(math.pi * k)
    lum = frame.mean(2, keepdims=True) / 255
    frame += (band[..., None] * (.35 + lum) * .8) * np.array([90, 190, 255], np.float32)

# ---------- one frame ----------
def blend(a, b, k):
    if np.isscalar(k): return a if k <= 0 else (b if k >= 1 else a * (1 - k) + b * k)
    return a * (1 - k) + b * k
# coverage: 1 inside a source image, feathered to 0 at its edges (so a layer never shows mirrored borders)
COV = np.ones((2000, 1116), np.float32); F_ = 28
ramp_ = np.linspace(0, 1, F_, dtype=np.float32)
COV[:F_] *= ramp_[:, None]; COV[-F_:] *= ramp_[::-1, None]; COV[:, :F_] *= ramp_[None]; COV[:, -F_:] *= ramp_[None, ::-1]
def warp_c(img, A):
    w = cv2.warpAffine(img, A[:2], (OW, OH), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    c = cv2.warpAffine(COV, A[:2], (OW, OH), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return w, c[..., None]
def remap_c(img, mx, my):
    w = cv2.remap(img, mx, my, cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    c = cv2.remap(COV, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return w, c[..., None]
def frame_at(t):
    if t < 7.05:
        vA = camA(t); V = view_map(vA); Vout = np.linalg.inv(V)
        base = blend(IMG[12].astype(np.float32), IMG[1].astype(np.float32), eio(ramp(t, .1, 1.05)))
        if t > 4.9: base = blend(base, RELIT.astype(np.float32), eio(ramp(t, 5.0, 5.9)))
        out, _ = warp_c(base, V)
        k4 = eio(ramp(t, 1.5, 1.95)) * (1 - eio(ramp(t, 4.12, 4.62)))
        if k4 > 0:
            amp = 7.5 * eio(ramp(t, 1.7, 2.3)) * (1 - eio(ramp(t, 4.1, 4.7)))
            mx, my = sway_maps(M14 @ V, t, amp)
            T4, c4 = remap_c(PLATE4, mx, my)
            out = blend(out, T4, k4 * c4)
        for L_ in LEAVES:
            st = leaf_state(L_, t)
            if st:
                p, rot, sc, a, g = st
                spd = (breeze(t + .02)[0] - breeze(t)[0]) * 1.7 / (vA[2] / OH)
                paste_sprite(out, L_['sp'], Vout, p, rot, sc, a * (1 - ramp(t, 6.0, 6.4)), S41, gain=.8 + .5 * g, blur_dx=spd)
        for K in KEYS:
            st = key_state(K, t)
            if st:
                p, rot, sc, a = st
                spd = (breeze(t + .02)[0] - breeze(t)[0]) * 1.7 / (vA[2] / OH)
                paste_sprite(out, K['sp'], Vout, p, rot, sc, a * (1 - ramp(t, 6.0, 6.4)), S41, gain=1.05, blur_dx=spd)
                if t < K['te'] + .55:
                    o = Vout @ np.array([p[0], p[1], 1.0]); glint(out, o[0], o[1], 1.1 * math.sin(math.pi * ramp(t, K['te'], K['te'] + .55)))
        sk = eio(ramp(t, 5.0, 5.75)) * (1 - eio(ramp(t, 6.35, 6.9)))
        if sk > 0:
            o = Vout @ np.array([905, 862, 1.0]); flare(out, o[0], o[1], .75 * sk)
        if t > WOLF_XF[0] - .05:
            mx, my = wolf_maps(M1_10 @ V, t, 0)
            W10i, c10 = remap_c(IMG[10], mx, my)
            out = blend(out, W10i, eio(ramp(t, *WOLF_XF)) * c10)
        sweep(out, t, 6.3, 7.25)
    else:
        vB = camB(t); V = view_map(vB)
        alive = eio(ramp(t, 7.2, 7.7)) * (1 - eio(ramp(t, 9.3, 10.0)))
        out = None
        if t < 12.0:
            mx, my = wolf_maps(V, t, alive)
            out, _ = remap_c(IMG[10], mx, my)
            k9 = eio(ramp(t, 9.0, 9.75))
            if k9 > 0:
                L9, _ = remap_c(IMG[9], mx, my); out = blend(out, L9, k9)
        A8 = M10_8 @ V
        for n, (t0, t1) in ((8, (9.7, 10.5)), (7, (10.5, 11.2)), (6, (11.2, 12.0))):
            k = eio(ramp(t, t0, t1))
            if k > 0 and (t < 12.0 or n == 6):
                Ln, cn = warp_c(IMG[n], A8)
                out = Ln if out is None else blend(out, Ln, k * cn)
        if t >= 12.45:
            L11, _ = warp_c(IMG[11], view_map(cam11(t)))
            out = blend(out, L11, eio(ramp(t, 12.45, 13.1)))
        if 7.0 <= t < 9.6:
            o = np.linalg.inv(V) @ np.array([930, 640, 1.0]); flare(out, o[0], o[1], .28 * alive, rays=False)
        sweep(out, t, 6.3, 7.25)
    mist_amt = .10 + .30 * math.sin(math.pi * ramp(t, 8.9, 12.4)) + .14 * math.sin(math.pi * ramp(t, 12.2, 13.6))
    m = mist_layer(t, mist_amt)
    if m is not None: out = out * (1 - m) + m * np.array([200, 228, 245], np.float32)
    dust(out, t, 0, 0, .55 + .25 * ramp(t, 8.5, 11))
    hl = np.clip(out - 205, 0, None); out += cv2.GaussianBlur(hl, (0, 0), 18) * .55
    return np.clip(out * VIG, 0, 255).astype(np.uint8)

gy, gx = np.mgrid[0:OH, 0:OW].astype(np.float32)
VIG = (1 - .22 * (((gx - OW / 2) / (OW * .75)) ** 2 + ((gy - OH / 2) / (OH * .75)) ** 2))[..., None]

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        ts = [float(x) for x in sys.argv[2].split(',')]; od = sys.argv[3]
        for t in ts: cv2.imwrite(f'{od}/s_{t:05.2f}.jpg', frame_at(t), [cv2.IMWRITE_JPEG_QUALITY, 90])
    else:
        out = sys.argv[2]; N = int(round(DUR * FPS))
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
                              '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15',
                              '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        lo, hi = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, N)
        for i in range(lo, hi):
            p.stdin.write(frame_at(i / FPS).tobytes())
            if i % 30 == 0: print('frame', i, '/', N, flush=True)
        p.stdin.close(); p.wait()
