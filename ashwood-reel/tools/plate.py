import cv2, numpy as np, json
I4 = cv2.imread('src/i04.jpg'); F = I4.astype(np.float32); H, W = I4.shape[:2]
small = cv2.resize(I4, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
sky = cv2.resize(cv2.medianBlur(small, 9), (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
dev = np.sqrt(((F - sky) ** 2).sum(2))
meta = json.load(open('assets/sprites.json'))
mask = np.zeros((H, W), np.uint8)
for k, v in meta.items():
    x0, y0, x1, y1 = v['box']; mask[y0:y1, x0:x1] |= (dev[y0:y1, x0:x1] > 12).astype(np.uint8)
mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
# low-frequency fill: inpaint at 1/4 scale (smooth, no stains), soft-composite, add grain
q = 4
sm = cv2.resize(I4, (W // q, H // q), interpolation=cv2.INTER_AREA)
mm = cv2.dilate(cv2.resize(mask, (W // q, H // q), interpolation=cv2.INTER_NEAREST), np.ones((3, 3), np.uint8))
low = cv2.resize(cv2.inpaint(sm, mm, 6, cv2.INPAINT_NS), (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
rng = np.random.default_rng(3); grain = rng.normal(0, 1.6, (H, W, 1)).astype(np.float32)
soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 3)[..., None]
plate = F * (1 - soft) + (low + grain) * soft
# key D on the branch / roof edge: copy a strip from further down the same roof edge (edge direction ~(0.365,-0.931))
x0, y0, x1, y1 = 734, 1192, 866, 1250
hsv = cv2.cvtColor(I4, cv2.COLOR_BGR2HSV)
sub = hsv[y0:y1, x0:x1]
gold = ((sub[..., 0] > 8) & (sub[..., 0] < 30) & (sub[..., 1] > 60) & (sub[..., 2] > 110)).astype(np.uint8)
mD = np.zeros((H, W), np.uint8); mD[y0:y1, x0:x1] = gold
mD[y0:y1, x0:x0 + 34] = 0
mD = cv2.dilate(mD, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
best = None
for s in range(40, 160, 6):   # shift along the roof edge, downward-left
    dx, dy = int(round(-0.365 * s)), int(round(0.931 * s))
    shifted = np.roll(np.roll(F, dy, 0), dx, 1)   # content from (x-dx, y-dy)
    ring = cv2.dilate(mD, np.ones((9, 9), np.uint8)) - mD
    err = np.abs(shifted - F)[ring > 0].mean()
    if best is None or err < best[0]: best = (err, s, shifted)
print('roof-edge patch shift', best[1], 'ring error', round(float(best[0]), 1))
sD = cv2.GaussianBlur(mD.astype(np.float32), (0, 0), 2.5)[..., None]
plate = plate * (1 - sD) + best[2] * sD
cv2.imwrite('assets/plate4.png', np.clip(plate, 0, 255).astype(np.uint8))
# key D sprite (for reference only): golden pixels on the original
a = cv2.GaussianBlur(mD.astype(np.float32), (0, 0), 1.0)[y0:y1, x0:x1]
rgba = np.dstack([F[y0:y1, x0:x1], np.clip(a * 255 * gold.astype(np.float32) * 1.0 + 0, 0, 255)]).astype(np.uint8)
cv2.imwrite('assets/keyD.png', rgba); meta['keyD'] = dict(box=[x0, y0, x1, y1], kind='key'); json.dump(meta, open('assets/sprites.json', 'w'), indent=1)
# tighter alpha for the key sprites (remove the pale halo), keep glints
P = plate
for k in ['keyA', 'keyB', 'keyC']:
    x0, y0, x1, y1 = meta[k]['box']; o = F[y0:y1, x0:x1]; b = P[y0:y1, x0:x1]
    d = np.sqrt(((o - b) ** 2).sum(2)); al = np.clip((d - 14) / 30, 0, 1); al = cv2.GaussianBlur(al, (3, 3), 0)
    c = (o - (1 - al[..., None]) * b) / np.maximum(al[..., None], 0.1)
    cv2.imwrite(f'assets/{k}.png', np.dstack([np.clip(c, 0, 255), al * 255]).astype(np.uint8))
o = cv2.imread('src/i04.jpg'); p = cv2.imread('assets/plate4.png')
cv2.imwrite('/tmp/claude-0/-home-user-start/7f8dc566-25ff-5876-9bec-42cca704db29/scratchpad/sheets/plate2.jpg', np.hstack([o[480:1350, 520:1116], np.full((870, 8, 3), 40, np.uint8), p[480:1350, 520:1116]]))
