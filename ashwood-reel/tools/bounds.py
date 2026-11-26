import sys; sys.path.insert(0, 'tools')
import numpy as np, render as R
def corners(A): return [A @ np.array([x, y, 1.0]) for x, y in [(0, 0), (R.OW, 0), (0, R.OH), (R.OW, R.OH)]]
bad = []
for i in range(int(R.DUR * 30)):
    t = i / 30; L = []
    if t < 7.05:
        V = R.view_map(R.camA(t)); L.append(('img1', V))
        if 1.5 < t < 4.62: L.append(('img4', R.M14 @ V))
        if t > 6.5: L.append(('img10', R.M1_10 @ V))
    else:
        V = R.view_map(R.camB(t))
        if t < 12: L.append(('img10/9', V))
        if t > 9.7: L.append(('img8/7/6', R.M10_8 @ V))
        if t > 12.45: L.append(('img11', R.view_map(R.cam11(t))))
    for name, A in L:
        for c in corners(A):
            if c[0] < -2 or c[1] < -2 or c[0] > 1118 or c[1] > 2002: bad.append((round(t, 2), name, np.round(c[:2]).tolist())); break
print('out-of-image frames:', len(bad)); print(bad[:12])
