"""Check the generated library against the source pin data.

    python3 scripts/check_lib.py [vendor-docs-dir]

Always checks (repo data only):
  * Alif E3 symbol pins == hardware/data/alif_e3_fbga194.json; footprint balls on the 0.5 mm grid.
  * edge symbol pins == hardware/data/edge_pinout.json; footprint pads at the generated positions.
  * every symbol's pin numbers == its footprint's pad numbers (stock footprints read from KiCad).
  * DP83825I symbol identical to the KiCad stock symbol.
With vendor docs (default ~/fiumaralabs/som-vendor-docs/ae3-som), also checks the BW3501N, TPS65214 and
TCAN1044A pin names against the datasheet text.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/fiumaralabs/som-vendor-docs/ae3-som")
KICAD = "/Applications/KiCad/KiCad.app/Contents/SharedSupport"
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def sexpr(text):
    tokens = re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()"]+', text)
    stack = [[]]
    for t in tokens:
        if t == "(":
            stack.append([])
        elif t == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(t[1:-1].replace('\\"', '"') if t.startswith('"') else t)
    return stack[0][0]


def find(node, key):
    for c in node:
        if isinstance(c, list) and c and c[0] == key:
            yield c


def first(node, key):
    return next(find(node, key), None)


def symbol_pins(sym):
    pins = {}
    for unit in find(sym, "symbol"):
        for p in find(unit, "pin"):
            num = first(p, "number")[1]
            name = first(p, "name")[1]
            check(num not in pins or pins[num][0] == name, f"{sym[1]}: pin {num} defined twice")
            pins[num] = (name, p[1])
    return pins


def fp_pads(path):
    fp = sexpr(open(path).read())
    pads = {}
    for p in find(fp, "pad"):
        at = first(p, "at")
        pads.setdefault(p[1], []).append((float(at[1]), float(at[2])))
    return pads


lib = sexpr(open(f"{ROOT}/hardware/lib/fiumara-ae3-som.kicad_sym").read())
syms = {s[1]: s for s in find(lib, "symbol")}
pretty = f"{ROOT}/hardware/lib/fiumara-ae3-som.pretty"


def fp_path(ref):
    libname, name = ref.split(":")
    base = pretty if libname == "fiumara-ae3-som" else f"{KICAD}/footprints/{libname}.pretty"
    return f"{base}/{name}.kicad_mod"


# --- every symbol vs its footprint
for name, s in syms.items():
    fpref = next(p[2] for p in find(s, "property") if p[1] == "Footprint")
    pins = set(symbol_pins(s))
    pads = {k for k in fp_pads(fp_path(fpref)) if k}
    check(pins == pads, f"{name}: symbol/footprint mismatch: only-symbol {sorted(pins - pads)[:8]}, "
                        f"only-footprint {sorted(pads - pins)[:8]}")

# --- Alif
balls = json.load(open(f"{ROOT}/hardware/data/alif_e3_fbga194.json"))
pins = symbol_pins(syms["AE302F80F55D5LE"])
for b, p in balls.items():
    want = "NC" if p["name"] == "NC" else p["name"]
    check(pins.get(b, (None,))[0] == want, f"Alif {b}: symbol {pins.get(b)} != table {want}")
rows = "ABCDEFGHJKLMNPRTUVW"
for b, xy in fp_pads(fp_path("fiumara-ae3-som:Alif_FBGA-194_10x10mm_Layout19x19_P0.5mm")).items():
    want = ((int(b[1:]) - 10) * 0.5, (rows.index(b[0]) - 9) * 0.5)
    check(xy == [want], f"Alif ball {b} at {xy}, want {want}")

# --- module edge
edge = json.load(open(f"{ROOT}/hardware/data/edge_pinout.json"))["pads"]
check(len(edge) == 244, "edge pad count")
pins = symbol_pins(syms["AE3_SoM_Edge_244"])
pads = fp_pads(fp_path("fiumara-ae3-som:AE3_SoM_LGA-244_35x35mm_P1.0mm_BottomPads"))
for p in edge:
    n = str(p["num"])
    check(pins.get(n, (None,))[0] == p["net"], f"edge pad {n}: symbol {pins.get(n)} != {p['net']}")
    check(pads.get(n) == [(float(p["x"]), float(p["y"]))], f"edge pad {n} at {pads.get(n)}, want {(p['x'], p['y'])}")

# --- DP83825I identical to stock
stock = sexpr(open(f"{KICAD}/symbols/Interface_Ethernet.kicad_sym").read())
st = next(s for s in find(stock, "symbol") if s[1] == "DP83825I")
check(symbol_pins(st) == symbol_pins(syms["DP83825I"]), "DP83825I differs from KiCad stock symbol")


# --- datasheet text checks
def pdftext(name):
    return subprocess.run(["pdftotext", "-layout", f"{DOCS}/{name}", "-"], capture_output=True, text=True).stdout


if os.path.isdir(DOCS):
    t = pdftext("bde_bw3501_datasheet.pdf")
    a = t.index("Table 2. Pin Descriptions\n")
    b = t.index("3.3. Signal Descriptions", a)
    table = {int(m.group(1)): m.group(2) for m in re.finditer(r"^ ?(\d{1,2})\s{2,}\S+\s+(\S+)", t[a:b], re.M)}
    pins = symbol_pins(syms["BDE-BW3501N"])
    check(len(table) == 64, f"BW3501 table rows parsed: {len(table)}")
    for n, nm in table.items():
        check(pins.get(str(n), (None,))[0] == nm, f"BW3501 pin {n}: {pins.get(str(n))} != datasheet {nm}")
    for n in range(65, 74):
        check(pins.get(str(n), (None,))[0] == "GND", f"BW3501 pin {n} should be GND (Fig 6)")

    t = pdftext("tps65214.pdf")
    seg = t[t.index("Table 5-1. Pin Functions"):t.index("6 Specifications", t.index("Table 5-1. Pin Functions"))]
    table = {}
    for m in re.finditer(r"^\s*([A-Za-z0-9_/]+)\s+(\d{1,2})\s+(I/O|I|O|PWR|GND)?\s", seg, re.M):
        table.setdefault(int(m.group(2)), m.group(1))
    pins = symbol_pins(syms["TPS6521402"])
    check(len(table) == 24, f"TPS65214 table rows parsed: {len(table)} {sorted(table)}")
    for n, nm in table.items():
        check(pins.get(str(n), (None,))[0] == nm, f"TPS65214 pin {n}: {pins.get(str(n))} != datasheet {nm}")

    t = pdftext("tcan1044a-q1.pdf")
    seg = t[t.index("Table 5-1. Pin Functions"):]
    seg = seg[:seg.index("Thermal Pad")]
    table = {int(m.group(2)): m.group(1) for m in re.finditer(r"^ ([A-Z]{2,4})\s+(\d)\s", seg, re.M)}
    table[5] = "VIO"   # row 5 reads "NC / VIO"; the V-suffix part uses VIO
    pins = symbol_pins(syms["TCAN1044AVDRBRQ1"])
    check(len(table) == 8, f"TCAN table rows parsed: {len(table)}")
    for n, nm in table.items():
        check(pins.get(str(n), (None,))[0] == nm, f"TCAN pin {n}: {pins.get(str(n))} != datasheet {nm}")
else:
    print(f"note: {DOCS} not found, skipped datasheet text checks")

if fails:
    print("\n".join(fails))
    sys.exit(f"{len(fails)} check(s) failed")
print(f"library OK: {len(syms)} symbols checked")
