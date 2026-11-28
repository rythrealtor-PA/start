# Ashwood reel v6 (long): draft v4 (v3 0–9 s + Kling k4 9–18 s) continued by Kling k6 (river -> forest -> the house)
# 24 fps, every Kling frame used 1:1; k6 frame 0 == k4's last frame, so k6 starts at its frame 1 (no duplicate).
# k6's last, static second is played slower (house + slow push) so v4's 3.4 s musical ending fits after the arrival.
# usage: render6.py stills t1,t2 OUTDIR | render6.py video OUT.mp4 [lo hi]
import sys, math, json, subprocess
sys.path.insert(0, 'tools')
import numpy as np, cv2
import render3 as V3
from render3 import R, OW, OH, FULL, FULL_H, ramp, eio, view_map, remap_c, blend

FPS = 24
T4 = 9.0
NF4, NF6 = 217, 121
I4 = int(round(T4 * FPS))                  # output frame where k4 starts (216)
I6 = I4 + NF4 - 1                          # output frame of k6's frame 0 (= k4's last frame, not shown twice) -> 432
J_SLOW = 96                                # k6 is static from here: its last second is played slower, ending on frame 120
N = 592                                    # 24.63 s: room for v4's 3.4 s ending after the house arrives
I_SLOW = I6 + J_SLOW                       # 528 (22.0 s)
DUR = N / FPS
MT = json.load(open('tmp/k4_match.json'))
G = np.array(MT['gain'], np.float32); O = np.array(MT['off'], np.float32)
Mk = np.vstack([np.array(MT['M']), [0, 0, 1]])
SKK = np.diag([1076 / 1116, 1924 / 2000, 1.0]) @ np.linalg.inv(Mk)   # image coords -> Kling pixels (k4 and k6 share it)
C6 = json.load(open('tmp/k6_to_k4.json'))     # tiny colour match of k6 to k4's last frame, faded out over 1.5 s
G6 = np.array(C6['gain'], np.float32); O6 = np.array(C6['off'], np.float32)
VF = view_map(FULL)
_c = {}
def kimg(clip, j):
    key = (clip, j)
    if key not in _c:
        _c[key] = cv2.imread(f'kling/fr_{clip}/{j:03d}.jpg').astype(np.float32)
        if len(_c) > 6: _c.pop(next(iter(_c)))
    return _c[key]
def kling(clip, p, V=VF, w6=0.0):
    j0 = int(math.floor(p)); w = p - j0
    im = kimg(clip, j0)
    if w > 1e-3: im = im * (1 - w) + kimg(clip, j0 + 1) * w     # only used on k6's static tail (motion < 0.3 px/frame)
    if w6 > 0: im = im * (1 + (G6 - 1) * w6) + O6 * w6
    im = np.clip(im * G + O, 0, 255)
    A = SKK @ V
    return cv2.warpAffine(im, A[:2], (OW, OH), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
def post_kling(out, t):
    k = 1 - eio(ramp(t, T4, T4 + .6))        # mist + glow of the logo part fade out over 0.6 s (same as FINAL)
    if k > 0:
        m = R.mist_layer(t, .10 * k)
        if m is not None: out = out * (1 - m) + m * np.array([200, 228, 245], np.float32)
        hl = np.clip(out - 205, 0, None); out += cv2.GaussianBlur(hl, (0, 0), 18) * .55 * k
    R.dust(out, t, 0, 0, .55)
    return np.clip(out * R.VIG, 0, 255).astype(np.uint8)
A_PUSH = .4
def push(u):                                # slow push-in on the house: eases in, then keeps moving to the last frame
    p = u * u / (2 * A_PUSH) if u < A_PUSH else u - A_PUSH / 2
    return p / (1 - A_PUSH / 2)
def frame(i):
    t = i / FPS
    if i < I4: return V3.frame_at(t)                                 # 0–9 s exactly as v3/v4
    if i <= I6:                                                      # k4 frames 0..216, 1:1
        j = i - I4; out = kling('k4', j)
        if j < 3: out = blend(remap_c(R.IMG[10], *R.wolf_maps(VF, t, 0))[0], out, (j + 1) / 4)
        return post_kling(out, t)
    j = i - I6; w6 = 1 - eio(min(1.0, (j - 1) / 36))
    if i <= I_SLOW: return post_kling(kling('k6', j, w6=w6), t)      # k6 frames 1..96, 1:1
    u = (i - I_SLOW) / (N - 1 - I_SLOW)                              # 0..1 over the last 2.6 s
    kx = (N - 1 - I_SLOW) / (NF6 - 1 - J_SLOW)                       # starts at exactly 1 source frame per output frame
    p = J_SLOW + (NF6 - 1 - J_SLOW) * (1 - (1 - u) ** kx)
    z = 1 + .03 * push(u)
    return post_kling(kling('k6', min(p, NF6 - 1), view_map((FULL[0], FULL[1], FULL_H / z))), t)

if __name__ == '__main__':
    print(f'k4 at {I4/FPS:.3f}s, k6 (frame 1) at {(I6+1)/FPS:.3f}s, slow tail from {I_SLOW/FPS:.3f}s, {N} frames = {DUR:.3f}s', flush=True)
    mode = sys.argv[1]
    if mode == 'stills':
        ts = [float(x) for x in sys.argv[2].split(',')]; od = sys.argv[3]
        for t in ts: cv2.imwrite(f'{od}/g_{t:05.2f}.jpg', frame(int(round(t * FPS))), [cv2.IMWRITE_JPEG_QUALITY, 92])
    else:
        out = sys.argv[2]
        lo, hi = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, N)
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
                              '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '11',
                              '-x264-params', 'aq-mode=3', '-profile:v', 'high', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                              '-color_range', 'tv', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        for i in range(lo, min(hi, N)):
            p.stdin.write(frame(i).tobytes())
            if i % 24 == 0: print('frame', i, '/', N, flush=True)
        p.stdin.close(); p.wait()
