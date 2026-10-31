"""Extract the Alif Ensemble E3 FBGA194 ball map and pin mux from ADTS0007 v2.12, Table 4-1.

Usage: python3 scripts/extract_alif_pins.py <alif_E3_datasheet.pdf> hardware/data/alif_e3_fbga194.json

Output: ball -> {name, type, rail, alts[[mux, signal, dir]]}. Checked for exactly 194 unique balls
on the A..W x 1..19 grid.

Table 4-1 lists 7 FBGA VSS balls, but Figure 4-2 (p.89) also shows VSS at B2, C18 and J10. Only
with those three does the total reach 194, so the figure is treated as authoritative for VSS.
"""
import json
import re
import subprocess
import sys

pdf, out_path = sys.argv[1], sys.argv[2]
txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout.splitlines()
start = next(i for i, l in enumerate(txt) if l.strip().startswith("4.2 Pin Function Options by Location") and i > 5000)
end = next(i for i, l in enumerate(txt) if l.strip().startswith("4.3 Pin Function Multiplexing") and i > start)
rows = txt[start:end]

BALL = r"[A-HJ-NPR-W]\d{1,2}"
sig_re = re.compile(r"^\s{20,}([A-Z][A-Z0-9_]+)(?:\([a-z]\))?\s+(IO|I|O|A)(?:\s+(\d))?\s")
inline_re = re.compile(rf"^P\d+_\d\s+\S+\s+{BALL}\s+([A-Z][A-Z0-9_]+)(?:\([a-z]\))?\s+(IO|I|O|A)(?:\s+(\d))?\s")
gpio_re = re.compile(rf"^(P\d+_\d)\s+(\S+)\s+({BALL})\s+.*?(VDD_IO_1V8|VDD_IO_FLEX)\s*$")

pins = {}
block, blocks = None, []
for l in rows:
    m = sig_re.match(l + " ")
    if m:
        name, typ, n = m.groups()
        if n == "0" or name.startswith("GPIOV_") or block is None:
            block = {"alts": []}
            blocks.append(block)
        block["alts"].append([int(n) if n else None, name, typ])
        continue
    m = gpio_re.match(l)
    if m:
        inline = inline_re.match(l + " ")
        if inline:
            name, typ, n = inline.groups()
            if name.startswith("GPIOV_"):   # P15_4..7: the only signal sits on the pin row itself
                block = {"alts": [[0, name, typ]]}
                blocks.append(block)
            else:                           # a mux signal printed on the pin row (mid-block)
                block["alts"].append([int(n) if n else None, name, typ])
        assert block is not None
        block["pin"], block["ball"], block["rail"] = m.group(1), m.group(3), m.group(4)
for b in blocks:
    if "pin" not in b:
        continue
    alts = b["alts"]
    if alts[0][0] is None:  # P15_x (LPGPIO, flex pads): the table gives no mux numbers
        alts = [[i, a[1], a[2]] for i, a in enumerate(alts)]
    pins[b["ball"]] = {"name": b["pin"], "type": "bidirectional", "rail": b["rail"], "alts": alts}
n_gpio = len(pins)

TYPE = {"I": "input", "O": "output", "IO": "bidirectional", "A": "passive", "P": "passive",
        "PWR": "power_in", "GND": "power_in"}
single_re = re.compile(rf"^([A-Z][A-Z0-9_.]+)\s+(?:[A-Z]\d{{1,2}}(?:, ?[A-Z]\d{{1,2}})*,?\s+)?({BALL})\s+\1\s+(IO|I|O|A|P|PWR|GND)\b")
for l in rows:
    m = single_re.match(l)
    if m and not re.match(r"P\d+_\d$", m.group(1)):
        pins[m.group(2)] = {"name": m.group(1), "type": TYPE[m.group(3)]}

