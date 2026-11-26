# Ashwood reel v2: 0–6 s from v1; new wolf transformation and a continuous forward flight to the valley (15 s)
# usage: render2.py stills t1,t2,... OUTDIR  |  render2.py video OUT.mp4 [lo hi]
import sys, math, subprocess, json
sys.path.insert(0, 'tools')
import numpy as np, cv2
import render as R
from render import OW, OH, FPS, FULL_H, FULL, ramp, eio, eio3, eout, lerp, vlerp, view_map, xform_view, warp_c, remap_c, blend, M3

DUR = 15.0
for n in (13, 14, 15, 16, 17): R.IMG[n] = cv2.imread(f'src/i{n:02d}.jpg')
AL = json.load(open('tmp/align.json'))
M13_15 = M3(AL['13->15']['M']); M15_16 = M3(AL['15->16sift']['M']); M13_16 = M15_16 @ M13_15
INV1_10 = np.linalg.inv(R.M1_10)

# ---------------- cameras ----------------
P0 = (560, 990, FULL_H * .985)
_camA_v1 = R.camA                 # keep v1's camera for 0–6 s
def camA2(t):                     # image-1 coords
    if t < 6.0: return _camA_v1(t)
    return vlerp(P0, R.WOLF_V, eio3(ramp(t, 6.0, 6.65)))
C0, H0 = (556.0, 1005.0), 1880.0
AIM = np.array([560.0, 870.0])      # vanishing point of the flight (image-13 coords): the mountain, kept inside images 15/16
RATE = 0.21
def lnh(t):                        # constant-speed forward flight (log zoom), eased in over 9.0–9.8
    if t <= 9.0: return math.log(H0)
    u = min((t - 9.0) / .8, 1.0); I = .8 * (u ** 3 - u ** 4 / 2)
    if t > 9.8: I += t - 9.8
    return math.log(H0) - RATE * I
def cam13(t):                      # image-13 coords
    if t < 7.3: return vlerp(FULL, (557, 1002, 1950), eio(ramp(t, 6.65, 7.3)))
    if t < 9.0: return vlerp((557, 1002, 1950), (C0[0], C0[1], H0), eio(ramp(t, 7.3, 9.0)))
    h = math.exp(lnh(t)); c = AIM + (np.array(C0) - AIM) * (h / H0)
    return (c[0], c[1], h)
def t_at_h(hv):                    # time when the flight reaches view height hv
    lo, hi = 9.0, 16.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if math.exp(lnh(mid)) > hv: lo = mid
        else: hi = mid
    return lo
H15 = FULL_H / math.hypot(M13_15[0, 0], M13_15[1, 0]); H16 = FULL_H / math.hypot(M13_16[0, 0], M13_16[1, 0])
T15 = (t_at_h(1290), t_at_h(1200)); T16 = (t_at_h(940), t_at_h(860)); T17 = (13.75, 14.4)
A17 = np.array([600.0, 900.0])
def cam17(t):
    k = ramp(t, T17[0], DUR); f = k * (1.15 - .15 * k)
    h = FULL_H * math.exp(-.223 * f); c = A17 + (np.array([558.0, 1000.0]) - A17) * (h / FULL_H)
    return (c[0], c[1], h)

# ---------------- the wolf comes to life: TPS morph + fur growing from the mane to the face ----------------
# landmarks: image 1 (2D logo wolf) -> image 13 (carved wolf); house points keep the background stable
P1 = np.array([[800, 417], [833, 500], [713, 503], [700, 480], [587, 573], [803, 600], [790, 650], [683, 593], [686, 640], [690, 845], [990, 955]], float)
P13 = np.array([[805, 411], [873, 562], [676, 555], [714, 517], [418, 736], [845, 860], [857, 1062], [577, 888], [614, 1048], [620, 1550], [1060, 1714]], float)
def to13(p): return (p @ R.M1_10[:2, :2].T) + R.M1_10[:2, 2]
P1p = to13(P1)
ANC = np.array([[0, 2000], [1116, 2000], [0, 1100], [1116, 1100], [558, 2000], [200, 1400], [1000, 1300]], float)
def circ_fit(pts):
    A = np.c_[2 * pts, np.ones(len(pts))]; b = (pts ** 2).sum(1); cx, cy, c = np.linalg.lstsq(A, b, rcond=None)[0]; return np.array([cx, cy]), math.sqrt(c + cx * cx + cy * cy)
C13, R13 = circ_fit(np.array([[167, 133], [600, 33], [967, 233], [1100, 533]], float))     # the ring in image 13
C1p = to13(np.array([[558.0, 1105.0]]))[0]; R1p = 868 * math.hypot(R.M1_10[0, 0], R.M1_10[1, 0])   # the logo ring, in image-13 coords
RING13 = []; RING1 = []
for x in (60, 330, 600, 870, 1090):
    dy = math.sqrt(max(R13 ** 2 - (x - C13[0]) ** 2, 0)); p = np.array([x, C13[1] - dy]); d = (p - C13) / np.linalg.norm(p - C13)
    RING13.append(p); RING1.append(C1p + R1p * d)
