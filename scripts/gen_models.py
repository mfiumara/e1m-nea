"""Write simple VRML 3D models for parts without a stock KiCad model.

    python3 scripts/gen_models.py

KiCad VRML units are 0.1 inch (2.54 mm). Models are centred on the footprint origin, z up from the board.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "hardware", "lib", "fiumara-ae3-som.3dshapes")
U = 1 / 2.54


def box(cx, cy, z0, w, h, t, color, spec=(0.2, 0.2, 0.2), shin=0.2):
    return f"""Transform {{ translation {cx * U:.4f} {cy * U:.4f} {(z0 + t / 2) * U:.4f}
  children Shape {{
    appearance Appearance {{ material Material {{ diffuseColor {color[0]} {color[1]} {color[2]}
      specularColor {spec[0]} {spec[1]} {spec[2]} shininess {shin} }} }}
    geometry Box {{ size {w * U:.4f} {h * U:.4f} {t * U:.4f} }} }} }}
"""


def write(name, shapes):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w") as fh:
        fh.write("#VRML V2.0 utf8\n" + "".join(shapes))


# BDE-BW3501N: 14 x 12.6 mm, 0.8 mm green module PCB, nickel-silver shield can, 3.0 mm total height.
write("BDE-BW3501N.wrl", [
    box(0, 0, 0.05, 14.0, 12.6, 0.8, (0.05, 0.25, 0.12)),
    box(0, 0, 0.85, 13.4, 12.0, 2.15, (0.50, 0.51, 0.52), spec=(0.6, 0.6, 0.6), shin=0.5),
])
print("wrote", OUT)
