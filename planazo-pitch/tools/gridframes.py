# usage: gridframes.py out.jpg clip:t[:label] ...   -> full-res frames with a source-pixel grid, tiled
import sys, subprocess, io
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]; specs = sys.argv[2:]
S = 0.36
tiles = []
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15) if __import__('os').path.exists('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf') else ImageFont.load_default()
for sp in specs:
    clip, t = sp.split(':')[:2]
    raw = subprocess.run(['ffmpeg','-v','error','-ss',t,'-i',f'src/{clip}.mp4','-frames:v','1','-f','image2pipe','-vcodec','png','-'],capture_output=True).stdout
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    im.save(f'ref/{clip}_{t}.png')
    w,h = im.size; im = im.resize((int(w*S), int(h*S)), Image.LANCZOS)
    d = ImageDraw.Draw(im, 'RGBA')
    for x in range(0, w, 100):
        d.line([(x*S,0),(x*S,h*S)], fill=(0,160,255,90 if x%500 else 200), width=1)
        if x%200==0: d.text((x*S+2, 2), str(x), fill=(0,90,200,255), font=font)
    for y in range(0, h, 100):
        d.line([(0,y*S),(w*S,y*S)], fill=(255,0,160,90 if y%500 else 200), width=1)
        if y%200==0: d.text((2, y*S+2), str(y), fill=(200,0,120,255), font=font)
    d.rectangle([0,h*S-24,200,h*S], fill=(0,0,0,200)); d.text((4,h*S-21), f'{clip} @ {t}', fill=(255,255,0,255), font=font)
    tiles.append(im)
W = sum(t.width for t in tiles)+6*(len(tiles)-1); H = max(t.height for t in tiles)
sheet = Image.new('RGB',(W,H),(30,30,30)); x=0
for t in tiles: sheet.paste(t,(x,0)); x+=t.width+6
sheet.save(out, quality=88)
