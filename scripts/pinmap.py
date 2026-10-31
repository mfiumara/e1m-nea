"""M3: allocate Alif E3 pins to the module's edge interfaces and to the on-module peripherals.

    python scripts/pinmap.py         # writes hardware/data/pinmap.json, then checks it
    python3 scripts/gen_edge.py      # places the resulting edge nets on the LGA pads

Input: hardware/data/alif_e3_fbga194.json (ball -> mux alternatives)

The edge interface set and its net names are this project's own (see docs/edge-pinout.md).

Method
------
Every multi-signal interface is a *group*: all its signals must come from one peripheral instance
with one pin-option suffix (_A/_B/_C/_D), so timing-related signals share Alif's characterised
pin set. A CP-SAT model (OR-Tools) picks at most one option per group and one pin per single GPIO
net, with each ball and each peripheral instance used at most once, and maximises the summed
priority. Dedicated balls (USB, MIPI, crystals, SEUART, reset) are fixed.

needs: pip install ortools
"""
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
balls = json.load(open(f"{ROOT}/hardware/data/alif_e3_fbga194.json"))

# signal name -> (pin, ball, mux)
SIG = {}
PIN_BALL = {}
for b, p in balls.items():
    if "alts" not in p:
        continue
    PIN_BALL[p["name"]] = b
    for mux, name, _ in p["alts"]:
        assert name not in SIG, f"signal {name} on two pins"
        SIG[name] = (p["name"], b, mux)
GPIO_PINS = sorted(PIN_BALL, key=lambda n: tuple(int(x) for x in n[1:].split("_")))


# ----------------------------------------------------------------------------- group specs
# roles: {role: (template, net or edge silkscreen)}; template uses {i} = instance, {s} = suffix.
# instances: iterable of instance strings. "edge" roles name an edge pad by silkscreen.
G = []


def group(name, prio, instances, roles, kind):
    G.append(dict(name=name, prio=prio, instances=list(instances), roles=roles, kind=kind))


SUF = "ABCD"
# --- on-module (internal) interfaces
group("ETH_RMII", 1000, [""], {
    "TXD0": "ETH_TXD0_{s}", "TXD1": "ETH_TXD1_{s}", "TXEN": "ETH_TXEN_{s}", "RXD0": "ETH_RXD0_{s}",
    "RXD1": "ETH_RXD1_{s}", "CRS_DV": "ETH_CRS_DV_{s}", "REFCLK": "ETH_REFCLK_{s}", "MDC": "ETH_MDC_{s}",
    "MDIO": "ETH_MDIO_{s}", "IRQ": "ETH_IRQ_{s}", "RST": "ETH_RST_{s}"}, "internal")
group("WIFI_SPI", 1000, ["0", "1", "2", "3"], {
    "SCLK": "SPI{i}_SCLK_{s}", "MOSI": "SPI{i}_MOSI_{s}", "MISO": "SPI{i}_MISO_{s}", "CS": "SPI{i}_SS0_{s}"},
      "internal")
group("PMIC_I2C", 1000, ["0", "1", "2", "3"], {"SCL": "I2C{i}_SCL_{s}", "SDA": "I2C{i}_SDA_{s}"}, "internal")
# --- edge interfaces (role -> edge net name)
group("UART0", 60, list("01234567"), {"UART0_TX": "UART{i}_TX_{s}", "UART0_RX": "UART{i}_RX_{s}",
                                      "UART0_RTS": "UART{i}_RTS_{s}", "UART0_CTS": "UART{i}_CTS_{s}"}, "edge")
group("UART1", 55, list("01234567"), {"UART1_TX": "UART{i}_TX_{s}", "UART1_RX": "UART{i}_RX_{s}"}, "edge")
group("UART2", 35, list("01234567"), {"UART2_TX": "UART{i}_TX_{s}", "UART2_RX": "UART{i}_RX_{s}"}, "edge")
group("SPI0", 60, list("0123"), {"SPI0_SCK": "SPI{i}_SCLK_{s}", "SPI0_MOSI": "SPI{i}_MOSI_{s}",
                                  "SPI0_MISO": "SPI{i}_MISO_{s}", "SPI0_CS0": "SPI{i}_SS0_{s}",
                                  "SPI0_CS1": "SPI{i}_SS1_{s}"}, "edge")
group("SPI1", 50, list("0123"), {"SPI1_SCK": "SPI{i}_SCLK_{s}", "SPI1_MOSI": "SPI{i}_MOSI_{s}",
                                  "SPI1_MISO": "SPI{i}_MISO_{s}", "SPI1_CS0": "SPI{i}_SS0_{s}"}, "edge")