# Multi-ball and wrapped rows of Table 4-1, checked against Figure 4-2.
MANUAL = {
    "VSS": ["B2", "C18", "J10", "J11", "K9", "K10", "K11", "L2", "L10", "V12"],
    "VDD_IO_1V8": ["A5", "D19", "W3"],
    "VDD_CORE_0V8": ["B5", "E1", "E19", "V6"],
    "VREG_CORE_0V8": ["W18"],
    "VREG_AUX_1V8": ["V18"],
    "VREG_DIG_1V8": ["U19"],
    "VSW": ["T19"],
    "NC": ["B1", "C1", "J8", "M18"],
}
for name, balls in MANUAL.items():
    for b in balls:
        pins[b] = {"name": name, "type": "no_connect" if name == "NC" else "power_in"}
for p in pins.values():
    if p["name"].startswith("VREG_") or p["name"] == "VSW":
        p["type"] = "power_out"
    if p["name"].startswith("VSS"):
        p["type"] = "power_in"

# Cross-check against Table 4-2 (pure mux table). Its empty cells collapse in the text dump, so only
# rows with all 8 entries can be compared position by position; every other row must at least list
# the same signals.
t42_start = end
t42_end = next(i for i, l in enumerate(txt) if i > t42_start and re.match(r"^\s*4\.4\b|^\s*5 Electrical", l))
rows42 = {}
for l in txt[t42_start:t42_end]:
    m = re.match(r"^(P\d+_\d)\s+(.*)$", l)
    if m:
        rows42[m.group(1)] = [c for c in m.group(2).split() if c != "RESERVED"]
by_pin = {p["name"]: p for p in pins.values() if "alts" in p}
checked = 0
for pin, cells in rows42.items():
    if pin not in by_pin:
        continue
    mine = by_pin[pin]["alts"]
    names = [re.sub(r"\([a-z]\)$", "", c) for c in cells]
    assert {a[1] for a in mine} == set(names), (pin, sorted(a[1] for a in mine), sorted(names))
    if len(names) == 8:
        assert [a[1] for a in sorted(mine)] == names, (pin, mine, names)
    checked += 1
assert checked >= 120, checked

grid = {f"{r}{c}" for r in "ABCDEFGHJKLMNPRTUVW" for c in range(1, 20)}
assert all(b in grid for b in pins), [b for b in pins if b not in grid]
names = {p["name"] for p in pins.values()}
need = {"POR_N", "NSRST", "HFXO_P", "HFXO_N", "LFXO_P", "LFXO_N", "USB_DP", "USB_DM", "USB_VBUS",
        "VDD_MAIN", "VDD_BATT", "VDD_BUCK", "VDD_USB_3V3", "VDD_IO_FLEX", "VREG_AON", "SEUART_TX",
        "MIPICSI_C_P", "MIPIDSI_C_P", "VSS_ANA", "VSS_BUCK", "VREF_P"}
assert need <= names, need - names
# Spot checks against Figure 4-2.
fig = {"A1": "VDD_PLL_0V8", "A2": "VDD_SX_0V8", "A3": "HFXO_N", "A4": "HFXO_P", "J12": "NSRST",
       "U18": "POR_N", "W17": "LFXO_P", "V17": "LFXO_N", "R9": "USB_IO_ID", "T18": "VDD_BATT",
       "R19": "P0_0", "V2": "P15_0", "V1": "P15_3", "V3": "P15_4", "W4": "P15_5", "V4": "P15_6",
       "W5": "P15_7", "U3": "P7_6", "W19": "VREG_LP_1V8", "P19": "VDD_MAIN"}
for b, n in fig.items():
    assert pins[b]["name"] == n, (b, pins[b]["name"], n)
assert len(pins) == 194, len(pins)
print(f"{len(pins)} balls ({n_gpio} GPIO)")
order = "ABCDEFGHJKLMNPRTUVW"
json.dump(dict(sorted(pins.items(), key=lambda kv: (order.index(kv[0][0]), int(kv[0][1:])))),
          open(out_path, "w"), indent=1)
