import sys
from PIL import Image, ImageDraw, ImageFont
# gridimg.py out.jpg scale img:x0,y0,x1,y1 ...
out, S = sys.argv[1], float(sys.argv[2]); tiles = []
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
for sp in sys.argv[3:]:
    n, box = sp.split(':'); x0, y0, x1, y1 = map(int, box.split(','))
    im = Image.open(f'src/i{int(n):02d}.jpg').convert('RGB').crop((x0, y0, x1, y1))
    im = im.resize((int(im.width * S), int(im.height * S)), Image.LANCZOS); d = ImageDraw.Draw(im, 'RGBA')
    for x in range((x0 // 50 + 1) * 50, x1, 50):
        X = (x - x0) * S; d.line([(X, 0), (X, im.height)], fill=(0, 200, 255, 200 if x % 100 == 0 else 70))
        if x % 100 == 0: d.text((X + 2, 2), str(x), fill=(0, 220, 255, 255), font=f)
    for y in range((y0 // 50 + 1) * 50, y1, 50):
        Y = (y - y0) * S; d.line([(0, Y), (im.width, Y)], fill=(255, 60, 200, 200 if y % 100 == 0 else 70))
        if y % 100 == 0: d.text((2, Y + 2), str(y), fill=(255, 90, 210, 255), font=f)
    d.rectangle([0, im.height - 18, 60, im.height], fill=(0, 0, 0, 200)); d.text((3, im.height - 17), f'img {n}', fill='yellow', font=f)
    tiles.append(im)
W = sum(t.width for t in tiles) + 6 * (len(tiles) - 1); H = max(t.height for t in tiles)
c = Image.new('RGB', (W, H), (30, 30, 30)); x = 0
for t in tiles: c.paste(t, (x, 0)); x += t.width + 6
c.save(out, quality=88)
