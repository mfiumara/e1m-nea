"""Render every symbol unit and footprint of the project library to cropped PNGs for review.

usage: DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib python scripts/render_lib.py <outdir>
needs: kicad-cli, cairosvg, pillow
"""
import glob
import io
import os
import shutil
import subprocess
import sys

import cairosvg
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fiumara-ae3-som-lib"
shutil.rmtree(out, ignore_errors=True)
for d in ("sym", "fp", "png"):
    os.makedirs(os.path.join(out, d))
subprocess.run(["kicad-cli", "sym", "export", "svg", "-o", f"{out}/sym", f"{ROOT}/hardware/lib/fiumara-ae3-som.kicad_sym"],
               check=True, capture_output=True)
subprocess.run(["kicad-cli", "fp", "export", "svg", "--layers",
                "F.Cu,B.Cu,F.Paste,F.SilkS,B.SilkS,F.Fab,B.Fab,F.CrtYd,B.CrtYd",
                "-o", f"{out}/fp", f"{ROOT}/hardware/lib/fiumara-ae3-som.pretty"], check=True, capture_output=True)
for svg in sorted(glob.glob(f"{out}/sym/*.svg") + glob.glob(f"{out}/fp/*.svg")):
    png = cairosvg.svg2png(url=svg, scale=(8 if "AE3_SoM_LGA" in svg else 25) if "/fp/" in svg else 5, background_color="white")
    im = Image.open(io.BytesIO(png)).convert("RGB")
    bb = ImageOps.invert(im).getbbox()
    if bb:
        im = im.crop((max(0, bb[0] - 20), max(0, bb[1] - 20), bb[2] + 20, bb[3] + 20))
    im.thumbnail((2000, 2000))
    p = f"{out}/png/{os.path.basename(svg)[:-4]}.png"
    im.save(p)
    print(p, im.size)
