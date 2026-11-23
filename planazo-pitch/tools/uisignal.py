import sys, subprocess, numpy as np
clip, t0, dur = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
regions = [tuple(map(int, r.split(','))) for r in sys.argv[4:]]  # x0,y0,x1,y1 in source px
W, H = 295, 639
raw = subprocess.run(['ffmpeg','-v','error','-ss',str(t0),'-i',f'src/{clip}.mp4','-t',str(dur),'-vf',f'scale={W}:{H},format=gray','-r','60','-f','rawvideo','-'],capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
s = W/1180
prev = None
for i, f in enumerate(fr):
    vals = [f[int(y0*s):int(y1*s), int(x0*s):int(x1*s)].mean() for x0,y0,x1,y1 in regions]
    d = '' if prev is None else ' '.join(f'{v-p:+6.1f}' for v,p in zip(vals,prev))
    if prev is None or max(abs(v-p) for v,p in zip(vals,prev)) > 3: print(f'{t0+i/60:7.3f}', ' '.join(f'{v:6.1f}' for v in vals), '|', d)
    prev = vals
