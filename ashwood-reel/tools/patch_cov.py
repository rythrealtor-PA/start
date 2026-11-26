# replaces frame_at() in render.py with a coverage-aware version (layers fade into the one below outside their image)
p = 'tools/render.py'; s = open(p).read()
a = s.index('def blend(a, b, k):'); b = s.index('gy, gx = np.mgrid[0:OH, 0:OW].astype(np.float32)\nVIG')
new = r'''def blend(a, b, k):
    if np.isscalar(k): return a if k <= 0 else (b if k >= 1 else a * (1 - k) + b * k)
    return a * (1 - k) + b * k
# coverage: 1 inside a source image, feathered to 0 at its edges (so a layer never shows mirrored borders)
COV = np.ones((2000, 1116), np.float32); F_ = 28
ramp_ = np.linspace(0, 1, F_, dtype=np.float32)
COV[:F_] *= ramp_[:, None]; COV[-F_:] *= ramp_[::-1, None]; COV[:, :F_] *= ramp_[None]; COV[:, -F_:] *= ramp_[None, ::-1]
def warp_c(img, A):
    w = cv2.warpAffine(img, A[:2], (OW, OH), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    c = cv2.warpAffine(COV, A[:2], (OW, OH), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return w, c[..., None]
def remap_c(img, mx, my):
    w = cv2.remap(img, mx, my, cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    c = cv2.remap(COV, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return w, c[..., None]
def frame_at(t):
    if t < 7.05:
        vA = camA(t); V = view_map(vA); Vout = np.linalg.inv(V)
        base = blend(IMG[12].astype(np.float32), IMG[1].astype(np.float32), eio(ramp(t, .1, 1.05)))
        if t > 4.9: base = blend(base, RELIT.astype(np.float32), eio(ramp(t, 5.0, 5.9)))
        out, _ = warp_c(base, V)
        k4 = eio(ramp(t, 1.5, 1.95)) * (1 - eio(ramp(t, 4.12, 4.62)))
        if k4 > 0:
            amp = 7.5 * eio(ramp(t, 1.7, 2.3)) * (1 - eio(ramp(t, 4.1, 4.7)))
            mx, my = sway_maps(M14 @ V, t, amp)
            T4, c4 = remap_c(PLATE4, mx, my)
            out = blend(out, T4, k4 * c4)
        for L_ in LEAVES:
            st = leaf_state(L_, t)
            if st:
                p, rot, sc, a, g = st
                spd = (breeze(t + .02)[0] - breeze(t)[0]) * 1.7 / (vA[2] / OH)
                paste_sprite(out, L_['sp'], Vout, p, rot, sc, a * (1 - ramp(t, 6.0, 6.4)), S41, gain=.8 + .5 * g, blur_dx=spd)
        for K in KEYS:
            st = key_state(K, t)
            if st:
                p, rot, sc, a = st
                spd = (breeze(t + .02)[0] - breeze(t)[0]) * 1.7 / (vA[2] / OH)
                paste_sprite(out, K['sp'], Vout, p, rot, sc, a * (1 - ramp(t, 6.0, 6.4)), S41, gain=1.05, blur_dx=spd)
                if t < K['te'] + .55:
                    o = Vout @ np.array([p[0], p[1], 1.0]); glint(out, o[0], o[1], 1.1 * math.sin(math.pi * ramp(t, K['te'], K['te'] + .55)))
        sk = eio(ramp(t, 5.0, 5.75)) * (1 - eio(ramp(t, 6.35, 6.9)))
        if sk > 0:
            o = Vout @ np.array([905, 862, 1.0]); flare(out, o[0], o[1], .75 * sk)
        if t > 6.5:
            mx, my = wolf_maps(M1_10 @ V, t, 0)
            W10i, c10 = remap_c(IMG[10], mx, my)
            out = blend(out, W10i, eio(ramp(t, 6.55, 7.05)) * c10)
        sweep(out, t, 6.3, 7.25)
    else:
        vB = camB(t); V = view_map(vB)
        alive = eio(ramp(t, 7.2, 7.7)) * (1 - eio(ramp(t, 9.3, 10.0)))
        out = None
        if t < 12.0:
            mx, my = wolf_maps(V, t, alive)
            out, _ = remap_c(IMG[10], mx, my)
            k9 = eio(ramp(t, 9.0, 9.75))
            if k9 > 0:
                L9, _ = remap_c(IMG[9], mx, my); out = blend(out, L9, k9)
        A8 = M10_8 @ V
        for n, (t0, t1) in ((8, (9.7, 10.5)), (7, (10.5, 11.2)), (6, (11.2, 12.0))):
            k = eio(ramp(t, t0, t1))
            if k > 0 and (t < 12.0 or n == 6):
                Ln, cn = warp_c(IMG[n], A8)
                out = Ln if out is None else blend(out, Ln, k * cn)
        if t >= 12.45:
            L11, _ = warp_c(IMG[11], view_map(cam11(t)))
            out = blend(out, L11, eio(ramp(t, 12.45, 13.1)))
        if 7.0 <= t < 9.6:
            o = np.linalg.inv(V) @ np.array([930, 640, 1.0]); flare(out, o[0], o[1], .28 * alive, rays=False)
    mist_amt = .10 + .30 * math.sin(math.pi * ramp(t, 8.9, 12.4)) + .14 * math.sin(math.pi * ramp(t, 12.2, 13.6))
    m = mist_layer(t, mist_amt)
    if m is not None: out = out * (1 - m) + m * np.array([200, 228, 245], np.float32)
    dust(out, t, 0, 0, .55 + .25 * ramp(t, 8.5, 11))
    hl = np.clip(out - 205, 0, None); out += cv2.GaussianBlur(hl, (0, 0), 18) * .55
    return np.clip(out * VIG, 0, 255).astype(np.uint8)

'''
s = s[:a] + new + s[b:]
old = "TREE_V = xform_view(FULL, INV14)          # image 4's full frame, seen in image 1"
assert s.count(old) == 1
s = s.replace(old, "TREE_V = xform_view((558, 1000, FULL_H * .97), INV14)   # image 4's frame, a hair tighter (it is rotated 0.76 deg)")
open(p, 'w').write(s); print('patched')