group("I2C0", 60, list("0123"), {"I2C0_SCL": "I2C{i}_SCL_{s}", "I2C0_SDA": "I2C{i}_SDA_{s}"}, "edge")
group("I2C1", 55, list("0123"), {"I2C1_SCL": "I2C{i}_SCL_{s}", "I2C1_SDA": "I2C{i}_SDA_{s}"}, "edge")
group("I3C0", 30, [""], {"I3C0_SCL": "I3C_SCL_{s}", "I3C0_SDA": "I3C_SDA_{s}"}, "edge")
group("I2S0", 40, list("0123"), {"I2S0_BCLK": "I2S{i}_SCLK_{s}", "I2S0_LRCLK": "I2S{i}_WS_{s}",
                                  "I2S0_DIN": "I2S{i}_SDI_{s}", "I2S0_DOUT": "I2S{i}_SDO_{s}"}, "edge")
group("I2S0_MCLK", 15, [""], {"I2S0_MCLK": "AUDIO_CLK_{s}"}, "edge")
group("PDM", 25, [""], {"PDM_CLK0": "PDM_C0_{s}", "PDM_DAT0": "PDM_D0_{s}", "PDM_CLK1": "PDM_C1_{s}",
                        "PDM_DAT1": "PDM_D1_{s}"}, "edge")
group("CAN", 70, [""], {"CAN_TXD": "CAN_TXD_{s}", "CAN_RXD": "CAN_RXD_{s}", "CAN_STB": "CAN_STBY_{s}"}, "edge")
group("SD", 70, [""], {"SD_CLK": "SD_CLK_{s}", "SD_CMD": "SD_CMD_{s}", "SD_DAT0": "SD_D0_{s}",
                       "SD_DAT1": "SD_D1_{s}", "SD_DAT2": "SD_D2_{s}", "SD_DAT3": "SD_D3_{s}"}, "edge")
group("DEBUG", 200, [""], {"SWCLK": "JTAG_TCK", "SWDIO": "JTAG_TMS", "TDI": "JTAG_TDI", "SWO": "JTAG_TDO"}, "edge")
group("DVP", 20, [""], {"DVP_PCLK": "CAM_PCLK_{s}", "DVP_HSYNC": "CAM_HSYNC_{s}", "DVP_VSYNC": "CAM_VSYNC_{s}",
                        "DVP_XCLK": "CAM_XVCLK_{s}", **{f"DVP_D{k}": f"CAM_D{k}_{{s}}" for k in range(8)}}, "edge")
for k in range(2):
    group(f"QEC{k}", 8, list("0123"), {f"QEC{k}_A": "QEC{i}_X_{s}", f"QEC{k}_B": "QEC{i}_Y_{s}"}, "edge")
for k in range(6):   # PWM: any UTIMER output, one per pad
    group(f"PWM{k}", 6, [f"{t}_T{o}" for t in range(12) for o in (0, 1)], {f"PWM{k}": "UT{i}_{s}"}, "edge")
for k in range(6):   # analog inputs: prefer the matching ANA_S channel, any of S0-S17 allowed
    group(f"AIN{k}", 7, [str(k)] + [str(c) for c in range(18) if c != k], {f"AIN{k}": "ANA_S{i}"}, "edge")
group("AOUT0", 7, [""], {"AOUT0": "ANA_S18"}, "edge")
group("AOUT1", 7, [""], {"AOUT1": "ANA_S19"}, "edge")
group("OSPI_MEM", 45, ["0", "1"], {**{f"D{k}": f"OSPI{{i}}_D{k}_{{s}}" for k in range(8)},
                                   "SCLK": "OSPI{i}_SCLK_{s}", "RXDS": "OSPI{i}_RXDS_{s}",
                                   "SS0": "OSPI{i}_SS0_{s}", "SS1": "OSPI{i}_SS1_{s}"}, "internal")

# Single nets on any free GPIO: (net, priority, kind). Edge GPIOs fill whatever balls remain.
SINGLES = [("WIFI_IRQ", 1000, "internal"), ("WIFI_nRESET", 1000, "internal"), ("PMIC_nINT", 1000, "internal"),
           ("SD_PWR_EN", 500, "internal"), ("SD_CD", 60, "edge"), ("WAKE_N", 80, "edge")]
EDGE_GPIO = [f"GPIO{k}" for k in range(40)]
SINGLES += [(s, 4 if k < 24 else 3, "edge") for k, s in enumerate(EDGE_GPIO)]
LPGPIO = ["P15_0", "P15_1", "P15_2", "P15_3", "P15_4", "P15_5", "P15_6", "P15_7"]
# WAKE_N must land on an LPGPIO (P15_x) so it can wake the SoC from STOP.
PREFERRED = {"WAKE_N": LPGPIO}

