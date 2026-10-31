"""Turn the fiumaralabs.com favicon into a 1-bit silkscreen bitmap (circle crop, ring outline).

    python scripts/gen_logo.py      # needs pillow; writes hardware/data/logo/logo_bitmap.json

Bright pixels become silkscreen. Threshold 115 on a 48 px autocontrast resize was picked by eye
as the most legible of 95 / 115 / 135.
"""
import json
import os

from PIL import Image, ImageDraw, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N, TH = 48, 115
src = Image.open(os.path.join(ROOT, "hardware/data/logo/fiumaralabs-favicon.png")).convert("L")
g = ImageOps.autocontrast(src.resize((N, N), Image.LANCZOS), cutoff=1)
t = g.point(lambda v: 255 if v > TH else 0)
mask = Image.new("L", (N, N), 0)
ImageDraw.Draw(mask).ellipse((0, 0, N - 1, N - 1), fill=255)
out = Image.new("L", (N, N), 0)
out.paste(t, (0, 0), mask)
ImageDraw.Draw(out).ellipse((0, 0, N - 1, N - 1), outline=255, width=2)
px = out.load()
runs = []   # [row, x_start, x_end_exclusive]
for y in range(N):
    x = 0
    while x < N:
        if px[x, y]:
            s = x
            while x < N and px[x, y]:
                x += 1
            runs.append([y, s, x])
        else:
            x += 1
json.dump({"size": N, "runs": runs}, open(os.path.join(ROOT, "hardware/data/logo/logo_bitmap.json"), "w"))
print(len(runs), "runs")
