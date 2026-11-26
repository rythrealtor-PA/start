import cv2, numpy as np, json
I4 = cv2.imread('src/i04.jpg'); F = I4.astype(np.float32)
H, W = I4.shape[:2]
# smooth sky estimate (objects are small): downsample, median, upsample
small = cv2.resize(I4, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
sky = cv2.resize(cv2.medianBlur(small, 9), (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
dev = np.sqrt(((F - sky) ** 2).sum(2))
# object boxes in image-4 coords (x0,y0,x1,y1, kind)
boxes = {
 'keyA': (845, 560, 1018, 700, 'key'), 'keyB': (952, 620, 1100, 765, 'key'), 'keyC': (808, 795, 962, 950, 'key'),
 'leaf1': (575, 612, 640, 655, 'leaf'), 'leaf2': (710, 725, 795, 770, 'leaf'), 'leaf3': (835, 1000, 902, 1065, 'leaf'),
 'leaf4': (785, 625, 810, 650, 'leaf'), 'leaf5': (748, 845, 775, 870, 'leaf'), 'leaf6': (1075, 515, 1116, 555, 'leaf'), 'leaf7': (1072, 800, 1116, 860, 'leaf'),
}
mask = np.zeros((H, W), np.uint8)
for k, (x0, y0, x1, y1, kind) in boxes.items():
    m = (dev[y0:y1, x0:x1] > 16).astype(np.uint8)
    mask[y0:y1, x0:x1] |= m
# sparkles / glints near keys too
mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
# key D on the branch: tight box, golden pixels
x0, y0, x1, y1 = 736, 1196, 862, 1246
hsv = cv2.cvtColor(I4, cv2.COLOR_BGR2HSV)
sub = hsv[y0:y1, x0:x1]; gold = ((sub[..., 0] > 8) & (sub[..., 0] < 30) & (sub[..., 1] > 70) & (sub[..., 2] > 120)).astype(np.uint8)
gold[:, :40] = 0   # leave the golden leaf at the bow side alone
maskD = np.zeros((H, W), np.uint8); maskD[y0:y1, x0:x1] = gold
maskD = cv2.dilate(maskD, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
plate = cv2.inpaint(I4, mask, 9, cv2.INPAINT_TELEA)
plate = cv2.inpaint(plate, maskD, 7, cv2.INPAINT_NS)
cv2.imwrite('assets/plate4.png', plate)
P = plate.astype(np.float32)
meta = {}
for k, (x0, y0, x1, y1, kind) in boxes.items():
    o = F[y0:y1, x0:x1]; b = P[y0:y1, x0:x1]
    d = np.sqrt(((o - b) ** 2).sum(2)); a = np.clip((d - 6) / 34, 0, 1)
    a = cv2.GaussianBlur(a, (3, 3), 0)
    c = (o - (1 - a[..., None]) * b) / np.maximum(a[..., None], 0.08)
    rgba = np.dstack([np.clip(c, 0, 255), a * 255]).astype(np.uint8)
    cv2.imwrite(f'assets/{k}.png', rgba); meta[k] = dict(box=[x0, y0, x1, y1], kind=kind)
json.dump(meta, open('assets/sprites.json', 'w'), indent=1)
# relight: low-frequency light of image 2 transferred onto image 1
I1 = cv2.imread('src/i01.jpg').astype(np.float32); I2 = cv2.imread('src/i02.jpg').astype(np.float32)
b1 = cv2.GaussianBlur(I1, (0, 0), 28) + 4; b2 = cv2.GaussianBlur(I2, (0, 0), 28) + 4
ratio = np.clip(b2 / b1, 0.6, 2.4)
cv2.imwrite('assets/relight.png', np.clip(I1 * ratio, 0, 255).astype(np.uint8))
np.save('assets/ratio12.npy', ratio.astype(np.float16))
g = cv2.GaussianBlur(cv2.cvtColor(I2.astype(np.uint8), cv2.COLOR_BGR2GRAY), (0, 0), 20)
_, mx, _, loc = cv2.minMaxLoc(g[300:1100, 600:]); print('sun in image 2 at', (loc[0] + 600, loc[1] + 300), mx)
# manual image1 -> image10 similarity from structure points
p1 = np.float32([[690, 845], [680, 635], [990, 955], [810, 415]]); p10 = np.float32([[620, 1550], [614, 1048], [1060, 1714], [798, 417]])
M, _ = cv2.estimateAffinePartial2D(p1, p10, method=cv2.LMEDS)
print('M1->10 scale', np.hypot(M[0, 0], M[1, 0]), 'residuals', np.round(np.abs((p1 @ M[:, :2].T + M[:, 2]) - p10).max(1), 1))
al = json.load(open('tmp/align.json')); al['1->10'] = dict(M=M.tolist()); json.dump(al, open('tmp/align.json', 'w'), indent=1)