# Fixed balls (dedicated functions): edge silkscreen -> Alif pin name
FIXED_EDGE = {"USB_DP": "USB_DP", "USB_DN": "USB_DM", "USB_VBUS": "USB_VBUS", "USB_ID": "USB_IO_ID",
              "DSI_CLK_P": "MIPIDSI_C_P", "DSI_CLK_N": "MIPIDSI_C_N", "DSI_D0_P": "MIPIDSI_0_P",
              "DSI_D0_N": "MIPIDSI_0_N", "DSI_D1_P": "MIPIDSI_1_P", "DSI_D1_N": "MIPIDSI_1_N",
              "CSI_CLK_P": "MIPICSI_C_P", "CSI_CLK_N": "MIPICSI_C_N", "CSI_D0_P": "MIPICSI_0_P",
              "CSI_D0_N": "MIPICSI_0_N", "CSI_D1_P": "MIPICSI_1_P", "CSI_D1_N": "MIPICSI_1_N",
              "CONSOLE_TX": "SEUART_TX", "CONSOLE_RX": "SEUART_RX", "DBG_NRST": "NSRST"}


# ----------------------------------------------------------------------------- options
def options(g):
    out = []
    sufs = SUF if any("{s}" in t for t in g["roles"].values()) else [""]
    for inst in g["instances"]:
        for s in sufs:
            pins = {}
            for role, tmpl in g["roles"].items():
                sig = tmpl.replace("{i}", inst).replace("{s}", s)
                if sig.endswith("_"):
                    sig = sig[:-1]
                if sig not in SIG:
                    break
                pins[role] = (SIG[sig][0], sig, SIG[sig][2])
            else:
                if len({p[0] for p in pins.values()}) == len(pins):
                    out.append(dict(inst=inst, suffix=s, pins=pins))
    return out


for g in G:
    g["options"] = options(g)
    g["resources"] = {f"{g['name']}"}

# Peripheral instance exclusivity: two groups may not use the same UART2 / SPI1 / I2C0 ... instance.
def instance_key(g, opt):
    keys = set()
    for role, (pin, sig, mux) in opt["pins"].items():
        m = re.match(r"(UART\d|SPI\d|I2C\d|I2S\d|QEC\d|OSPI\d|I3C|PDM|CAN|SD|ETH|LPTMR\d|AUDIO)", sig)
        if m:
            keys.add(m.group(1))
    if g["name"].startswith(("PWM", "ADC")):
        keys = set()     # timers / ADC channels are per-pin resources, the pin check covers them
    return keys


from ortools.sat.python import cp_model  # noqa: E402

m = cp_model.CpModel()
pin_users = defaultdict(list)
inst_users = defaultdict(list)
gvars = {}
for g in G:
    vs = []
    for j, opt in enumerate(g["options"]):
        v = m.NewBoolVar(f"{g['name']}_{j}")
        vs.append((v, opt))
        for pin, _, _ in opt["pins"].values():
            pin_users[pin].append(v)
        for key in instance_key(g, opt):
            inst_users[key].append((g["name"], v))
    m.Add(sum(v for v, _ in vs) <= 1)
    gvars[g["name"]] = vs
# singles: one var per (net, candidate pin)
svars = {}
for net, prio, kind in SINGLES:
    cands = PREFERRED.get(net, GPIO_PINS)
    vs = []
    for pin in cands:
        v = m.NewBoolVar(f"{net}_{pin}")
        vs.append((v, pin))
        pin_users[pin].append(v)
    m.Add(sum(v for v, _ in vs) <= 1)
    svars[net] = vs
for pin, vs in pin_users.items():
    m.Add(sum(vs) <= 1)
for key, users in inst_users.items():
    # one group per peripheral instance (options of the same group already exclude each other)
    by_group = defaultdict(list)
    for gname, v in users:
        by_group[gname].append(v)
    if len(by_group) > 1:
        used = []
        for gname, vs in by_group.items():
            u = m.NewBoolVar(f"use_{key}_{gname}")
            m.AddMaxEquality(u, vs)
            used.append(u)
        m.Add(sum(used) <= 1)
obj = []
for g in G:
    for v, opt in gvars[g["name"]]:
        # small tie-breaks: prefer the ADC channel that matches the pad name, and the lowest instance
        bonus = 1 if g["name"].startswith("ADC") and opt["inst"] == g["name"][3:] else 0
        # and the Alif instance whose number matches the edge interface (UART0 -> UART0, SPI1 -> SPI1)
        if g["kind"] == "edge" and g["name"][-1:].isdigit() and opt["inst"] == g["name"][-1]:
            bonus += 1
        obj.append(v * (g["prio"] * 10 + bonus))