SRC1 = np.vstack([P1p, RING1, ANC]); SRC13 = np.vstack([P13, RING13, ANC])
def U(r2): return np.where(r2 > 0, r2 * np.log(r2 + 1e-12), 0.0)
def tps_fit(ctrl, dst, lam=1e-6):
    n = len(ctrl); K = U(((ctrl[:, None] - ctrl[None]) ** 2).sum(-1)); K += lam * np.eye(n) * K.mean()
    Pm = np.hstack([np.ones((n, 1)), ctrl]); L = np.zeros((n + 3, n + 3)); L[:n, :n] = K; L[:n, n:] = Pm; L[n:, :n] = Pm.T
    Y = np.vstack([dst, np.zeros((3, 2))]); return np.linalg.solve(L, Y)
def tps_eval(par, ctrl, pts):
    n = len(ctrl); K = U(((pts[:, None] - ctrl[None]) ** 2).sum(-1))
    return K @ par[:n] + par[n] + pts @ par[n + 1:]
H13, W13 = R.IMG[10].shape[:2]
yy, xx = np.mgrid[0:H13, 0:W13].astype(np.float32)
B_, E_ = np.array([640.0, 1010.0]), np.array([805.0, 411.0]); ax = E_ - B_
ORDER = (((xx - B_[0]) * ax[0] + (yy - B_[1]) * ax[1]) / (ax @ ax)).astype(np.float32)
WOLFM = cv2.GaussianBlur(np.maximum(R.MANE, R.HEAD) ** .5, (0, 0), 6).astype(np.float32)
rng = np.random.default_rng(21)
def noise_tex(h, w, cells, seed, blur=None):
    r = np.random.default_rng(seed); n = r.random((h // cells + 2, w // cells + 2)).astype(np.float32)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    if blur: n = cv2.GaussianBlur(n, (0, 0), *blur)
    n -= n.min(); return n / n.max()
NOISE = (.6 * noise_tex(H13, W13, 40, 3) + .4 * noise_tex(H13, W13, 12, 4)).astype(np.float32)
STRAND = noise_tex(H13, W13, 3, 5)
ang = math.degrees(math.atan2(ax[1], ax[0]))      # fur strands roughly along the wolf's axis
Mrot = cv2.getRotationMatrix2D((W13 / 2, H13 / 2), ang + 90, 1.0)
STRAND = cv2.GaussianBlur(cv2.warpAffine(STRAND, Mrot, (W13, H13), borderMode=cv2.BORDER_REFLECT), (0, 0), 1.0, 9.0)
STRAND = cv2.warpAffine(STRAND, cv2.invertAffineTransform(Mrot), (W13, H13), borderMode=cv2.BORDER_REFLECT)
STRAND = ((STRAND - STRAND.min()) / (STRAND.max() - STRAND.min())).astype(np.float32)
def morph_frame(t, V):
    a = eio(ramp(t, 6.62, 7.25)); p = lerp(-.25, 1.22, eio(ramp(t, 6.68, 7.33)))
    L = (1 - a) * SRC1 + a * SRC13
    f13 = tps_fit(L, SRC13); f1 = tps_fit(L, SRC1)
    q = 4; gy, gx = np.mgrid[0:OH:q, 0:OW:q].astype(np.float64)
    pts = np.stack([V[0, 0] * gx + V[0, 2], V[1, 1] * gy + V[1, 2]], -1).reshape(-1, 2)
    m13 = tps_eval(f13, L, pts); m1 = tps_eval(f1, L, pts) @ INV1_10[:2, :2].T + INV1_10[:2, 2]
    up = lambda m, k: cv2.resize(m[:, k].reshape(gx.shape).astype(np.float32), (OW, OH), interpolation=cv2.INTER_LINEAR)
    x13, y13, x1, y1 = up(m13, 0), up(m13, 1), up(m1, 0), up(m1, 1)
    I13, c13 = remap_c(R.IMG[10], x13, y13)
    I1, _ = remap_c(R.RELIT, x1, y1)
    W = cv2.remap(WOLFM, x13, y13, cv2.INTER_LINEAR)[..., None]
    O = cv2.remap(ORDER, x13, y13, cv2.INTER_LINEAR); N = cv2.remap(NOISE, x13, y13, cv2.INTER_LINEAR)
    S = cv2.remap(STRAND, x13, y13, cv2.INTER_LINEAR)
    front = p - O - .22 * (N - .5)
    rev = np.clip(front / .11 + .5, 0, 1); rev = (rev * rev * (3 - 2 * rev))[..., None]
    bg = eio(ramp(t, 6.70, 6.95)); bgf = eio(ramp(t, 6.70, 6.82))
    txt = np.clip((y13 - 1690) / 90, 0, 1)[..., None]
    k = ((bg * (1 - txt) + bgf * txt) * (1 - W) + rev * W) * c13
    out = blend(I1, I13, k)
    glow = np.exp(-(front / .045) ** 2) * (1.0 if -0.2 < p < 1.2 else 0.0)
    g = cv2.GaussianBlur((glow * W[..., 0] * (.15 + 1.1 * S * S)).astype(np.float32), (0, 0), 1.6)
    out += g[..., None] * np.array([150, 218, 255], np.float32) * .55
    return out

# ---------------- post (same look as v1) ----------------
def post(out, t, mist_amt, dust_amt):
    m = R.mist_layer(t, mist_amt)
    if m is not None: out = out * (1 - m) + m * np.array([200, 228, 245], np.float32)
    R.dust(out, t, 0, 0, dust_amt)
    hl = np.clip(out - 205, 0, None); out += cv2.GaussianBlur(hl, (0, 0), 18) * .55
    return np.clip(out * R.VIG, 0, 255).astype(np.uint8)
def bump(t, a, b): return math.sin(math.pi * ramp(t, a, b))

# ---------------- one frame ----------------
R.camA = camA2
R.sweep = lambda *a, **k: None
R.WOLF_XF = (99.0, 100.0)
def frame_at(t):
    if t < 6.0: return R.frame_at(t)
    sun_k = eio(ramp(t, 5.0, 5.75)) * (1 - eio(ramp(t, 6.35, 6.9)))
    if t < 6.65:
        return R.frame_at(t)        # v1 logo block with the new camera (no sweep, no v1 wolf cross-fade)
    v = cam13(t); V = view_map(v); Vout = np.linalg.inv(V)
    if t < 7.35:
        out = morph_frame(t, V)
        if sun_k > 0:
            p13 = to13(np.array([[905.0, 862.0]]))[0]; o = Vout @ np.array([p13[0], p13[1], 1.0]); R.flare(out, o[0], o[1], .75 * sun_k)
        return post(out, t, .10, .55)
    alive = eio(ramp(t, 7.3, 7.6)) * (1 - eio(ramp(t, 9.4, 10.0)))
    out = None
    if t < T15[1] + .05:
        mx, my = R.wolf_maps(V, t - .12, alive)
        out, _ = remap_c(R.IMG[10], mx, my)
        k14 = eio(ramp(t, 9.0, 10.0))
        if k14 > 0:
            L14, _ = remap_c(R.IMG[14], mx, my); out = blend(out, L14, k14)
    k15 = eio(ramp(t, *T15))
    if k15 > 0 and t < T16[1] + .05:
        L15, c15 = warp_c(R.IMG[15], M13_15 @ V)
        out = L15 if out is None else blend(out, L15, k15 * c15)
    k16 = eio(ramp(t, *T16))
    if k16 > 0 and t < T17[1] + .05:
        L16, c16 = warp_c(R.IMG[16], M13_16 @ V)
        out = L16 if out is None else blend(out, L16, k16 * c16)
    k17 = eio(ramp(t, *T17))
    if k17 > 0:
        L17, _ = warp_c(R.IMG[17], view_map(cam17(t)))
        out = L17 if out is None else blend(out, L17, k17)
    if 7.3 <= t < 9.8:
        o = Vout @ np.array([930, 640, 1.0]); R.flare(out, o[0], o[1], .28 * alive, rays=False)
    mist = .10 + .20 * bump(t, 9.0, 10.6) + .24 * bump(t, T15[0] - .6, T16[1] + .4) + .34 * bump(t, T17[0] - .45, T17[1] + .45)
    haze = .55 * bump(t, T17[0] - .3, T17[1] + .3) ** 1.5
    if haze > 0: out = out * (1 - haze) + haze * np.array([214, 232, 246], np.float32)
    return post(out, t, mist, .55 + .25 * ramp(t, 8.5, 11) - .25 * ramp(t, 13.5, 14.5))

if __name__ == '__main__':
    print('flight windows: 15 at', [round(x, 2) for x in T15], ' 16 at', [round(x, 2) for x in T16], ' 17 at', T17, flush=True)
    mode = sys.argv[1]
    if mode == 'stills':
        ts = [float(x) for x in sys.argv[2].split(',')]; od = sys.argv[3]
        for t in ts: cv2.imwrite(f'{od}/v2_{t:05.2f}.jpg', frame_at(t), [cv2.IMWRITE_JPEG_QUALITY, 90])
    else:
        out = sys.argv[2]; N = int(round(DUR * FPS))
        lo, hi = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, N)
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
                              '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15',
                              '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        for i in range(lo, hi):
            p.stdin.write(frame_at(i / FPS).tobytes())
            if i % 30 == 0: print('frame', i, '/', N, flush=True)
        p.stdin.close(); p.wait()
