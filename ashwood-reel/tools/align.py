import cv2, numpy as np, sys, json
def load(n): return cv2.imread(f'src/i{n:02d}.jpg')
sift = cv2.SIFT_create(8000)
def match(a, b, maska=None, maskb=None):
    A, B = load(a), load(b)
    ga, gb = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY), cv2.cvtColor(B, cv2.COLOR_BGR2GRAY)
    ka, da = sift.detectAndCompute(ga, maska); kb, db = sift.detectAndCompute(gb, maskb)
    m = cv2.BFMatcher().knnMatch(da, db, k=2)
    good = [x for x, y in m if x.distance < .75 * y.distance]
    pa = np.float32([ka[g.queryIdx].pt for g in good]); pb = np.float32([kb[g.trainIdx].pt for g in good])
    if len(good) < 6: return None, len(good), 0
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=6, maxIters=20000)
    return M, len(good), int(inl.sum()) if inl is not None else 0
res = {}
for a, b in [(1, 4), (3, 4), (1, 10), (10, 9), (9, 8), (8, 7), (7, 6), (6, 11), (1, 9), (10, 8)]:
    M, ng, ni = match(a, b)
    if M is None: print(a, b, 'no match', ng); continue
    s = float(np.hypot(M[0, 0], M[1, 0])); rot = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
    print(f'{a}->{b}: good {ng} inliers {ni}  scale {s:.3f} rot {rot:.2f} tx {M[0,2]:.1f} ty {M[1,2]:.1f}')
    res[f'{a}->{b}'] = dict(M=M.tolist(), inliers=ni, good=ng)
json.dump(res, open('tmp/align.json', 'w'), indent=1)
