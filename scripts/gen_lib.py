"""Generate the project symbol and footprint libraries.

    python3 scripts/gen_lib.py

Inputs:  hardware/data/alif_e3_fbga194.json   (scripts/extract_alif_pins.py, ADTS0007 v2.12 Table 4-1)
         hardware/data/edge_pinout.json        (scripts/gen_edge.py, this project's own edge pinout)
         the KiCad 10 stock library (DP83825I symbol)
Outputs: hardware/lib/fiumara-ae3-som.kicad_sym, hardware/lib/fiumara-ae3-som.pretty/*.kicad_mod

Pin tables of the BW3501N, TPS6521402 and TCAN1044AV are transcribed below and checked against
the datasheet text by scripts/check_lib.py.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from kisexpr import (Pin, stack, symbol, symbol_lib, footprint, pad, custom_pad, fp_rect_line,  # noqa: E402
                     fp_line, fp_poly, fp_text, rect_pts, f)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "hardware", "lib")
PRETTY = os.path.join(LIB, "fiumara-ae3-som.pretty")
KICAD_SYM = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
LIBNAME = "fiumara-ae3-som"
SMD = ["F.Cu", "F.Mask", "F.Paste"]

TYPEMAP = {"I": "input", "O": "output", "IO": "bidirectional", "A": "passive"}


# =============================================================== Alif Ensemble E3, FBGA194
def alif_symbol():
    balls = json.load(open(os.path.join(ROOT, "hardware/data/alif_e3_fbga194.json")))
    by_name = {}
    for b, p in balls.items():
        by_name.setdefault(p["name"], []).append(b)

    def one(name, etype=None):
        (b,) = by_name[name]
        return Pin(b, name, etype or balls[b]["type"])

    def many(name, etype="power_in"):
        return stack(by_name[name], name, etype)

    power = dict(
        top=[*[one(n) for n in ("VDD_MAIN", "VDD_BATT", "VDD_BUCK", "VDD_USB_3V3")],
             *many("VDD_IO_1V8"), one("VDD_IO_FLEX"), one("VDD_MIPI_1V8"),
             *many("VDD_CORE_0V8"), one("VDD_SX_0V8"), one("VDD_PLL_0V8")],
        right=[one("VSW", "power_out"), one("VREG_CORE_0V8"), None, one("VREG_AON"), one("VREG_LP_1V8"),
               one("VREG_DIG_1V8"), one("VREG_AUX_1V8"), None, one("VREG_MIPI_1V8"), one("VREG_MIPI_0V8"),
               None, one("VREF_P", "passive")],
        left=[Pin(b, "NC", "no_connect", hidden=False) for b in by_name["NC"]],
        bottom=[*many("VSS"), one("VSS_ANA", "power_in"), one("VSS_BUCK", "power_in")],
    )
    system = dict(
        left=[one("POR_N"), one("NSRST"), None, one("HFXO_P"), one("HFXO_N"), None, one("LFXO_P"),
              one("LFXO_N"), None, one("SEUART_RX"), one("SEUART_TX")],
        right=[one("USB_DP"), one("USB_DM"), one("USB_VBUS"), one("USB_IO_ID"), one("USB_REXT"), None,
               one("MIPICSI_C_P"), one("MIPICSI_C_N"), one("MIPICSI_0_P"), one("MIPICSI_0_N"),
               one("MIPICSI_1_P"), one("MIPICSI_1_N"), None,
               one("MIPIDSI_C_P"), one("MIPIDSI_C_N"), one("MIPIDSI_0_P"), one("MIPIDSI_0_N"),
               one("MIPIDSI_1_P"), one("MIPIDSI_1_N"), None, one("MIPI_REXT")],
    )

    def port_pin(port, bit):
        b = by_name[f"P{port}_{bit}"][0]
        alts = [(a[1], TYPEMAP[a[2]]) for a in balls[b]["alts"]]
        return Pin(b, f"P{port}_{bit}", "bidirectional", alts=alts)

    units, names = [power, system], ["Power", "System, USB, MIPI"]
    for first in (0, 4, 8, 12):
        ports = range(first, first + 4)
        lp, rp = ports[:2], ports[2:]
        left = [x for p in lp for x in ([port_pin(p, i) for i in range(8)] + [None])][:-1]
        right = [x for p in rp for x in ([port_pin(p, i) for i in range(8)] + [None])][:-1]
        units.append(dict(left=left, right=right))
        names.append(f"GPIO P{first}-P{first + 3}")
    return symbol(f"AE302F80F55D5LE", "U", "AE302F80F55D5LE",
                  f"{LIBNAME}:Alif_FBGA-194_10x10mm_Layout19x19_P0.5mm",
                  "https://alifsemi.com/download/ADTS0007",
                  "Alif Ensemble E3 MCU, 2x Cortex-M55 + 2x Ethos-U55, 5.5 MB MRAM, 13.5 MB SRAM, FBGA194",
                  units, keywords="Alif Ensemble E3 MCU Cortex-M55 NPU", fp_filter="Alif*FBGA*194*",
                  unit_names=names)


def alif_footprint():
    balls = json.load(open(os.path.join(ROOT, "hardware/data/alif_e3_fbga194.json")))
    rows = "ABCDEFGHJKLMNPRTUVW"
    items = [fp_text("Reference", "REF**", 0, -6.2, "F.SilkS"),
             fp_text("Value", "Alif_FBGA-194_10x10mm", 0, 6.2, "F.Fab"),
             fp_text("Datasheet", "https://alifsemi.com/download/ADTS0007", 0, 0, "F.Fab", hide=True),
             fp_rect_line("F.Fab", -5, -5, 5, 5, 0.1),
             fp_poly("F.Fab", [(-5, -4), (-4, -5), (-5, -5)], 0.1, True),
             fp_rect_line("F.CrtYd", -5.5, -5.5, 5.5, 5.5, 0.05),
             fp_line("F.SilkS", -5.11, -4.0, -5.11, 5.11, 0.12), fp_line("F.SilkS", -5.11, 5.11, 5.11, 5.11, 0.12),
             fp_line("F.SilkS", 5.11, 5.11, 5.11, -5.11, 0.12), fp_line("F.SilkS", 5.11, -5.11, -4.0, -5.11, 0.12),
             fp_poly("F.SilkS", [(-5.11, -5.11), (-5.6, -5.11), (-5.11, -5.6)], 0.12, True)]
    for b in balls:
        r, c = rows.index(b[0]), int(b[1:])
        x, y = (c - 10) * 0.5, (r - 9) * 0.5
        items.append(pad(b, "circle", x, y, 0.25, 0.25, SMD, " (solder_mask_margin 0.05)"))
    return footprint("Alif_FBGA-194_10x10mm_Layout19x19_P0.5mm",
                     "Alif Ensemble FBGA194, 10x10 mm, 19x19 grid, 0.5 mm pitch, 0.25 mm ball (ADTS0007 v2.12 Fig 6-5). "
                     "0.25 mm NSMD land.", "BGA 194 0.5mm Alif Ensemble", items)


# =============================================================== BDE-BW3501N
# Module pin -> (name, type) from BDE-BW3501 datasheet V0.6 Table 2 (pins 1-64) and Figure 6 (65-73).
BW_PINS = {
    1: "GND", 2: "GND", 3: "GND", 4: "VDD_3V3", 5: "VDD_3V3", 6: "GND", 7: "VDD_1V8", 8: "VDD_1V8",
    9: "GPIO35", 10: "GPIO34", 11: "GPIO33", 12: "GPIO32", 13: "GPIO31", 14: "GPIO30", 15: "GND", 16: "GND",
    17: "xSPI_D0", 18: "xSPI_D3", 19: "xSPI_CLK", 20: "xSPI_D2", 21: "xSPI_D1", 22: "xSPI_CS",
    23: "GPIO29", 24: "GPIO28", 25: "GPIO27", 26: "GPIO26", 27: "VIO2", 28: "VDD_SF", 29: "GND",
    30: "GPIO19", 31: "GPIO18", 32: "GPIO17", 33: "GND", 34: "GPIO16", 35: "GPIO15", 36: "GPIO14",
    37: "GPIO13", 38: "GPIO12", 39: "GPIO11", 40: "GPIO10", 41: "VIO1", 42: "LOGGER", 43: "SWCLK",
    44: "SWDIO", 45: "GPIO6", 46: "GPIO5", 47: "GPIO4", 48: "GND", 49: "GND", 50: "GPIO3", 51: "GPIO2",
    52: "GND", 53: "GND", 54: "GPIO1", 55: "GPIO0", 56: "nRESET", 57: "GND", 58: "GND", 59: "GND",
    60: "GND", 61: "GND", 62: "GND", 63: "ANT0", 64: "GND",
    **{n: "GND" for n in range(65, 74)},
}


def bw_symbol():
    gnd = [n for n, v in BW_PINS.items() if v == "GND"]
    by = {v: n for n, v in BW_PINS.items() if v != "GND"}
    g = lambda name, t="bidirectional": Pin(by[name], name, t)
    left = [g("nRESET", "input"), g("LOGGER", "output"), g("SWCLK", "input"), g("SWDIO"), None,
            *[g(f"GPIO{i}") for i in (0, 1, 2, 3, 4, 5, 6)], None,
            *[g(f"GPIO{i}") for i in range(10, 20)]]
    right = [g("ANT0", "passive"), None, *[g(f"GPIO{i}") for i in range(26, 36)], None,
             *[g(n) for n in ("xSPI_CLK", "xSPI_CS", "xSPI_D0", "xSPI_D1", "xSPI_D2", "xSPI_D3")]]
    top = [*stack([4, 5], "VDD_3V3"), *stack([7, 8], "VDD_1V8"),
           Pin(41, "VIO1", "power_in"), Pin(27, "VIO2", "power_in"), Pin(28, "VDD_SF", "power_in")]
    bottom = stack(gnd, "GND")
    return symbol(f"BDE-BW3501N", "U", "BDE-BW3501N42",
                  f"{LIBNAME}:BDE-BW3501N_14x12.6mm",
                  "https://www.bdecomm.com/en/show_info.asp?id=492",
                  "BDE-BW3501N Wi-Fi 6 + BLE 5.4 module (TI CC3501E), 2.4 GHz, RF on ANT0 pin, 14x12.6 mm",
                  [dict(left=left, right=right, top=top, bottom=bottom)],
                  keywords="WiFi 6 BLE CC3501E module", fp_filter="BDE*BW3501N*")


def bw_footprint():
    """BDE-BW3501 datasheet V0.6 Fig 16/17 (BW3551N land pattern), top view, origin at body centre.

    Body 14.0 x 12.6. Signal pads 0.75 x 0.4 at 0.7 pitch, 0.3 in from the edge; corner pads
    0.75 x 0.75; 3x3 ground pads 1.0 x 1.0 at 1.4 pitch, whose bottom-view edges are 3.729 from
    the left and 4.142 from the bottom (top view: grid centre +1.371, +0.258).
    """
    W, H = 14.0, 12.6
    xe, ye = W / 2 - 0.3 - 0.375, H / 2 - 0.3 - 0.375   # pad centre lines: 6.325, 5.625
    items = [fp_text("Reference", "REF**", 0, -H / 2 - 1.2, "F.SilkS"),
             fp_text("Value", "BDE-BW3501N", 0, H / 2 + 1.2, "F.Fab"),
             fp_rect_line("F.Fab", -W / 2, -H / 2, W / 2, H / 2, 0.1),
             fp_rect_line("F.CrtYd", -W / 2 - 0.25, -H / 2 - 0.25, W / 2 + 0.25, H / 2 + 0.25, 0.05),
             fp_rect_line("F.SilkS", -W / 2 - 0.11, -H / 2 - 0.11, W / 2 + 0.11, H / 2 + 0.11, 0.12),
             fp_poly("F.SilkS", [(-W / 2 - 0.11, -H / 2 + 0.6), (-W / 2 - 0.6, -H / 2 - 0.11),
                                 (-W / 2 - 0.11, -H / 2 - 0.11)], 0.12, True)]
    c = 0.75
    corners = {1: (-xe, -ye), 16: (-xe, ye), 33: (xe, ye), 48: (xe, -ye)}
    for n, (x, y) in corners.items():
        items.append(pad(n, "rect", x, y, c, c, SMD))
    for i, n in enumerate(range(2, 16)):        # left column, top -> bottom
        items.append(pad(n, "rect", -xe, -4.55 + i * 0.7, 0.75, 0.4, SMD))
    for i, n in enumerate(range(17, 33)):       # bottom row, left -> right
        items.append(pad(n, "rect", -5.25 + i * 0.7, ye, 0.4, 0.75, SMD))
    for i, n in enumerate(range(34, 48)):       # right column, bottom -> top
        items.append(pad(n, "rect", xe, 4.55 - i * 0.7, 0.75, 0.4, SMD))
    for i, n in enumerate(range(49, 65)):       # top row, right -> left
        items.append(pad(n, "rect", 5.25 - i * 0.7, -ye, 0.4, 0.75, SMD))
    gx, gy = 1.371, 0.258
    grid = {65: (-1, -1), 66: (-1, 0), 67: (-1, 1), 70: (0, -1), 69: (0, 0), 68: (0, 1),
            71: (1, -1), 72: (1, 0), 73: (1, 1)}
    for n, (i, j) in grid.items():
        items.append(pad(n, "rect", gx + i * 1.4, gy + j * 1.4, 1.0, 1.0, SMD,
                         " (solder_paste_margin_ratio -0.1)"))
    return footprint("BDE-BW3501N_14x12.6mm",
                     "BDE-BW3501N Wi-Fi 6/BLE module, ANT-pin variant, 14x12.6 mm, 73 pads "
                     "(BDE-BW3501 datasheet V0.6, Fig 16-17)", "BDE BW3501 CC3501E WiFi module", items)


# =============================================================== TI TPS6521402 (TPS65214), VAF0024A
TPS_PINS = {1: "MODE/STBY", 2: "FB_B2", 3: "VLDO2", 4: "VSYS/PVIN_LDO12", 5: "VLDO1", 6: "AGND",
            7: "VDD1P8", 8: "FB_B1", 9: "GPO/nWAKEUP", 10: "PGND", 11: "LX_B1", 12: "PVIN_B1", 13: "SDA",
            14: "SCL", 15: "nINT", 16: "GPIO/VSEL", 17: "nRSTOUT", 18: "FB_B3", 19: "EN/PB/VSENSE",
            20: "PVIN_B3", 21: "LX_B3", 22: "PGND", 23: "LX_B2", 24: "PVIN_B2", 25: "PGND"}


def tps_symbol():
    P = lambda n, t: Pin(n, TPS_PINS[n], t)
    left = [P(4, "power_in"), P(12, "power_in"), P(24, "power_in"), P(20, "power_in"), None,
            P(19, "input"), P(1, "input"), P(16, "bidirectional"), None, P(13, "bidirectional"), P(14, "input")]
    right = [P(11, "power_out"), P(8, "input"), None, P(23, "power_out"), P(2, "input"), None,
             P(21, "power_out"), P(18, "input"), None, P(5, "power_out"), P(3, "power_out"), P(7, "power_out"),
             None, P(17, "output"), P(15, "open_collector"), P(9, "open_collector")]
    bottom = [P(6, "power_in"), *stack([10, 22, 25], "PGND")]
    return symbol(f"TPS6521402", "U", "TPS6521402VAFR",
                  f"{LIBNAME}:TI_VAF0024A_WQFN-HR-24_3.5x3.5mm_P0.5mm",
                  "https://www.ti.com/lit/ds/symlink/tps65214.pdf",
                  "PMIC, 3 buck + 2 LDO, I2C, AM62L NVM (BUCK2 1.8V, BUCK3 3.3V with VSEL low, LDO1 1.8V), WQFN-HR-24",
                  [dict(left=left, right=right, bottom=bottom)], keywords="PMIC buck LDO I2C TPS65214",
                  fp_filter="TI*VAF0024A*")


def tps_footprint():
    """TI VAF0024A example board layout (SLVSHK7A p.139, 4230459/C).

    Pad rows on +-1.65; side pads 0.6 x 0.25 at 0.5 pitch (positions +-1.0, +-0.5, 0); corner pads are
    L shapes (0.6 long arms, 0.225 thick) whose arm centre lines sit 0.4875 beyond the last side pad.
    PGND: 1.0 x 0.673 centre pad joined to pins 10 and 22 by 0.2 wide strips.
    """
    items = [fp_text("Reference", "REF**", 0, -2.9, "F.SilkS"),
             fp_text("Value", "TI_VAF0024A", 0, 2.9, "F.Fab"),
             fp_rect_line("F.Fab", -1.75, -1.75, 1.75, 1.75, 0.1),
             fp_rect_line("F.CrtYd", -2.25, -2.25, 2.25, 2.25, 0.05),
             fp_poly("F.SilkS", [(-2.1, -2.1), (-2.1, -1.7), (-1.7, -2.1)], 0.12, True)]
    e, L, T = 1.65, 0.6, 0.25
    pos = [-1.0, -0.5, 0.0, 0.5, 1.0]
    for i, n in enumerate(range(2, 7)):
        items.append(pad(n, "roundrect", -e, pos[i], L, T, SMD, " (roundrect_rratio 0.2)"))
    for i, n in enumerate(range(8, 13)):
        items.append(pad(n, "roundrect", pos[i], e, T, L, SMD, " (roundrect_rratio 0.2)"))
    for i, n in enumerate(range(14, 19)):
        items.append(pad(n, "roundrect", e, -pos[i], L, T, SMD, " (roundrect_rratio 0.2)"))
    for i, n in enumerate(range(20, 25)):
        items.append(pad(n, "roundrect", -pos[i], -e, T, L, SMD, " (roundrect_rratio 0.2)"))
    arm, th, c = 0.6, 0.225, 1.4875
    outer = e + L / 2   # 1.95
    for n, (sx, sy) in {1: (-1, -1), 7: (-1, 1), 13: (1, 1), 19: (1, -1)}.items():
        horiz = rect_pts(min(sx * (outer - arm), sx * outer), sy * c - th / 2, max(sx * (outer - arm), sx * outer), sy * c + th / 2)
        vert = rect_pts(sx * c - th / 2, min(sy * (outer - arm), sy * outer), sx * c + th / 2, max(sy * (outer - arm), sy * outer))
        cx, cy = sx * c, sy * c
        rel = lambda pts: [(x - cx, y - cy) for x, y in pts]
        items.append(custom_pad(n, cx, cy, th, [rel(horiz), rel(vert)], SMD))
    centre = rect_pts(-0.5, -0.3365, 0.5, 0.3365)
    strip = rect_pts(-0.1, -e, 0.1, e)
    items.append(custom_pad(25, 0, 0, 0.2, [centre, strip], SMD))
    return footprint("TI_VAF0024A_WQFN-HR-24_3.5x3.5mm_P0.5mm",
                     "TI VAF0024A WQFN-HR 24 pin 3.5x3.5 mm, 0.5 mm pitch, L corner pads and PGND bar "
                     "(TPS65214 datasheet SLVSHK7A, example board layout 4230459/C)", "WQFN-HR VAF TPS65214", items)


# =============================================================== TCAN1044AV-Q1 (DRB, VSON-8)
def tcan_symbol():
    left = [Pin(1, "TXD", "input"), Pin(4, "RXD", "output"), Pin(8, "STB", "input")]
    right = [Pin(7, "CANH", "bidirectional"), Pin(6, "CANL", "bidirectional")]
    top = [Pin(3, "VCC", "power_in"), Pin(5, "VIO", "power_in")]
    bottom = stack([2, 9], "GND")
    return symbol(f"TCAN1044AVDRBRQ1", "U", "TCAN1044AVDRBRQ1",
                  "Package_SON:VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm",
                  "https://www.ti.com/lit/ds/symlink/tcan1044a-q1.pdf",
                  "CAN FD transceiver with VIO level shifting, 5 V VCC, VSON-8 (DRB)",
                  [dict(left=left, right=right, top=top, bottom=bottom)], keywords="CAN FD transceiver VIO",
                  fp_filter="VSON*3x3mm*P0.65mm*")


# =============================================================== DP83825I (KiCad stock symbol, copied)
def stock_symbol(lib, name):
    s = open(os.path.join(KICAD_SYM, f"{lib}.kicad_sym")).read()
    i = s.index(f'(symbol "{name}"')
    depth, j = 0, i
    while True:
        ch = s[j]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                break
        elif ch == '"':
            j = s.index('"', j + 1)
            while s[j - 1] == "\\":
                j = s.index('"', j + 1)
        j += 1
    blk = s[i:j + 1]
    return blk.replace(f'(symbol "{name}"', f'(symbol "{name}"', 1)


# =============================================================== module edge (244 LGA pads, bottom side)
EDGE_FP = "AE3_SoM_LGA-244_35x35mm_P1.0mm_BottomPads"
EDGE_UNITS = [
    ("Power, control, debug, USB, RF", ("VIN", "VREF_1V8", "EN", "STBY_N", "RESET_N", "WAKE_N", "CONSOLE_", "SWDIO",
                                        "SWCLK", "SWO", "TDI", "DBG_NRST", "USB_", "WIFI_", "ANT")),
    ("SD, CAN, Ethernet, analog", ("SD_", "CAN", "ETH_", "AIN", "AOUT", "PWM", "QEC")),
    ("MIPI, serial, audio", ("CSI_", "DSI_", "SPI", "I2C", "I3C", "UART", "I2S", "PDM")),
    ("GPIO", ("GPIO",)),
    ("GND", ("GND",)),
]


def edge_pads():
    return json.load(open(os.path.join(ROOT, "hardware/data/edge_pinout.json")))["pads"]


def edge_unit(net):
    for k, (_, prefixes) in enumerate(EDGE_UNITS):
        if net == "GND" and "GND" in prefixes:
            return k
        if net != "GND" and net.startswith(prefixes):
            return k
    raise KeyError(net)


def edge_symbol():
    pads = edge_pads()
    natural = lambda p: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", p["net"])]
    units, names = [], []
    for k, (uname, _) in enumerate(EDGE_UNITS):
        mine = sorted([p for p in pads if edge_unit(p["net"]) == k], key=lambda p: (natural(p), p["num"]))
        if uname == "GND":
            units.append(dict(bottom=stack([p["num"] for p in mine], "GND")))
            names.append(uname)
            continue
        out, seen = [], {}
        for p in mine:
            if p["net"] in seen:     # repeated power pads (VIN x6, VREF_1V8 x2) are stacked
                out.insert(seen[p["net"]] + 1, Pin(p["num"], p["net"], "passive", hidden=True))
                continue
            seen[p["net"]] = len(out)
            out.append(Pin(p["num"], p["net"], p["type"]))
        half = (len([q for q in out if not q.hidden]) + 1) // 2
        vis = 0
        for idx, q in enumerate(out):
            vis += not q.hidden
            if vis > half:
                break
        units.append(dict(left=out[:idx], right=out[idx:]))
        names.append(uname)
    return symbol("AE3_SoM_Edge_244", "J", "AE3_SoM_Edge", f"{LIBNAME}:{EDGE_FP}", "",
                  "Fiumara Labs AE3 SoM edge: 244 LGA pads on the module underside (docs/edge-pinout.md)",
                  units, keywords="SoM LGA module edge pads", fp_filter="AE3_SoM_LGA*", unit_names=names)


def edge_footprint():
    """Module-side land: 0.60 mm round pads on B.Cu at 1.0 mm pitch, top-view coordinates
    (scripts/gen_edge.py). Placed on the front of the module board without flipping."""
    pads = edge_pads()
    items = [fp_text("Reference", "REF**", 0, -18.5, "F.SilkS"),
             fp_text("Value", "AE3_SoM_Edge", 0, 18.5, "F.Fab"),
             fp_rect_line("F.Fab", -17.5, -17.5, 17.5, 17.5, 0.1),
             fp_rect_line("B.Fab", -17.5, -17.5, 17.5, 17.5, 0.1),
             fp_rect_line("B.CrtYd", -17.75, -17.75, 17.75, 17.75, 0.05),
             fp_rect_line("B.Fab", -14.2, -14.2, 14.2, 14.2, 0.1),   # bottom-side component area inside the rings
             # pin-1 marker at the top-left corner, both sides
             fp_poly("F.SilkS", [(-17.3, -17.3), (-16.6, -17.3), (-17.3, -16.6)], 0, True),
             fp_poly("B.SilkS", [(-17.3, -17.3), (-16.6, -17.3), (-17.3, -16.6)], 0, True)]
    for p in pads:
        items.append(pad(p["num"], "circle", p["x"], p["y"], 0.6, 0.6, ["B.Cu", "B.Mask", "B.Paste"],
                         " (solder_mask_margin 0.05)"))
    return footprint(EDGE_FP, "Fiumara Labs AE3 SoM underside: 244 round 0.60 mm LGA pads on B.Cu, 1.0 mm pitch, "
                     "two rings, 35x35 mm outline, NSMD 0.70 mm mask opening", "SoM LGA module edge 244", items)


# =============================================================== main
def main():
    os.makedirs(PRETTY, exist_ok=True)
    syms = [alif_symbol(), bw_symbol(), tps_symbol(), tcan_symbol(), stock_symbol("Interface_Ethernet", "DP83825I"),
            edge_symbol()]
    open(os.path.join(LIB, f"{LIBNAME}.kicad_sym"), "w").write(symbol_lib(syms))
    for name, text in [("Alif_FBGA-194_10x10mm_Layout19x19_P0.5mm", alif_footprint()),
                       ("BDE-BW3501N_14x12.6mm", bw_footprint()),
                       ("TI_VAF0024A_WQFN-HR-24_3.5x3.5mm_P0.5mm", tps_footprint()),
                       (EDGE_FP, edge_footprint())]:
        open(os.path.join(PRETTY, f"{name}.kicad_mod"), "w").write(text)
    print("wrote", len(syms), "symbols, 4 footprints")


if __name__ == "__main__":
    main()
