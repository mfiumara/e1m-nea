"""Shared helpers for writing KiCad 10 symbol and footprint s-expressions."""
import math
import uuid

GRID = 2.54
PIN_LEN = 2.54
FONT = "(effects (font (size 1.27 1.27)))"
HIDDEN_FONT = "(effects (font (size 1.27 1.27)) (hide yes))"


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---------------------------------------------------------------- symbols
class Pin:
    def __init__(self, number, name, etype="bidirectional", alts=(), hidden=False, shape="line"):
        self.number, self.name, self.etype = str(number), name, etype
        self.alts, self.hidden, self.shape = list(alts), hidden, shape


def _pin_sexpr(p, x, y, angle):
    alts = "".join(f"(alternate {q(n)} {t} line)" for n, t in p.alts)
    hide = " (hide yes)" if p.hidden else ""
    return (f"(pin {p.etype} {p.shape} (at {f(x)} {f(y)} {angle}) (length {f(PIN_LEN)}){hide} "
            f"(name {q(p.name)} {FONT}) (number {q(p.number)} {FONT}){alts})")


def stack(numbers, name, etype="power_in"):
    """KLC-style stack: first pin visible with the real type, the rest hidden passive at the same spot."""
    numbers = list(numbers)
    first = Pin(numbers[0], name, etype)
    rest = [Pin(n, name, "passive", hidden=True) for n in numbers[1:]]
    return [first] + rest


def _groups(pins):
    """Group a side's pin list into slots: a stacked group shares one slot."""
    slots = []
    for p in pins:
        if p is None:
            slots.append([])
        elif p.hidden and slots and slots[-1] and slots[-1][0].name == p.name:
            slots[-1].append(p)
        else:
            slots.append([p])
    return slots


