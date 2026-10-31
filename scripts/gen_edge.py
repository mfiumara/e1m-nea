"""Fiumara Labs AE3 SoM edge pinout: LGA geometry and pad assignment (project-original).

    python3 scripts/gen_edge.py      # reads hardware/data/pinmap.json, writes hardware/data/edge_pinout.json

Geometry (top view, origin at the module centre, mm):
  * 35.0 x 35.0 mm module, 1.0 mm pitch, 0.60 mm round pads.
  * Two concentric rings: the outer ring on x or y = +-16 (1.5 mm in from the edge), the inner ring
    on +-15. The four outer-ring corners are left empty, so the outer ring has 4 x 31 = 124 pads
    and the inner ring 4 x 30 = 120 pads: 244 pads in total.
  * Numbering runs anticlockwise like a QFN: outer ring 1-124 starting at the top of the left
    side (left side top to bottom, bottom side left to right, right side bottom to top, top side
    right to left), then the inner ring 125-244 in the same order.

Assignment follows the on-module placement: power and debug on the left (PMIC side), the
antenna at the bottom of the left side next to the Wi-Fi module, SD/CAN/Ethernet along the
bottom (PHY bottom right), analog/PWM/encoders and MIPI on the right (SoC side), and the serial
and audio buses along the top. Every differential pair and the antenna pad are flanked by GND
on the same ring and backed by GND on the other ring.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pm = json.load(open(f"{ROOT}/hardware/data/pinmap.json"))
alif_edge = set(pm["edge"])

# Edge nets that are not Alif balls (connected in the M4 schematic).
OTHER = {
    "VIN": "5 V input: PMIC VSYS/PVIN, CAN transceiver VCC",
    "VREF_1V8": "PMIC LDO1, 1.8 V I/O reference output for carrier level shifters (<= 100 mA)",
    "EN": "PMIC EN/PB/VSENSE; 1 MOhm pull-up to VIN, 5 V tolerant, open-drain to turn the module off",
    "STBY_N": "PMIC MODE/STBY, pull-up to 1V8",
    "RESET_N": "PMIC nRSTOUT and Alif POR_N, open-drain wired-AND, pull-up to 1V8",
    "ETH_TX_P": "PHY TD_P", "ETH_TX_N": "PHY TD_M", "ETH_RX_P": "PHY RD_P", "ETH_RX_N": "PHY RD_M",
    "ETH_LED_LINK": "PHY LED_0", "ETH_LED_ACT": "PHY LED_1",
    "ANT": "Wi-Fi module ANT0, 50 Ohm (DNP U.FL alternative on the module)",
    "SD_VDD": "3.3 V SD card supply, load switch controlled by SD_PWR_EN",
    "CANH": "CAN transceiver CANH (assembly option)", "CANL": "CAN transceiver CANL (assembly option)",
    "WIFI_SWDIO": "Wi-Fi module SWDIO (factory programming)", "WIFI_SWCLK": "Wi-Fi module SWCLK (factory programming)",
    "WIFI_LOG": "Wi-Fi module LOGGER UART output",
}

GPIO = sorted([n for n in alif_edge if n.startswith("GPIO")], key=lambda n: int(n[4:]))
gpio_iter = iter(GPIO)
G = "GPIO*"     # placeholder: next free GPIO
X = "GND"

# --- per side, in pin-number order; outer has 31 slots, inner 30.
LEFT_OUTER = [X, "VIN", "VIN", "VIN", X, "VREF_1V8", "EN", "STBY_N", "RESET_N", "WAKE_N", X,
              "CONSOLE_TX", "CONSOLE_RX", "SWDIO", "SWCLK", "SWO", "TDI", "DBG_NRST", X,
              "USB_VBUS", "USB_ID", X, "USB_DP", "USB_DN", X, "WIFI_SWDIO", "WIFI_SWCLK", "WIFI_LOG", X, "ANT", X]
LEFT_INNER = [X, "VIN", "VIN", "VIN", X, "VREF_1V8", X, "I2C0_SCL", "I2C0_SDA", X, "I2C1_SCL", "I2C1_SDA",
              "UART0_TX", "UART0_RX", "UART0_RTS", "UART0_CTS", X, G, G, X, X, X, X, X, X, G, G, X, X, X]
BOTTOM_OUTER = [X, X, "SD_VDD", "SD_CLK", X, "SD_CMD", "SD_DAT0", "SD_DAT1", "SD_DAT2", "SD_DAT3", "SD_CD", X,
                "CAN_TXD", "CAN_RXD", "CAN_STB", "CANH", "CANL", X, "ETH_LED_LINK", "ETH_LED_ACT", X,
                "ETH_TX_P", "ETH_TX_N", X, X, "ETH_RX_P", "ETH_RX_N", X, "AOUT0", "AOUT1", X]
BOTTOM_INNER = [X, X, X, X, X, "UART1_TX", "UART1_RX", "UART2_TX", "UART2_RX", G, G, X, G, G, G, X, X,
                G, G, X, X, X, X, X, X, X, X, X, G, X]
RIGHT_OUTER = [X, "AIN0", "AIN1", "AIN2", X, "AIN3", "AIN4", "AIN5", X, "PWM0", "PWM1", "PWM2", "PWM3", "PWM4",
               "PWM5", X, "QEC0_A", "QEC0_B", "QEC1_A", "QEC1_B", X, "CSI_CLK_P", "CSI_CLK_N", X, "CSI_D0_P",
               "CSI_D0_N", X, "CSI_D1_P", "CSI_D1_N", X, X]
RIGHT_INNER = [X, X, X, X, X, G, G, G, X, G, G, G, G, G, G, X, G, G, G, G, X, X, X, X, X, X, X, X, X, X]
TOP_OUTER = [X, "DSI_CLK_P", "DSI_CLK_N", X, "DSI_D0_P", "DSI_D0_N", X, "DSI_D1_P", "DSI_D1_N", X,
             "SPI0_SCK", "SPI0_MOSI", "SPI0_MISO", "SPI0_CS0", "SPI0_CS1", X, "I2S0_MCLK", "I2S0_BCLK",
             "I2S0_LRCLK", "I2S0_DIN", "I2S0_DOUT", X, "PDM_CLK0", "PDM_DAT0", "PDM_CLK1", "PDM_DAT1", X,
             "I3C0_SCL", "I3C0_SDA", X, X]
TOP_INNER = [X, X, X, X, X, X, X, X, X, X, "SPI1_SCK", "SPI1_MOSI", "SPI1_MISO", "SPI1_CS0", X, G, G, G, G,
             G, X, G, G, G, G, X, G, G, X, X]

SIDES = [("left", LEFT_OUTER, LEFT_INNER), ("bottom", BOTTOM_OUTER, BOTTOM_INNER),
         ("right", RIGHT_OUTER, RIGHT_INNER), ("top", TOP_OUTER, TOP_INNER)]


def outer_xy(side, j):      # j = 0..30
    t = -15 + j
    return {"left": (-16, t), "bottom": (t, 16), "right": (16, -t), "top": (-t, -16)}[side]


def inner_xy(side, j):      # j = 0..29
    t = -15 + j
    return {"left": (-15, t), "bottom": (t, 15), "right": (15, -t), "top": (-t, -15)}[side]


def ptype(net):
    if net in ("VIN",):
        return "power_in"
    if net in ("VREF_1V8", "SD_VDD"):
        return "power_out"
    if net == "GND":
        return "power_in"
    if net.startswith(("AIN", "AOUT", "ANT", "ETH_TX", "ETH_RX", "CSI_", "DSI_", "USB_D", "CANH", "CANL")):
        return "passive"
    return "bidirectional"


pads = []
for ring, start in (("outer", 1), ("inner", 125)):
    n = start
    for side, outer, inner in SIDES:
        seq = outer if ring == "outer" else inner
        assert len(seq) == (31 if ring == "outer" else 30), (side, ring, len(seq))
        for j, net in enumerate(seq):
            if net == G:
                net = next(gpio_iter, X)
            x, y = (outer_xy if ring == "outer" else inner_xy)(side, j)
            pads.append(dict(num=n, x=x, y=y, ring=ring, side=side, net=net, type=ptype(net)))
            n += 1

# ------------------------------------------------------------------ checks
fails = []
nets = [p["net"] for p in pads if p["net"] != "GND"]
want = alif_edge | set(OTHER)
multi = {"VIN": 6, "VREF_1V8": 2}
for net in want:
    c = nets.count(net)
    if c != multi.get(net, 1):
        fails.append(f"{net}: placed {c}x, want {multi.get(net, 1)}")
for net in set(nets) - want:
    fails.append(f"{net}: placed but not defined")
xy = [(p["x"], p["y"]) for p in pads]
if len(set(xy)) != len(xy) or len(pads) != 244:
    fails.append(f"geometry: {len(pads)} pads, {len(set(xy))} unique positions")
by_xy = {(p["x"], p["y"]): p for p in pads}


def neighbours(p):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        q = by_xy.get((p["x"] + dx, p["y"] + dy))
        if q:
            yield q


for p in pads:   # every high-speed / RF pad must touch GND on at least two sides
    if p["net"] == "ANT" or p["net"].endswith(("_P", "_N")) and p["net"].startswith(("CSI", "DSI", "ETH", "USB_D")):
        g = sum(q["net"] == "GND" for q in neighbours(p))
        if g < 2:
            fails.append(f"pad {p['num']} {p['net']}: only {g} GND neighbours")
left_gpio = list(gpio_iter)
if left_gpio:
    fails.append(f"GPIOs without a pad: {left_gpio}")
if fails:
    raise SystemExit("\n".join(fails))

json.dump({"name": "Fiumara Labs AE3 SoM edge", "pitch_mm": 1.0, "pad_mm": 0.6, "outline_mm": 35.0,
           "pads": pads, "other": OTHER}, open(f"{ROOT}/hardware/data/edge_pinout.json", "w"), indent=1)
print(f"{len(pads)} pads: {len(nets)} signal/power, {len(pads) - len(nets)} GND")
