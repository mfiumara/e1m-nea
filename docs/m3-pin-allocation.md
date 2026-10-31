# M3: own edge pinout and pin allocation

Status: in review.

- [edge-pinout.md](edge-pinout.md): pad map with picture, the non-SoC nets, all 244 pads.
- [pinmap.md](pinmap.md): the SoC ball behind every edge and on-module net.
- Data: `hardware/data/pinmap.json` and `hardware/data/edge_pinout.json`.

```sh
pip install -r scripts/requirements.txt
python scripts/pinmap.py          # CP-SAT ball allocation -> pinmap.json
python3 scripts/gen_edge.py       # places the nets on the LGA pads -> edge_pinout.json
python scripts/gen_docs.py        # pinmap.md, edge-pinout.md, images/edge-pinout.png
python3 scripts/check_pinmap.py   # independent checks
python3 scripts/gen_lib.py && python3 scripts/check_lib.py
```

## Edge pinout

The module's edge is this project's own design:
- 35 × 35 mm outline, 244 round 0.60 mm LGA pads at 1.0 mm pitch.
- Two concentric rings, 1.5 mm and 2.5 mm in from the edge. The outer-ring corners are left empty.
- QFN-style anticlockwise numbering: outer ring 1–124, inner ring 125–244.
- 138 signal and power pads, 106 GND pads.

Pads are grouped to match the floorplan:
- **Left side:** power, control and debug, next to the PMIC.
- **Bottom of the left side:** the antenna pad, next to the Wi‑Fi module.
- **Bottom side:** SD, CAN and Ethernet (the PHY sits bottom right).
- **Right side:** analog, PWM, encoders and the camera input, next to the SoC.
- **Top side:** the display output and the serial and audio buses.

`gen_edge.py` checks that every differential pair and the antenna pad have GND on at least two
neighbouring pads, and that every net appears exactly once (VIN ×6 and VREF_1V8 ×2 excepted).

## Interface set

| Interface | Count |
| --- | --- |
| Power and control | VIN ×6, VREF_1V8 ×2, EN, STBY_N, RESET_N, WAKE_N |
| Debug | SWD (SWDIO, SWCLK, SWO, TDI), DBG_NRST, console UART, Wi‑Fi module SWD + log |
| USB | USB 2.0 HS (DP, DN, VBUS, ID) |
| MIPI | CSI 2-lane, DSI 2-lane |
| Ethernet | 10/100 (TX, RX pairs, link and activity LEDs) |
| Wireless | ANT (2.4 GHz Wi‑Fi 6 + BLE 5.4) |
| CAN | TXD, RXD, STB logic pads; CANH/CANL when the transceiver is fitted |
| SD | 4-bit + CD, 3.3 V card supply SD_VDD |
| Serial | UART0 with RTS/CTS, UART1, UART2, SPI0 (2 CS), SPI1, I²C0, I²C1, I³C |
| Audio | I²S0 + MCLK, PDM ×2 |
| Analog and timers | AIN0–5, AOUT0–1, PWM0–5, QEC0–1 |
| GPIO | GPIO0–29 (fills the remaining SoC balls) |

## Ball allocation

A CP-SAT model (OR-Tools) is used, deterministic with one worker and a fixed seed.

**Rules:**
- Each multi-signal interface uses one Alif peripheral instance and one pin-option suffix.
- Each ball and each peripheral instance is used at most once.
- `WAKE_N` must land on an LPGPIO (P15_x), so it can wake the SoC from STOP.

**Priorities, highest first:**
1. On-module functions and debug.
2. CAN, SD and the core serial interfaces.
3. The OSPI memory option.
4. Audio.
5. Analog, PWM and encoders.
6. GPIO.

**Result:**
- All 128 GPIO balls are used: 114 edge nets and 33 on-module nets. The on-module side is
  RMII + PHY IRQ/reset, Wi‑Fi SPI + IRQ/reset, the PMIC I²C + IRQ, SD power enable, and the
  OSPI HyperRAM + NOR option (now wired, DNP by default).
- The only interface left out is an 8-bit parallel camera. MIPI CSI covers camera input, and
  the balls went to the OSPI memory and GPIO instead.

## Extraction fix (during M3)

The extractor now also reads mux signals printed on a pin's own row of Table 4-1, and signals
with footnote markers. It cross-checks every pin's signal set against Table 4-2.

## Open for M4

- DP83825I straps on the LED pins.
- The SD level translator and the 3.3 V card switch.
- I²C pull-ups (on-module for the PMIC bus).
- The `WAKE_N` 5 V-tolerant front end.
- On-module pull-ups on `EN`, `STBY_N` and `RESET_N`.
