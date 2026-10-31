"""Generate the Rev A placement floorplan (no nets, no routing) as hardware/fiumara-ae3-som.kicad_pcb.

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
        scripts/gen_floorplan.py

Layout: SoC top right, Wi-Fi module bottom left with the antenna corner at the ANT edge pad
(pad 30), power stages on the left, Ethernet PHY and its crystal bottom right. Package sizes from the
datasheets.
Coordinates below are mm from the module's top-left corner (top view).
"""
import os

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "hardware", "fiumara-ae3-som.kicad_pcb")
OX, OY = 100.0, 100.0      # board origin on the sheet
KICAD_FP = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
LOCAL_FP = os.path.join(ROOT, "hardware", "lib", "fiumara-ae3-som.pretty")

# ref, library, footprint, x, y, rotation, value
PLACEMENT = [
    ("J1", None, "AE3_SoM_LGA-244_35x35mm_P1.0mm_BottomPads", 17.5, 17.5, 0, "AE3 SoM edge"),
    ("U1", None, "Alif_FBGA-194_10x10mm_Layout19x19_P0.5mm", 26.25, 10.9, 0, "AE302F80F55D5LE"),
    ("U2", None, "BDE-BW3501N_14x12.6mm", 11.5, 27.0, 90, "BDE-BW3501N42"),
    ("U3", None, "TI_VAF0024A_WQFN-HR-24_3.5x3.5mm_P0.5mm", 7.3, 16.6, 0, "TPS6521402"),
    ("L1", "Inductor_SMD", "L_1008_2520Metric", 3.4, 16.6, 90, "470nH BUCK1"),
    ("L2", "Inductor_SMD", "L_1008_2520Metric", 12.0, 16.6, 90, "470nH BUCK2"),
    ("L3", "Inductor_SMD", "L_1008_2520Metric", 18.6, 18.2, 0, "470nH BUCK3"),
    ("L4", "Inductor_SMD", "L_1008_2520Metric", 28.4, 3.0, 0, "Alif VSW inductor"),
    ("U4", "Package_DFN_QFN", "Texas_RMQ0024A_WQFN-24-1EP_3x3mm_P0.4mm_EP1.9x1.9mm", 28.0, 29.3, 0, "DP83825I"),
    ("Y2", "Crystal", "Crystal_SMD_2520-4Pin_2.5x2.0mm", 32.3, 32.4, 0, "25MHz"),
    ("Y1", "Crystal", "Crystal_SMD_2016-4Pin_2.0x1.6mm", 18.6, 13.9, 90, "HFXO"),
    ("Y3", "Crystal", "Crystal_SMD_3215-2Pin_3.2x1.5mm", 33.3, 9.0, 90, "32.768kHz"),
    ("U5", "Package_SON", "VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm", 29.6, 22.0, 0, "TCAN1044AV (DNP)"),
    ("J2", "Connector_Coaxial", "U.FL_Hirose_U.FL-R-SMT-1_Vertical", 2.7, 23.6, 0, "U.FL (DNP)"),
]

M3D = "${KICAD10_3DMODEL_DIR}"
# ref -> (model path, scale xyz): stand-in models for parts without an exact stock model
MODELS = {
    "U1": (f"{M3D}/Package_BGA.3dshapes/BGA-256_11.0x11.0mm_Layout20x20_P0.5mm_Ball0.3mm_Pad0.25mm_NSMD.step", (10 / 11, 10 / 11, 1.0)),
    "U2": ("${KIPRJMOD}/lib/fiumara-ae3-som.3dshapes/BDE-BW3501N.wrl", (1, 1, 1)),
    "U3": (f"{M3D}/Package_DFN_QFN.3dshapes/Texas_RTW_WQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm.step", (0.875, 0.875, 1.0)),
    "U4": (f"{M3D}/Package_DFN_QFN.3dshapes/Texas_RRW0024A_WQFN-24-1EP_3x3mm_P0.4mm_EP1.9x1.9mm.step", (1, 1, 1)),
}

# Reserved areas: DNP OSPI memories (HyperRAM + NOR).
RESERVED = [("OSPI HyperRAM (DNP)", 4.5, 5.0, 10.5, 10.5), ("OSPI NOR (DNP)", 11.8, 5.0, 17.8, 10.5)]


