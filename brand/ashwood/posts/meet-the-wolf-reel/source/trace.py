import numpy as np, potrace
from PIL import Image
m = ~(np.asarray(Image.open('wolf-mask2.png').convert('L')) > 127)
h, w = m.shape
bm = potrace.Bitmap(m)
pl = bm.trace(turdsize=200, alphamax=1.25, opticurve=True, opttolerance=1.0)
parts = []
for curve in pl:
    s = curve.start_point
    d = [f"M{s.x:.1f},{s.y:.1f}"]
    for seg in curve.segments:
        if seg.is_corner:
            d.append(f"L{seg.c.x:.1f},{seg.c.y:.1f}L{seg.end_point.x:.1f},{seg.end_point.y:.1f}")
        else:
            d.append(f"C{seg.c1.x:.1f},{seg.c1.y:.1f} {seg.c2.x:.1f},{seg.c2.y:.1f} {seg.end_point.x:.1f},{seg.end_point.y:.1f}")
    d.append("Z")
    parts.append("".join(d))
path = " ".join(parts)
open('wolf-path.txt','w').write(path)
svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w//4}" height="{h//4}"><rect width="100%" height="100%" fill="#08233B"/><path d="{path}" fill="#C7CED4" fill-rule="evenodd"/></svg>'
open('wolf.svg','w').write(svg)
print(w, h, len(pl), len(path))
