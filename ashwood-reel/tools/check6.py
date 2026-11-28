# v6 checks: frame-to-frame jumps over the whole reel, the k4 -> k6 join (18.0 s) and the slow tail (22.0 s), sharpness vs the Kling source
import sys, cv2, numpy as np
f = sys.argv[1]; cap = cv2.VideoCapture(f); prev = None; d = []; frames = {}
keep = {431, 432, 433, 434, 500, 528, 591}
i = 0
while True:
    ok, fr = cap.read()
    if not ok: break
    if i in keep: frames[i] = fr
    g = cv2.resize(fr, (270, 480), interpolation=cv2.INTER_AREA).astype(np.float32)
    if prev is not None: d.append(np.abs(g - prev).mean())
    prev = g; i += 1
d = np.array(d); med = np.median(d)
spikes = [(k + 1, round((k + 1) / 24, 2), round(float(v), 1)) for k, v in enumerate(d) if v > max(3 * med, med + 6) and (k == 0 or v > 2.2 * d[k - 1])]
print('frames', i, '| median diff', round(float(med), 2), '| jumps:', spikes)
print('k4 -> k6 join (frame 432|433):', [round(float(x), 2) for x in d[428:437]])
print('into the slow tail (frame 528):', [round(float(x), 2) for x in d[524:533]], '| last frames:', [round(float(x), 2) for x in d[-5:]])
def sharp(im): return cv2.Laplacian(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
for oi, kj in [(433, 1), (500, 68), (528, 96)]:
    src = cv2.resize(cv2.imread(f'kling/fr_k6/{kj:03d}.jpg'), (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
    print(f'sharpness output frame {oi} / k6 frame {kj}: {sharp(frames[oi]) / sharp(src) * 100:.0f}%')
