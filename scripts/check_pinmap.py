"""Check hardware/data/pinmap.json on its own (no solver needed).

    python3 scripts/check_pinmap.py

* every ball is used at most once, and each signal really is that mux option on that pin
  (hardware/data/alif_e3_fbga194.json, which the extractor cross-checks against Table 4-2);
* every Alif edge net sits on exactly one pad of hardware/data/edge_pinout.json, and every
  non-GND pad is either an Alif edge net or a declared non-Alif net;
* each multi-signal group uses one peripheral instance and one pin-option suffix.
"""
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
balls = json.load(open(f"{ROOT}/hardware/data/alif_e3_fbga194.json"))
ep = json.load(open(f"{ROOT}/hardware/data/edge_pinout.json"))
pm = json.load(open(f"{ROOT}/hardware/data/pinmap.json"))
fails = []
seen = {}
groups = defaultdict(set)
for section in ("edge", "internal"):
    for net, e in pm[section].items():
        b = e["ball"]
        if b in seen:
            fails.append(f"ball {b} used by {seen[b]} and {net}")
        seen[b] = net
        if balls[b]["name"] != e["pin"]:
            fails.append(f"{net}: ball {b} is {balls[b]['name']}, not {e['pin']}")
        if e["mux"] is not None:
            alts = {a[1]: a[0] for a in balls[b]["alts"]}
            if alts.get(e["signal"]) != e["mux"]:
                fails.append(f"{net}: {e['signal']} is not mux {e['mux']} of {e['pin']}")
        m = re.match(r"(UART\d|SPI\d|I2C\d|I2S\d|QEC\d|ETH|SD|CAN|PDM|I3C|CAM)_.*?(?:_([A-D]))?$", e["signal"])
        if m and e["group"] not in ("GPIO", "dedicated") and not e["group"].startswith(("PWM", "ADC")):
            groups[e["group"]].add((m.group(1), m.group(2)))
for g, keys in groups.items():
    if len(keys) > 1:
        fails.append(f"group {g} mixes instances/suffixes: {sorted(keys, key=str)}")
on_pads = [p["net"] for p in ep["pads"]]
for net in pm["edge"]:
    if on_pads.count(net) != 1:
        fails.append(f"{net}: on {on_pads.count(net)} edge pads")
for p in ep["pads"]:
    if p["net"] != "GND" and p["net"] not in pm["edge"] and p["net"] not in ep["other"]:
        fails.append(f"edge pad {p['num']} {p['net']} is neither an Alif net nor a declared net")
if fails:
    print("\n".join(fails))
    sys.exit(f"{len(fails)} pinmap check(s) failed")
print(f"pinmap OK: {len(seen)} balls, {len(pm['edge'])} edge nets, {len(pm['internal'])} on-module nets, "
      f"{len(ep['pads'])} edge pads")
