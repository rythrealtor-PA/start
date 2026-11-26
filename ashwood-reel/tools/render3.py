# Ashwood reel v3: v1 up to the wolf (0–9 s), then the client's 3 Kling clips (k1 13->14, k2 14->15, k3 16->17)
# with an aligned 15->16 bridge. usage: render3.py stills t1,t2 OUTDIR | render3.py video OUT.mp4 [lo hi]
import sys, math, json, subprocess
sys.path.insert(0, 'tools')
import numpy as np, cv2
import render as R                      # v1, untouched (camera, sweep, wolf cross-fade)
from render import OW, OH, FPS, FULL_H, FULL, ramp, eio, view_map, xform_view, remap_c, blend

# ---- Kling clips (already tone-mapped HLG -> SDR bt709 into kling/fr_kN/*.jpg) ----
NF = {'k1': 73, 'k2': 73, 'k3': 121}
T_K1 = 9.0
T_K2 = T_K1 + NF['k1'] / 24
T_BR = T_K2 + NF['k2'] / 24
BR = 1.1
T_K3 = T_BR + BR
DUR = T_K3 + (NF['k3'] - 1) / 24
KW, KH = 1440, 2580                     # working size of the clip frames (enough for the 1.19x bridge zoom)
SK = np.diag([KW / 1116, KH / 2000, 1.0])  # image px -> clip-frame px
COL = json.load(open('tmp/kling_color.json')); GAIN = np.array(COL['gain'], np.float32); OFF = np.array(COL['off'], np.float32)
_cache = {}
def kimg(clip, i):
    i = int(min(max(i, 0), NF[clip] - 1)); key = (clip, i)
    if key not in _cache:
        im = cv2.imread(f'kling/fr_{clip}/{i:03d}.jpg')
        im = cv2.resize(im, (KW, KH), interpolation=cv2.INTER_AREA).astype(np.float32)
        _cache[key] = np.clip(im * GAIN + OFF, 0, 255)
        if len(_cache) > 10: _cache.pop(next(iter(_cache)))
    return _cache[key]
def kframe(clip, tau):                   # 24 fps clip sampled at any time (adjacent frames blended)
    f = tau * 24; i0 = math.floor(f); w = f - i0
    a = kimg(clip, i0)
    return a if w < 1e-3 or i0 >= NF[clip] - 1 else a * (1 - w) + kimg(clip, i0 + 1) * w
def klayer(clip, tau, A_img):            # A_img: output px -> image coords (3x3)
    A = SK @ A_img
    return cv2.warpAffine(kframe(clip, tau), A[:2], (OW, OH), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)

# ---- 15 -> 16 bridge: k2's last frame (= image 15) into k3's first frame (= image 16), aligned, speed-matched ----
M23 = np.vstack([np.array(json.load(open('tmp/M_k2_last_k3_first.json'))), [0, 0, 1]])
LMAX = math.log(math.hypot(M23[0, 0], M23[1, 0]))          # total zoom of the bridge (1.19x)
K16_V = xform_view(FULL, np.linalg.inv(M23))               # k3's frame, seen in k2 coords
V0_RATE, V1_RATE = 0.075, 0.03                              # zoom speed at the end of k2 / start of k3 (measured)
def bridge_L(u):                                            # cubic Hermite: matches both speeds, reaches LMAX
    h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
    return h10 * V0_RATE * BR + h01 * LMAX + h11 * V1_RATE * BR
def bridge_view(u):
    L = bridge_L(u); k = L / LMAX
    return (FULL[0] + (K16_V[0] - FULL[0]) * k, FULL[1] + (K16_V[1] - FULL[1]) * k, FULL_H * math.exp(-L))

def bump(t, a, b): return math.sin(math.pi * ramp(t, a, b))
def post(out, t):
    mist = .10 + .26 * bump(t, T_BR - .25, T_K3 + .25)
    m = R.mist_layer(t, mist)
    if m is not None: out = out * (1 - m) + m * np.array([200, 228, 245], np.float32)
    R.dust(out, t, 0, 0, .55)
    hl = np.clip(out - 205, 0, None); out += cv2.GaussianBlur(hl, (0, 0), 18) * .55
    return np.clip(out * R.VIG, 0, 255).astype(np.uint8)

VF = view_map(FULL)
def frame_at(t):
    if t < 7.05: return R.frame_at(t)                       # v1 exactly: logo, tree, keys, sun, push + sunlight sweep
    if t < T_K1 + .4:
        # v1 wolf: breathes, mane moves, lifts its head and howls; settles to image 13 exactly at 9.0
        alive = eio(ramp(t, 7.2, 7.7)) * (1 - eio(ramp(t, 8.55, 9.0)))
        mx, my = R.wolf_maps(VF, t, alive)
        out, _ = remap_c(R.IMG[10], mx, my)
        R.sweep(out, t, 6.3, 7.25)
        if alive > 0:
            o = np.linalg.inv(VF) @ np.array([930, 640, 1.0]); R.flare(out, o[0], o[1], .28 * alive, rays=False)
        if t >= T_K1:                                       # hand over to k1 (its first frame is image 13)
            out = blend(out, klayer('k1', t - T_K1, VF), eio(ramp(t, T_K1, T_K1 + .4)))
        return post(out, t)
    if t < T_K2:
        out = klayer('k1', t - T_K1, VF)
        if t > T_K2 - 2 / 24: out = blend(out, klayer('k2', 0, VF), ramp(t, T_K2 - 2 / 24, T_K2))   # k2 starts where k1 ends
        return post(out, t)
    if t < T_BR: return post(klayer('k2', t - T_K2, VF), t)
    if t < T_K3:
        u = (t - T_BR) / BR; V = view_map(bridge_view(u))
        a = klayer('k2', (NF['k2'] - 1) / 24, V)
        b = klayer('k3', 0, M23 @ V)
        return post(blend(a, b, eio(ramp(u, .12, .88))), t)
    return post(klayer('k3', min(t - T_K3, (NF['k3'] - 1) / 24), VF), t)

if __name__ == '__main__':
    print(f'k1 {T_K1:.2f}  k2 {T_K2:.2f}  bridge {T_BR:.2f}  k3 {T_K3:.2f}  end {DUR:.2f}', flush=True)
    mode = sys.argv[1]
    if mode == 'stills':
        ts = [float(x) for x in sys.argv[2].split(',')]; od = sys.argv[3]
        for t in ts: cv2.imwrite(f'{od}/v3_{t:05.2f}.jpg', frame_at(t), [cv2.IMWRITE_JPEG_QUALITY, 90])
    else:
        out = sys.argv[2]; N = int(math.floor(DUR * FPS)) + 1
        lo, hi = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, N)
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
                              '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15',
                              '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        for i in range(lo, min(hi, N)):
            p.stdin.write(frame_at(min(i / FPS, DUR)).tobytes())
            if i % 30 == 0: print('frame', i, '/', N, flush=True)
        p.stdin.close(); p.wait()
