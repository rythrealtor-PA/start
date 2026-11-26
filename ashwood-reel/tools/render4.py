# Ashwood reel v4: v3 up to 9.0 s (frame = image 19), then the client's single Kling clip k4 (wolf -> mist -> cliff -> river)
# usage: render4.py stills t1,t2 OUTDIR | render4.py video OUT.mp4 [lo hi]
import sys, math, json, subprocess
sys.path.insert(0, 'tools')
import numpy as np, cv2
import render3 as V3
from render3 import R, OW, OH, FPS, FULL, ramp, eio, view_map, remap_c, blend, post as post3

T4 = 9.0
NF4 = 217
DUR = T4 + (NF4 - 1) / 24                      # 18.0 s
MT = json.load(open('tmp/k4_match.json'))
G4 = np.array(MT['gain'], np.float32); O4 = np.array(MT['off'], np.float32)
Mk = np.vstack([np.array(MT['M']), [0, 0, 1]])  # k4 (resized 1116x2000) -> image-19 coords, ~identity
SK4 = np.diag([1076 / 1116, 1924 / 2000, 1.0]) @ np.linalg.inv(Mk)   # image coords -> k4 pixels
_c = {}
def k4img(i):
    i = int(min(max(i, 0), NF4 - 1))
    if i not in _c:
        _c[i] = np.clip(cv2.imread(f'kling/fr_k4/{i:03d}.jpg').astype(np.float32) * G4 + O4, 0, 255)
        if len(_c) > 8: _c.pop(next(iter(_c)))
    return _c[i]
def k4frame(tau):
    f = tau * 24; i0 = math.floor(f); w = f - i0
    a = k4img(i0)
    return a if w < 1e-3 or i0 >= NF4 - 1 else a * (1 - w) + k4img(i0 + 1) * w
VF = view_map(FULL)
def k4layer(tau):
    A = SK4 @ VF
    return cv2.warpAffine(k4frame(tau), A[:2], (OW, OH), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
def post(out, t):   # same look as v3 (no bridge mist any more)
    m = R.mist_layer(t, .10)
    out = out * (1 - m) + m * np.array([200, 228, 245], np.float32)
    R.dust(out, t, 0, 0, .55)
    hl = np.clip(out - 205, 0, None); out += cv2.GaussianBlur(hl, (0, 0), 18) * .55
    return np.clip(out * R.VIG, 0, 255).astype(np.uint8)
def frame_at(t):
    if t < T4: return V3.frame_at(t)                       # v3 exactly (0–9 s)
    out = k4layer(min(t - T4, (NF4 - 1) / 24))
    if t < T4 + .1:                                        # 3-frame soft join: k4's first frame is image 19
        out = blend(remap_c(R.IMG[10], *R.wolf_maps(VF, t, 0))[0], out, eio(ramp(t, T4, T4 + .1)))
    return post(out, t)

if __name__ == '__main__':
    print(f'k4 from {T4:.2f}  end {DUR:.2f}', flush=True)
    mode = sys.argv[1]
    if mode == 'stills':
        ts = [float(x) for x in sys.argv[2].split(',')]; od = sys.argv[3]
        for t in ts: cv2.imwrite(f'{od}/v4_{t:05.2f}.jpg', frame_at(t), [cv2.IMWRITE_JPEG_QUALITY, 90])
    else:
        out = sys.argv[2]; N = int(round(DUR * FPS)) + 1
        lo, hi = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, N)
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
                              '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15',
                              '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        for i in range(lo, min(hi, N)):
            p.stdin.write(frame_at(min(i / FPS, DUR)).tobytes())
            if i % 30 == 0: print('frame', i, '/', N, flush=True)
        p.stdin.close(); p.wait()
