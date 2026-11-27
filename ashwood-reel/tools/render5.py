# Ashwood reel FINAL: v3 up to 9.0 s, then the client's Kling clip k5, rendered at 24 fps so every Kling frame
# is used 1:1 (no frame blending). On the Kling part only the gold dust and the vignette are kept.
# usage: render5.py stills t1,t2 OUTDIR | render5.py video OUT.mp4 [lo hi]
import sys, math, json, subprocess
sys.path.insert(0, 'tools')
import numpy as np, cv2
import render3 as V3
from render3 import R, OW, OH, FULL, ramp, eio, view_map, remap_c, blend

FPS = 24
T5 = 9.0
NF5 = 217
DUR = T5 + (NF5 - 1) / 24                       # 18.0 s -> 433 frames
MT = json.load(open('tmp/k5_match.json'))
G5 = np.array(MT['gain'], np.float32); O5 = np.array(MT['off'], np.float32)
Mk = np.vstack([np.array(MT['M']), [0, 0, 1]])   # k5 (resized 1116x2000) -> image-19 coords, ~identity
SK5 = np.diag([1076 / 1116, 1924 / 2000, 1.0]) @ np.linalg.inv(Mk)
VF = view_map(FULL)
def k5layer(i):                                  # i = Kling frame index (integer: no blending)
    im = cv2.imread(f'kling/fr_k5/{int(min(max(i, 0), NF5 - 1)):03d}.jpg').astype(np.float32)
    im = np.clip(im * G5 + O5, 0, 255)
    A = SK5 @ VF
    return cv2.warpAffine(im, A[:2], (OW, OH), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
def post_kling(out, t):
    k = 1 - eio(ramp(t, T5, T5 + .6))            # mist + glow of the logo part fade out over the first 0.6 s
    if k > 0:
        m = R.mist_layer(t, .10 * k)
        if m is not None: out = out * (1 - m) + m * np.array([200, 228, 245], np.float32)
        hl = np.clip(out - 205, 0, None); out += cv2.GaussianBlur(hl, (0, 0), 18) * .55 * k
    R.dust(out, t, 0, 0, .55)
    return np.clip(out * R.VIG, 0, 255).astype(np.uint8)
def frame(i):                                    # output frame i at 24 fps
    t = i / FPS
    if t < T5 - 1e-9: return V3.frame_at(t)      # v3 exactly (0–9 s)
    j = i - int(round(T5 * FPS))                 # Kling frame index, 1:1
    out = k5layer(j)
    if j < 3:                                    # 3-frame soft join: k5's first frame is image 19
        out = blend(remap_c(R.IMG[10], *R.wolf_maps(VF, t, 0))[0], out, (j + 1) / 4)
    return post_kling(out, t)

if __name__ == '__main__':
    N = int(round(DUR * FPS)) + 1
    print(f'k5 from {T5:.2f}  end {DUR:.2f}  frames {N} @ {FPS} fps', flush=True)
    mode = sys.argv[1]
    if mode == 'stills':
        ts = [float(x) for x in sys.argv[2].split(',')]; od = sys.argv[3]
        for t in ts: cv2.imwrite(f'{od}/f_{t:05.2f}.jpg', frame(int(round(t * FPS))), [cv2.IMWRITE_JPEG_QUALITY, 92])
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