def unit_body(left=(), right=(), top=(), bottom=(), min_w=15.24):
    """Lay out one unit on the 2.54 mm grid. Returns (rectangle, pin sexprs, half_w, half_h)."""
    L, R, T, B = (_groups(s) for s in (left, right, top, bottom))
    ceil_g = lambda v: math.ceil(v / GRID - 1e-9) * GRID
    lr_chars = max([len(p.name) for s in (left, right) for p in s if p] + [3])
    tb_chars = max([len(p.name) for s in (top, bottom) for p in s if p] + [0])
    tb_space = ceil_g(tb_chars * 0.9 + 1.0) if tb_chars else 0
    rows = max(len(L), len(R), 1)
    cols = max(len(T), len(B), 0)
    w = max(min_w, 2 * (lr_chars * 0.9 + 1.5) if (L and R) else lr_chars * 0.9 + 4, (cols + 1) * GRID)
    hw = ceil_g(w / 2)
    hh = ceil_g(((rows + 1) * GRID + (tb_space if T else 0) + (tb_space if B else 0)) / 2)
    out = []
    y0 = hh - GRID - (tb_space if T else 0)
    for i, slot in enumerate(L):
        out += [_pin_sexpr(p, -hw - PIN_LEN, y0 - i * GRID, 0) for p in slot]
    for i, slot in enumerate(R):
        out += [_pin_sexpr(p, hw + PIN_LEN, y0 - i * GRID, 180) for p in slot]
    x0 = -((len(T) - 1) // 2) * GRID
    for i, slot in enumerate(T):
        out += [_pin_sexpr(p, x0 + i * GRID, hh + PIN_LEN, 270) for p in slot]
    x1 = -((len(B) - 1) // 2) * GRID
    for i, slot in enumerate(B):
        out += [_pin_sexpr(p, x1 + i * GRID, -hh - PIN_LEN, 90) for p in slot]
    rect = (f"(rectangle (start {f(-hw)} {f(hh)}) (end {f(hw)} {f(-hh)}) "
            f"(stroke (width 0.254) (type default)) (fill (type background)))")
    return rect, out, hw, hh


def symbol(name, ref, value, footprint, datasheet, description, units, keywords="", fp_filter="",
           unit_names=None):
    """units: list of dicts with left/right/top/bottom pin lists (+ optional texts)."""
    bodies = [unit_body(**u) for u in units]
    hh_max = max(b[3] for b in bodies)
    hw_max = max(b[2] for b in bodies)
    has_top = any(u.get("top") for u in units)
    has_bot = any(u.get("bottom") for u in units)
    props = [
        ("Reference", ref, (-hw_max, hh_max + (PIN_LEN + 3.81 if has_top else 1.27)), False, "left"),
        ("Value", value, (-hw_max, -hh_max - (PIN_LEN + 3.81 if has_bot else 1.27)), False, "left"),
        ("Footprint", footprint, (0, -hh_max - 7.62), True, None),
        ("Datasheet", datasheet, (0, 0), True, None),
        ("Description", description, (0, 0), True, None),
        ("ki_keywords", keywords, (0, 0), True, None),
    ]
    if fp_filter:
        props.append(("ki_fp_filters", fp_filter, (0, 0), True, None))
    s = [f"(symbol {q(name)} (exclude_from_sim no) (in_bom yes) (on_board yes)"]
    for k, v, (x, y), hide, just in props:
        j = f" (justify {just})" if just else ""
        h = " (hide yes)" if hide else ""
        s.append(f"(property {q(k)} {q(v)} (at {f(x)} {f(y)} 0)"
                 f"{h} (effects (font (size 1.27 1.27)){j}))")
    for i, (rect, pins, hw, hh) in enumerate(bodies, start=1):
        uname = f' (unit_name {q(unit_names[i - 1])})' if unit_names else ""
        s.append(f"(symbol {q(f'{name}_{i}_1')}{uname} {rect} {' '.join(pins)})")
    s.append(")")
    return "\n".join(s)


def symbol_lib(symbols):
    return ("(kicad_symbol_lib (version 20251024) (generator \"fiumara-ae3-som-gen_lib\") (generator_version \"1\")\n"
            + "\n".join(symbols) + "\n)\n")


# ---------------------------------------------------------------- footprints
def uid():
    return str(uuid.uuid4())


def fp_rect_line(layer, x0, y0, x1, y1, width):
    return (f"(fp_rect (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) "
            f"(stroke (width {f(width)}) (type solid)) (fill no) (layer {q(layer)}) (uuid {q(uid())}))")


def fp_line(layer, x0, y0, x1, y1, width):
    return (f"(fp_line (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) "
            f"(stroke (width {f(width)}) (type solid)) (layer {q(layer)}) (uuid {q(uid())}))")


def fp_poly(layer, pts, width=0.0, fill=True):
    p = " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts)
    return (f"(fp_poly (pts {p}) (stroke (width {f(width)}) (type solid)) "
            f"(fill {'yes' if fill else 'no'}) (layer {q(layer)}) (uuid {q(uid())}))")


def fp_text(kind, text, x, y, layer, hide=False, size=1.0):
    h = " (hide yes)" if hide else ""
    th = f(size * 0.15)
    return (f"(property {q(kind)} {q(text)} (at {f(x)} {f(y)} 0) (layer {q(layer)}){h} (uuid {q(uid())}) "
            f"(effects (font (size {f(size)} {f(size)}) (thickness {th}))))")


def pad(number, shape, x, y, w, h, layers, extra=""):
    lay = " ".join(q(l) for l in layers)
    return (f"(pad {q(number)} smd {shape} (at {f(x)} {f(y)}) (size {f(w)} {f(h)}) "
            f"(layers {lay}){extra} (uuid {q(uid())}))")


def custom_pad(number, x, y, anchor, polys, layers, extra=""):
    """polys: list of point lists, relative to the pad anchor."""
    lay = " ".join(q(l) for l in layers)
    prims = " ".join(
        "(gr_poly (pts " + " ".join(f"(xy {f(px)} {f(py)})" for px, py in pts) + ") (width 0) (fill yes))"
        for pts in polys)
    return (f"(pad {q(number)} smd custom (at {f(x)} {f(y)}) (size {f(anchor)} {f(anchor)}) "
            f"(layers {lay}){extra} (options (clearance outline) (anchor rect)) "
            f"(primitives {prims}) (uuid {q(uid())}))")


def footprint(name, descr, tags, items, attr="smd", model=None):
    m = f"(model {q(model)} (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))" if model else ""
    return (f"(footprint {q(name)} (version 20260206) (generator \"fiumara-ae3-som-gen_lib\") (generator_version \"1\") "
            f"(layer \"F.Cu\") (descr {q(descr)}) (tags {q(tags)}) (attr {attr})\n"
            + "\n".join(items) + f"\n{m})\n")


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