for net, prio, kind in SINGLES:
    for v, pin in svars[net]:
        obj.append(v * prio * 10)
m.Maximize(sum(obj))
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60
solver.parameters.num_workers = 1
solver.parameters.random_seed = 1
status = solver.Solve(m)
assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE), solver.StatusName(status)
choice = {g: next(opt for v, opt in vs if solver.Value(v)) for g, vs in gvars.items()
          if any(solver.Value(v) for v, _ in vs)}
single_assign = {net: next(pin for v, pin in vs if solver.Value(v)) for net, vs in svars.items()
                 if any(solver.Value(v) for v, _ in vs)}
used = {p[0] for opt in choice.values() for p in opt["pins"].values()} | set(single_assign.values())
free = [p for p in GPIO_PINS if p not in used]
best = {"score": int(solver.ObjectiveValue()), "status": solver.StatusName(status)}
total_prio = sum(g["prio"] for g in G) * 10 + sum(p for _, p, _ in SINGLES) * 10

# ----------------------------------------------------------------------------- result
result = {"edge": {}, "internal": {}, "dropped": [], "free_pins": free}
for g in G:
    if g["name"] not in choice:
        result["dropped"].append(g["name"])
        continue
    opt = choice[g["name"]]
    for role, (pin, sig, mux) in opt["pins"].items():
        entry = dict(pin=pin, ball=PIN_BALL[pin], signal=sig, mux=mux, group=g["name"])
        if g["kind"] == "edge":
            result["edge"][role] = entry
        else:
            result["internal"][f"{g['name']}.{role}"] = entry
kind_of = {n: k for n, _, k in SINGLES}
for net, pin in single_assign.items():
    alts = {a[1]: a[0] for a in balls[PIN_BALL[pin]]["alts"]}
    gp = next(a for a in alts if a.startswith("GPIO"))
    entry = dict(pin=pin, ball=PIN_BALL[pin], signal=gp, mux=alts[gp], group="GPIO")
    if kind_of[net] == "edge":
        result["edge"][net] = entry
    else:
        result["internal"][net] = entry
for net, _, _ in SINGLES:
    if net not in single_assign:
        result["dropped"].append(net)
for silk, alif in FIXED_EDGE.items():
    b = next(k for k, v in balls.items() if v["name"] == alif)
    result["edge"][silk] = dict(pin=alif, ball=b, signal=alif, mux=None, group="dedicated")

# GPIO nets the solver could not place are simply not part of the edge (they are optional fill).
# Renumber the placed ones GPIO0..n in Alif port order so the edge names are contiguous.
result["dropped"] = [d for d in result["dropped"] if d not in EDGE_GPIO]
placed = sorted((n for n in result["edge"] if n in EDGE_GPIO),
                key=lambda n: tuple(int(x) for x in result["edge"][n]["pin"][1:].split("_")))
entries = [result["edge"].pop(n) for n in placed]
for k, e in enumerate(entries):
    result["edge"][f"GPIO{k}"] = e

json.dump(result, open(f"{ROOT}/hardware/data/pinmap.json", "w"), indent=1, sort_keys=True)

# ----------------------------------------------------------------------------- checks
fails = []
seen = {}
for section in ("edge", "internal"):
    for net, e in result[section].items():
        key = e["ball"]
        if key in seen:
            fails.append(f"ball {key} used twice: {seen[key]} and {net}")
        seen[key] = net
        if e["mux"] is not None:
            alts = {a[1]: a[0] for a in balls[e["ball"]]["alts"]}
            if alts.get(e["signal"]) != e["mux"]:
                fails.append(f"{net}: {e['signal']} is not mux {e['mux']} on {e['pin']}")
for gname, opt in choice.items():
    sufs = {p[1].rsplit("_", 1)[-1] for p in opt["pins"].values() if re.search(r"_[A-D]$", p[1])}
    if len(sufs) > 1:
        fails.append(f"{gname}: mixed pin-option suffixes {sufs}")
must = [g["name"] for g in G if g["prio"] >= 200] + [n for n, p, _ in SINGLES if p >= 500]
for m in must:
    if m in result["dropped"]:
        fails.append(f"required {m} could not be placed")
if fails:
    print("\n".join(fails))
    sys.exit(1)

print(f"{best['status']} score {best['score']}/{total_prio}; edge nets {len(result['edge'])}, internal {len(result['internal'])}, "
      f"free pins {len(free)}; dropped: {', '.join(result['dropped']) or 'none'}")