def mm(v):
    return pcbnew.FromMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def add_logo(board, x0, y0, pitch):
    """Fiumara Labs logo: the fiumaralabs.com favicon as a 1-bit silkscreen bitmap
    (hardware/data/logo/logo_bitmap.json from scripts/gen_logo.py), one rectangle per pixel run."""
    import json
    bm = json.load(open(os.path.join(ROOT, "hardware/data/logo/logo_bitmap.json")))
    for row, xs, xe in bm["runs"]:
        sh = pcbnew.PCB_SHAPE(board)
        sh.SetShape(pcbnew.SHAPE_T_POLY)
        y = y0 + row * pitch
        pts = [(x0 + xs * pitch, y), (x0 + xe * pitch, y), (x0 + xe * pitch, y + pitch), (x0 + xs * pitch, y + pitch)]
        sh.SetPolyPoints([vec(px, py) for px, py in pts])
        sh.SetFilled(True)
        sh.SetLayer(pcbnew.F_SilkS)
        sh.SetWidth(0)
        board.Add(sh)


STACKUP = """(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen") (color "White"))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 1" (type "prepreg") (thickness 0.09) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
\t\t\t(layer "In1.Cu" (type "copper") (thickness 0.0175))
\t\t\t(layer "dielectric 2" (type "core") (thickness 0.2) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
\t\t\t(layer "In2.Cu" (type "copper") (thickness 0.0175))
\t\t\t(layer "dielectric 3" (type "prepreg") (thickness 0.26) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
\t\t\t(layer "In3.Cu" (type "copper") (thickness 0.0175))
\t\t\t(layer "dielectric 4" (type "core") (thickness 0.2) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
\t\t\t(layer "In4.Cu" (type "copper") (thickness 0.0175))
\t\t\t(layer "dielectric 5" (type "prepreg") (thickness 0.09) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
\t\t\t(copper_finish "ENIG")
\t\t\t(dielectric_constraints no)
\t\t)
\t\t"""


def set_stackup(path):
    """pcbnew's Python API does not expose the stackup, so write it into the saved file:
    6 layers, ~1.0 mm (the module thickness the pinout spec suggests, §5.2.2), black mask, white silk, ENIG."""
    s = open(path).read()
    assert "(stackup" not in s
    s = s.replace("(setup\n\t\t", "(setup\n\t\t" + STACKUP, 1)
    s = s.replace("(general\n\t\t(thickness 1.6)", "(general\n\t\t(thickness 1.0)", 1)
    open(path, "w").write(s)


def main():
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(6)
    board.SetCopperLayerCount(6)

    rect = pcbnew.PCB_SHAPE(board)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetStart(vec(0, 0))
    rect.SetEnd(vec(35, 35))
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(mm(0.05))
    board.Add(rect)

    cache = {}
    for ref, lib, name, x, y, rot, value in PLACEMENT:
        path = LOCAL_FP if lib is None else f"{KICAD_FP}/{lib}.pretty"
        key = (path, name)
        if key not in cache:
            cache[key] = pcbnew.FootprintLoad(path, name)
            assert cache[key] is not None, key
        fp = pcbnew.Cast_to_FOOTPRINT(cache[key].Duplicate(False))
        fp.SetFPID(pcbnew.LIB_ID("fiumara-ae3-som" if lib is None else lib, name))
        fp.SetReference(ref)
        fp.SetValue(value)
        board.Add(fp)
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(vec(x, y))
        if ref in MODELS:
            path3d, (sx, sy, sz) = MODELS[ref]
            fp.Models().clear()
            m = pcbnew.FP_3DMODEL()
            m.m_Filename = path3d
            m.m_Scale.x, m.m_Scale.y, m.m_Scale.z = sx, sy, sz
            fp.Add3DModel(m)
        fp.Reference().SetLayer(pcbnew.F_Fab)   # refs on the fab layer: clean silkscreen, like a module
        if "DNP" in value:
            fp.SetDNP(True)

    for label, x0, y0, x1, y1 in RESERVED:
        r = pcbnew.PCB_SHAPE(board)
        r.SetShape(pcbnew.SHAPE_T_RECT)
        r.SetStart(vec(x0, y0))
        r.SetEnd(vec(x1, y1))
        r.SetLayer(pcbnew.F_Fab)
        r.SetWidth(mm(0.1))
        board.Add(r)
        t = pcbnew.PCB_TEXT(board)
        t.SetText(label)
        t.SetLayer(pcbnew.F_Fab)
        t.SetTextSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6)))
        t.SetPosition(vec((x0 + x1) / 2, (y0 + y1) / 2))
        board.Add(t)

    add_logo(board, 0.9, 0.25, 0.09)   # 48 px -> 4.3 mm
    silk = pcbnew.PCB_TEXT(board)
    silk.SetText("FIUMARA LABS")
    silk.SetLayer(pcbnew.F_SilkS)
    silk.SetTextSize(pcbnew.VECTOR2I(mm(1.3), mm(1.3)))
    silk.SetTextThickness(mm(0.26))
    silk.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    silk.SetPosition(vec(5.8, 2.4))
    board.Add(silk)

    board.Save(OUT)
    set_stackup(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
